"""Versioned article scope, not an estimate of the total cost of asylum."""
from pipeline_sources import DataError
from pipeline_organisations import organisation

SCOPE = {2023: 'VI', 2024: 'VI', 2025: 'XX', 2026: 'XX'}
ORGANISATIONS = ('COA', 'IND', 'VluchtelingenWerk Nederland')
UKRAINE = {'Nationaal Programma Oekraïense Vluchtelingen', 'Nationaal Programma Oekraïense Ontheemden'}


def build_asylum(data):
    result = {}
    for year, meta in data['jaren'].items():
        chapter = SCOPE.get(int(year))
        if chapter is None:
            result[year] = {'status': 'Afbakening voor dit jaar nog niet gevalideerd'}
            continue
        inside = lambda r: r['jaar'] == int(year) and r['hoofdstukcode'] == chapter and r['artikelcode'] == '37'
        articles = [r for r in data['artikelen'] if inside(r)]
        if len(articles) != 1:
            raise DataError(f'Asielpagina: verwacht precies één artikel {chapter}/37 voor {year}')
        posts = [r for r in data['grootste_regelingen'] if inside(r)]
        grouped = {label: [] for label in (*ORGANISATIONS, 'Oekraïense ontheemden', 'Overige migratieposten')}
        for row in posts:
            label = organisation(row['regeling'])
            if label not in ORGANISATIONS:
                label = 'Oekraïense ontheemden' if row['regeling'] in UKRAINE else 'Overige migratieposten'
            grouped[label].append(row)
        comparisons = []
        for name in ORGANISATIONS:
            budget = [r for r in data['grootste_regelingen'] if r['jaar'] == int(year) and organisation(r['regeling']) == name]
            receivers = [r for r in data['ontvangers'] if r['jaar'] == int(year) and organisation(r['naam']) == name]
            budget_total = sum(r['bedrag'] for r in budget) if budget else None
            received_total = sum(r['bedrag'] for r in receivers) if receivers else None
            comparable = meta['soort'] == 'realisatie' and budget_total is not None and received_total is not None
            comparisons.append({'naam': name, 'begrotingsposten': budget, 'ontvangerregels': receivers,
                                'begrotingsbedrag': budget_total, 'ontvangerbedrag': received_total,
                                'verschil': received_total - budget_total if comparable else None,
                                'buiten_artikel': [r for r in budget if not inside(r)]})
        result[year] = {'status': 'beschikbaar', 'hoofdstuk': chapter, 'artikel': articles[0],
                        'groepen': [{'naam': label, 'bedrag': sum(r['bedrag'] for r in rows), 'posten': rows}
                                    for label, rows in grouped.items()],
                        'aansluitverschil': articles[0]['bedrag'] - sum(r['bedrag'] for r in posts),
                        'organisaties': comparisons,
                        'ontvangerbron': next((s['url'] for s in data['bronnen'] if s.get('type') == 'ontvangers' and s['jaar'] == int(year)), None),
                        'toelichting': f'https://www.rijksfinancien.nl/jaarverslag/{year}/{chapter}' if meta['soort'] == 'realisatie'
                                        else f'https://www.rijksfinancien.nl/memorie-van-toelichting/{year}/OWB/{chapter}'}
    data['asiel'] = result
