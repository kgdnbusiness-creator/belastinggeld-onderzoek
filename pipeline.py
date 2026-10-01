#!/usr/bin/env python3
"""Belastinggeld-pipeline: Rijksbegroting open data -> aggregatie -> analyse -> site.

Bron: Budgettaire Tabellen Rijksbegroting (Ministerie van Financien, CC-0), via
data.overheid.nl / rijksfinancien.nl. Alleen standaardbibliotheek.

Gebruik:
  python pipeline.py --years 2023-2026          # downloaden + bouwen
  python pipeline.py --local ./csv_map          # bouwen uit lokale CSV's (test/offline)
"""
import argparse, csv, glob, io, json, re, sys, urllib.request, datetime as dt
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
PAGE = "https://data.overheid.nl/dataset/budgettaire-tabellen-rijksbegroting-{y}"
CSV_RE = re.compile(r"https://www\.rijksfinancien\.nl/sites/default/files/bestanden/open_data/[^\s\"'<>)]+\.csv")
UA = {"User-Agent": "belastinggeld-onderzoek/0.1 (open data research)"}
# Voorkeursvolgorde bedragkolom: realisatie boven raming; hoogste begrotingsfase eerst.
AMOUNT_PREF = ["Realisatie", "StandO2", "StandSBSupp", "StandO1", "StandOWB"]
FASE_RANK = {"OW": 1, "OWB": 1, "O1": 2, "I1": 2, "SBS": 3, "I2": 3, "O2": 4, "JV": 5}
UNIT = 1000  # bedragen in de bron staan in EUR x 1.000
DOORSLUIS = "Bijdrage aan (andere) begrotingshoofdstukken"  # dubbeltelling tussen hoofdstukken


