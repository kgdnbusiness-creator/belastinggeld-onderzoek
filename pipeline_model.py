"""Validated budget snapshots. Amounts are integer euros; source amounts are EUR x 1,000."""
import csv
import io
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pipeline_sources import DataError, PHASES, RANK

COLUMNS = {'JV': ('Realisatie',), 'O2': ('StandO2',),
           'SBS': ('StandSBS', 'StandSBSupp'), 'O1': ('StandO1',), 'OWB': ('StandOWB',)}


def amount(value):
    try:
        number = Decimal(value.strip().replace(',', '.')) * 1000
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError()
        return int(number)
    except (InvalidOperation, ValueError, AttributeError):
        raise DataError(f'Ongeldig of ontbrekend bedrag: {value!r}') from None


def parse(raw, source):
    text = raw.decode('utf-8-sig')
    first = text.splitlines()[0]
    reader = csv.DictReader(io.StringIO(text), delimiter=';' if ';' in first else ',')
    required = {'IBOSnummer', 'Begrotingsjaar', 'VUO', 'Totaal', 'Hoofdstuknummer',
                'Hoofdstuknaam', 'Artikelnummer', 'Artikelnaam', 'Instrumentnaam', 'Detailnaam'}
    if not required.issubset(reader.fieldnames or []):
        raise DataError(f'Onbekend bronschema: {source["url"]}')
    phase = source['fase']
    col = next((c for c in COLUMNS[phase] if c in reader.fieldnames), None)
    if not col:
        raise DataError(f'Geen bedragkolom voor fase {phase}: {source["url"]}')
    rows = []
    for line, row in enumerate(reader, 2):
        year = int(row['Begrotingsjaar'])
        if year != source['jaar'] or PHASES.get(row.get('Fase') or phase) != phase:
            raise DataError(f'Jaar/fase wijkt af op bronregel {line}')
        parts = row['IBOSnummer'].strip().split('.')
        if not 3 <= len(parts) <= 6 or parts[0] != str(year):
            raise DataError(f'Onbekende IBOS-hiërarchie op bronregel {line}')
        if row['VUO'] not in ('V', 'U', 'O') or row['Totaal'] not in ('J', 'N'):
            raise DataError(f'Onbekend rijtype op bronregel {line}')
        path = (row['Hoofdstuknummer'], *parts[2:])
        rows.append({'jaar': year, 'fase': phase, 'soort': 'realisatie' if phase == 'JV' else 'raming',
                     'vuo': row['VUO'], 'totaal': row['Totaal'], 'pad': path,
                     'ibos': row['IBOSnummer'], 'bronregel': line, 'bron': source['url'],
                     'bedragkolom': col, 'bedrag': amount(row[col]),
                     'hoofdstukcode': row['Hoofdstuknummer'], 'hoofdstuk': row['Hoofdstuknaam'],
                     'artikelcode': row['Artikelnummer'], 'artikel': row['Artikelnummer'] + '. ' + row['Artikelnaam'],
                     'instrument': row['Instrumentnaam'],
                     'regeling': row['Detailnaam'] or row['Instrumentnaam'] or row['Artikelnaam']})
    if not rows or not any(r['vuo'] == 'U' for r in rows):
        raise DataError('Bron bevat geen uitgaven')
    source['bedragkolom'] = col
    source['regels'] = len(rows)
    return rows


