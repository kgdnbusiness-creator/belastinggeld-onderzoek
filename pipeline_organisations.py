"""Recipient disclosures supplement budgets; they must never be added to them."""
import json
from urllib.parse import urlencode
from pipeline_sources import DataError, download, source_record, RECIPIENT_API, RECIPIENT_YEARS

ALIASES = {
    'COA': {'coa', 'centraal orgaan opvang asielzoekers', 'centraal orgaan opvang asielzoekers (coa)', 'centraal bureau coa'},
    'VluchtelingenWerk Nederland': {'vluchtelingenwerk', 'vluchtelingenwerk nederland',
                                  'stichting vluchtelingenwerk nederland', 'vluchtingenwerk nederland'},
}


def organisation(name):
    value = ' '.join(str(name).casefold().split())
    return next((key for key, aliases in ALIASES.items() if value in aliases), None)


def recipient_rows(raw, year):
    doc = json.loads(raw)
    if not isinstance(doc, dict) or not isinstance(doc.get('ontvangers'), list) or not doc['ontvangers']:
        raise DataError(f'Ontvangersbron {year}: onbekend of leeg schema')
    rows = []
    for item in doc['ontvangers']:
        value = item.get('realisatie', {}).get(str(year))
        if isinstance(value, bool) or not isinstance(value, int):
            raise DataError(f'Ontvangersbron {year}: bedrag is geen geheel aantal euro’s')
        name = str(item['naam'])
        rows.append({'jaar': year, 'naam': name, 'organisatie': organisation(name), 'bedrag': value})
    return rows


def enrich(data, cache, offline=False, refresh=False):
    data['organisaties'] = [{'organisatie': name, 'begrotingsposten': [r for r in data['grootste_regelingen']
                              if organisation(r['regeling']) == name]} for name in ALIASES]
    data['ontvangers'] = []
    data['ontvangerdekking'] = {}
    if offline:
        available = set()
    else:
        raw = download(RECIPIENT_YEARS, cache, refresh)
        years = json.loads(raw)
        if not isinstance(years, (dict, list)):
            raise DataError('Onbekend schema beschikbare ontvangerjaren')
        available = {int(y) for y in years}
    for value in data['jaren']:
        year = int(value)
        if year not in available:
            data['ontvangerdekking'][value] = 'Niet geladen (offline)' if offline else 'Nog niet beschikbaar in de ontvangersbron'
            continue
        url = RECIPIENT_API + '?' + urlencode({'year[]': year})
        raw = download(url, cache, refresh)
        data['ontvangers'].extend(recipient_rows(raw, year))
        data['bronnen'].append(source_record(url, raw, jaar=year, type='ontvangers', eenheid='EUR'))
        data['ontvangerdekking'][value] = 'Gepubliceerde ontvangers van financiële instrumenten; geen volledige dekking van alle overheidsbetalingen'
    data['organisatie_methode'] = ('Begrotingsposten en ontvangerrealisaties zijn twee afzonderlijke bronbeelden en worden nooit bij elkaar opgeteld. '
        'De koppeling COA/VluchtelingenWerk gebruikt een beperkte, expliciete namenlijst; geen bewezen transactiekoppeling of KvK-identificatie. '
        'Een begrotingspost kan een bijdrage aan een uitvoerder betreffen en bewijst niet wie uiteindelijk wordt betaald. '
        'De EU is geen enkele ontvanger in deze koppeling: afdrachten, ontvangsten en Europese projectsubsidies hebben verschillende dekking. '
        'Zoek daarvoor ook op Europese Unie, BNI, BTW en invoerrechten. Een complete netto EU-positie is nog niet berekend.')