def http(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8-sig", errors="replace")


def discover(years):
    """Zoek CSV-links op de datasetpagina per jaar. Slaat jaren over zonder pagina."""
    found = []
    for y in years:
        try:
            html = http(PAGE.format(y=y))
        except Exception as e:  # 404 of netwerkfout: melden, niet crashen
            print(f"[waarschuwing] geen datasetpagina voor {y}: {e}", file=sys.stderr)
            continue
        urls = sorted(u for u in set(CSV_RE.findall(html)) if 'incl' not in u.lower())
        print(f"{y}: {len(urls)} CSV-bestand(en)")
        found += urls
    return found


def to_int(s):
    s = (s or "").strip().replace(".", "").replace(",", ".")
    try:
        return int(round(float(s)))
    except ValueError:
        return 0


REQUIRED = ["VUO", "Totaal", "Hoofdstuknummer", "Hoofdstuknaam", "Artikelnummer", "Artikelnaam",
            "Artikelonderdeelnummer", "Instrumentnummer", "Instrumentnaam", "Detailnummer", "Detailnaam"]


def read_rows(text, source):
   first = text.split("\n", 1)[0]
   rd = csv.DictReader(io.StringIO(text), delimiter=";" if first.count(";") >= first.count(",") else ",")
    rd.fieldnames = [(c or "").strip() for c in (rd.fieldnames or [])]
    cols = rd.fieldnames
    col = next((c for c in AMOUNT_PREF if c in cols), None)
    missing = [c for c in REQUIRED if c not in cols]
    if not col or missing:
        print(f"[overgeslagen] onbekend formaat: {source}\n   kolommen: {';'.join(cols)}", file=sys.stderr)
        return
    name = source.replace("%20", " ")
    m_year = re.search(r"(20\d\d)", name)
    m_fase = re.search(r"[_ ](OWB|OW|O1|I1|SBS|I2|O2|JV)[_ .]", name)
    kind = "realisatie" if col == "Realisatie" else "raming"
    for r in rd:
        r["Begrotingsjaar"] = r.get("Begrotingsjaar") or (m_year.group(1) if m_year else "0")
        r["Fase"] = r.get("Fase") or (m_fase.group(1) if m_fase else "?")
        r["_amt"] = to_int(r.get(col)) * UNIT
        r["_kind"], r["_col"], r["_src"] = kind, col, source
        yield r


def aggregate(rows):
    """Tel alleen uitgaven (U) en alleen 'Totaal=J'-regels op het juiste niveau, om dubbeltelling te voorkomen."""
    art = defaultdict(int)      # (jaar,fase,kind,hfst,hnaam,artnr,artnaam)
    ins = defaultdict(int)      # (jaar,fase,kind,hfst,hnaam,instrument)
    det = defaultdict(int)      # (jaar,fase,kind,hnaam,artnaam,detailnaam)
    meta = {}
    for r in rows:
        if r["VUO"] != "U":
            continue
        y, f, k = to_int(r["Begrotingsjaar"]), r["Fase"], r["_kind"]
        h, hn = r["Hoofdstuknummer"], r["Hoofdstuknaam"]
        meta[(y, f)] = (r["_src"], r["_col"], k)
        no_ond, no_ins, no_det = not r["Artikelonderdeelnummer"], not r["Instrumentnummer"], not r["Detailnummer"]
        if r["Totaal"] == "J" and no_ond and no_ins:
            art[(y, f, k, h, hn, r["Artikelnummer"], r["Artikelnaam"])] += r["_amt"]
        elif r["Totaal"] == "J" and not no_ond and not no_ins and no_det:
            ins[(y, f, k, h, hn, r["Instrumentnaam"])] += r["_amt"]
        elif r["Totaal"] == "N" and not no_det:
            det[(y, f, k, hn, r["Artikelnaam"], r["Detailnaam"])] += r["_amt"]
    return art, ins, det, meta


def best_phase(meta):
    """Kies per jaar de hoogste beschikbare begrotingsfase."""
    best = {}
    for (y, f), (_, _, k) in meta.items():
        if y not in best or FASE_RANK.get(f, 0) > FASE_RANK.get(best[y], 0):
            best[y] = f
    return best


def build(art, ins, det, meta):
    best = best_phase(meta)
    keep = lambda y, f: best.get(y) == f
    ministries = defaultdict(lambda: defaultdict(int))  # naam -> jaar -> bedrag
    doorsluis = defaultdict(lambda: defaultdict(int))
    inst_out, art_out, kinds, warns = [], [], {}, []
    for (y, f, k, h, hn, ar, an), v in art.items():
        if keep(y, f):
            ministries[(h, hn)][y] += v
            art_out.append({"jaar": y, "hoofdstuk": hn, "artikel": f"{ar}. {an}", "bedrag": v})
            kinds[y] = {"fase": f, "soort": k, "bron": meta[(y, f)][0]}
    inst_sum = defaultdict(int)
    for (y, f, k, h, hn, i), v in ins.items():
        if keep(y, f):
            inst_out.append({"jaar": y, "hoofdstuk": hn, "instrument": i, "bedrag": v})
            inst_sum[(y, hn)] += v
            if i == DOORSLUIS:
                doorsluis[hn][y] += v
    # Controle: instrumenten horen op te tellen tot artikelen (tolerantie 1 mln).
    for (h, hn), yrs in ministries.items():
        for y, tot in yrs.items():
            d = tot - inst_sum.get((y, hn), 0)
            if inst_sum.get((y, hn)) and abs(d) > 1_000_000:
                warns.append(f"{hn} {y}: instrumenten wijken {d/1e6:,.0f} mln af van artikeltotaal")
    top = sorted(((v, k) for k, v in det.items() if keep(k[0], k[1])), reverse=True)
    top_det = [{"jaar": k[0], "hoofdstuk": k[3], "artikel": k[4], "regeling": k[5], "bedrag": v}
               for v, k in top[:200]]
    mins = [{"hoofdstuk": h, "naam": n, "per_jaar": dict(y), "doorgesluisd": dict(doorsluis.get(n, {}))}
            for (h, n), y in sorted(ministries.items())]
    return mins, inst_out, art_out, top_det, kinds, warns


def findings(mins, kinds):
    """Automatische signalen. Bewust neutraal geformuleerd: dit zijn aanknopingspunten voor onderzoek, geen conclusies."""
    out, years = [], sorted({y for m in mins for y in m["per_jaar"]})
    for a, b in zip(years, years[1:]):
        for m in mins:
            x, y = m["per_jaar"].get(a), m["per_jaar"].get(b)
            if x and y and abs(y - x) > 100e6 and abs(y / x - 1) > 0.25:
                out.append({"type": "grote verandering", "hoofdstuk": m["naam"], "van": a, "naar": b,
                            "pct": round((y / x - 1) * 100, 1), "verschil": y - x,
                            "let_op": "Kan komen door herindeling van artikelen of incidentele posten; controleer de toelichting in de begroting."})
    if any(k["soort"] != "realisatie" for k in kinds.values()):
        out.append({"type": "kwaliteit", "let_op": "Recente jaren zijn ramingen, geen realisaties; vergelijk ze niet zonder voorbehoud met jaarverslagcijfers."})
    return sorted(out, key=lambda f: -abs(f.get("verschil", 0)))


def render(data):
    tpl = (ROOT / "site" / "template.html").read_text(encoding="utf-8")
    (ROOT / "site").mkdir(exist_ok=True)
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    (ROOT / "site" / "index.html").write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default=f"{dt.date.today().year-3}-{dt.date.today().year}")
    ap.add_argument("--local", help="map met CSV-bestanden i.p.v. downloaden")
    a = ap.parse_args()
    texts = []
    if a.local:
        texts = [(p, Path(p).read_text(encoding="utf-8-sig")) for p in sorted(glob.glob(f"{a.local}/*.csv"))]
    else:
        lo, hi = (int(x) for x in a.years.split("-"))
        for u in discover(range(lo, hi + 1)):
            try:
                texts.append((u, http(u)))
            except Exception as e:
                print(f"[waarschuwing] download mislukt {u}: {e}", file=sys.stderr)
    if not texts:
        sys.exit("Geen data gevonden. Controleer netwerk of --local map.")
    rows = [r for src, t in texts for r in read_rows(t, src)]
    art, ins, det, meta = aggregate(rows)
    mins, inst, arts, top, kinds, warns = build(art, ins, det, meta)
    data = {"gegenereerd": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "eenheid": "EUR", "jaren": {str(k): v for k, v in sorted(kinds.items())},
            "ministeries": mins, "instrumenten": inst, "artikelen": arts, "grootste_regelingen": top,
            "signalen": findings(mins, kinds), "controle": warns,
            "methode": "Uitgaven (U), regels met Totaal=J op artikel- resp. instrumentniveau; per jaar de hoogste beschikbare begrotingsfase. "
                       "Exclusief premies; alleen Rijk (geen gemeenten/provincies). Doorgesluisde bijdragen tussen hoofdstukken zijn apart vermeld om dubbeltelling te tonen."}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "uitgaven.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    render(data)
    print(f"Klaar: {len(mins)} hoofdstukken, {len(inst)} instrument-regels, {len(warns)} controlewaarschuwingen.")


if __name__ == "__main__":
    main()