def build(snapshots, years):
    selected = []
    for year in years:
        candidates = [(raw, s) for raw, s in snapshots if s['jaar'] == year]
        if not candidates:
            raise DataError(f'Verwacht jaar {year} ontbreekt; publicatie gestopt')
        rank = max(RANK[s['fase']] for _, s in candidates)
        versions = {s['sha256']: (raw, s) for raw, s in candidates if RANK[s['fase']] == rank}
        if len(versions) != 1:
            raise DataError(f'Conflicterende bronversies voor {year}')
        selected.append(next(iter(versions.values())))
    articles, instruments, details, warnings, records, metadata = [], [], [], [], [], {}
    for raw, source in selected:
        rows = parse(raw, source)
        records.extend(rows)
        metadata[str(source['jaar'])] = {'fase': source['fase'], 'soort': rows[0]['soort'], 'bron': source['url']}
        for vuo in ('U', 'O'):
            nodes = {}
            for r in rows:
                if r['vuo'] != vuo:
                    continue
                if r['pad'] in nodes:
                    raise DataError(f'Dubbele IBOS-code {r["ibos"]} ({vuo})')
                nodes[r['pad']] = r
            children = defaultdict(list)
            for path, row in nodes.items():
                parent = next((path[:n] for n in range(len(path)-1, 1, -1) if path[:n] in nodes), None)
                children[parent].append(row)
            for path, row in nodes.items():
                kids = children[path]
                if kids:
                    difference = row['bedrag'] - sum(k['bedrag'] for k in kids)
                    if abs(difference) > max(1000, len(kids) * 500):
                        warnings.append(f'{row["jaar"]} {vuo} {row["ibos"]}: gerapporteerd totaal minus onderliggende posten = € {difference:,}')
                elif vuo == 'U':
                    details.append(row)
                if vuo == 'U' and len(path) == 4:
                    instruments.append(row)
            if vuo == 'U':
                groups = defaultdict(list)
                for r in children[None]:
                    groups[r['pad'][:2]].append(r)
                for path, roots in groups.items():
                    item = dict(roots[0])
                    item['bedrag'] = sum(r['bedrag'] for r in roots)
                    item['afgeleid'] = len(roots) != 1 or len(roots[0]['pad']) != 2
                    articles.append(item)
    ministries = {}
    # Names remain year-specific: reorganisations are not silently equated.
    for a in articles:
        key = (a['hoofdstukcode'], a['hoofdstuk'])
        m = ministries.setdefault(key, {'hoofdstuk': key[0], 'naam': key[1], 'per_jaar': {}, 'doorgesluisd': {}})
        y = str(a['jaar'])
        m['per_jaar'][y] = m['per_jaar'].get(y, 0) + a['bedrag']
    for r in instruments:
        if r['instrument'] == 'Bijdrage aan (andere) begrotingshoofdstukken':
            m = ministries[(r['hoofdstukcode'], r['hoofdstuk'])]
            y = str(r['jaar'])
            m['doorgesluisd'][y] = m['doorgesluisd'].get(y, 0) + r['bedrag']
    return {'eenheid': 'EUR', 'jaren': metadata, 'ministeries': list(ministries.values()),
            'artikelen': articles, 'instrumenten': instruments,
            'grootste_regelingen': sorted(details, key=lambda r: -r['bedrag']),
            'bronregels': records, 'bronnen': [s for _, s in selected], 'controle': warnings,
            'signalen': [{'type': 'Dekking', 'let_op': '2021–2022 ontbreken: de historische bronindeling is nog niet gevalideerd. Ontbrekend betekent niet nul.'},
                         {'type': 'Vergelijkbaarheid', 'let_op': 'Ramingen zijn geen realisaties. Departementale herindelingen en fondsbijdragen beïnvloeden vergelijkingen. Controleverschillen blijven zichtbaar; detailposten worden niet gecorrigeerd om totalen passend te maken.'}],
            'methode': 'Rijksbegroting exclusief premies, gemeenten en provincies. Per jaar één hoogste beschikbare fase. Bedragkolom hoort bij die fase. Artikelbedragen volgen de gerapporteerde hiërarchie; zonder artikeltotaal tellen alleen de bovenste beschikbare posten mee. Detailregels en ontvangsten worden niet bij artikeltotalen opgeteld. Aftrek van doorstortingen is een indicatie, geen volledig geconsolideerd overheidstotaal.'}
