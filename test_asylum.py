import unittest
from pipeline_asylum import build_asylum
from pipeline_sources import DataError
from pipeline_organisations import organisation


def row(name, value, chapter='XX', article='37'):
    return {'jaar': 2025, 'hoofdstukcode': chapter, 'artikelcode': article, 'regeling': name, 'bedrag': value}


def fixture():
    return {'jaren': {'2025': {'soort': 'realisatie'}}, 'artikelen': [row('', 150)],
            'grootste_regelingen': [row('COA', 100), row('IND', 30), row('Nationaal Programma Oekraïense Ontheemden', 20), row('COA', 7, 'VI', '38')],
            'ontvangers': [{'jaar': 2025, 'naam': 'Centraal Bureau COA', 'bedrag': 110}], 'bronnen': []}


class AsylumTests(unittest.TestCase):
    def test_article_groups_do_not_add_other_articles(self):
        data=fixture(); build_asylum(data); a=data['asiel']['2025']
        self.assertEqual(sum(g['bedrag'] for g in a['groepen']),150)
        self.assertEqual(a['aansluitverschil'],0)
        coa=a['organisaties'][0]
        self.assertEqual(coa['begrotingsbedrag'],107)
        self.assertEqual(coa['verschil'],3)
        self.assertEqual(len(coa['buiten_artikel']),1)

    def test_missing_is_not_zero(self):
        data=fixture();build_asylum(data)
        self.assertIsNone(data['asiel']['2025']['organisaties'][1]['ontvangerbedrag'])
        self.assertIsNone(data['asiel']['2025']['organisaties'][1]['verschil'])

    def test_estimate_not_compared_with_actual(self):
        data=fixture();data['jaren']['2025']['soort']='raming';build_asylum(data)
        self.assertIsNone(data['asiel']['2025']['organisaties'][0]['verschil'])

    def test_unknown_year_not_silently_classified(self):
        data=fixture();data['jaren']={'2027': {'soort':'raming'}};build_asylum(data)
        self.assertNotEqual(data['asiel']['2027']['status'],'beschikbaar')

    def test_article_required(self):
        data=fixture();data['artikelen']=[]
        with self.assertRaises(DataError):build_asylum(data)

    def test_historical_names_and_no_substring_matching(self):
        self.assertEqual(organisation('Vluchtelingenwerk Nederland (VWN)'), 'VluchtelingenWerk Nederland')
        self.assertEqual(organisation('Immigratie- en Naturalisatiedienst'), 'IND')
        self.assertIsNone(organisation('INDustrie'))

    def test_discrepancy_is_preserved(self):
        data=fixture();data['artikelen'][0]['bedrag']=160;build_asylum(data)
        self.assertEqual(data['asiel']['2025']['aansluitverschil'],10)

if __name__=='__main__':unittest.main()
