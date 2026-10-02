# Belastinggeld-pipeline

Doorzoekbare Rijksbegroting met bronverwijzingen en afzonderlijke ontvangersgegevens. Python 3.12+, standaardbibliotheek; Linux vereist `libarchive-tools` (bsdtar), Windows heeft een geschikte `tar`.

```sh
python -m unittest -v
python pipeline.py --years 2023-2026
# Offline begrotingscontrole; ontvangers worden dan expliciet als niet geladen getoond:
python pipeline.py --local ./csv --years 2023-2026
```

Zonder `--years` verwerkt de pipeline 2023 tot en met het huidige jaar. `--refresh` vernieuwt de lokale broncache. Open `site/index.html` na het bouwen. De GitHub-workflow test wijzigingen en bouwt/publiceert main; fouten blokkeren de nieuwe publicatie. Het bestaande dashboard blijft dan staan.

## Wat is zichtbaar?

- Hoofdstukken, artikelen, instrumenten en alle beschikbare detailposten, met jaar en begrotingsfase.
- Organisaties: benoemde COA- en VluchtelingenWerk-posten naast de ontvangersbron; andere ontvangers zijn doorzoekbaar.
- EU: de posten voor Europese samenwerking onder Buitenlandse Zaken, met uitgaven en ontvangsten apart.
- Controleverschillen, bronbestanden, SHA-256 en methode. CSV-export bevat alle geselecteerde posten, ook als het scherm alleen de grootste toont.

## Afbakening

Alleen de Rijksbegroting exclusief premies, gemeenten en provincies. Begrotingsramingen zijn geen gerealiseerde betalingen. Ontvangersbedragen zijn een afzonderlijke, onvolledige bron en worden nooit bij begrotingstotalen opgeteld. Naamkoppelingen zijn geen bewezen transactiekoppelingen. De EU-selectie is geen volledige Nederlandse netto EU-positie.

2021–2022 worden niet stilzwijgend overgeslagen of als nul weergegeven: de historische indeling/dekking vereist een afzonderlijke adapter. Bronverschillen blijven zichtbaar. Doorstortingen aftrekken is slechts een indicatie van consolidatie.

Zie [controle, verificatie en implementatievoorstel](PIPELINE-CONTROLE.md) voor bevindingen en de vervolgstappen voor thematoedeling (klimaat/asiel/defensie), historische jaren en volledige organisatieketens.

De actieve template is `site/template.html`; `dashboard-extra.js` vult de bestaande vormgeving aan. Alleen `.github/workflows/update.yml` is de actieve workflow. De oude gelijknamige bestanden in de hoofdmap zijn niet in gebruik.
