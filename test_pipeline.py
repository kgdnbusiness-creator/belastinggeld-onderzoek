import csv
import io
import json
import unittest
from pipeline_model import amount, build, parse
from pipeline_sources import DataError, source_record
from pipeline_organisations import organisation, recipient_rows
from pipeline import render


def fixture(phase='JV', count=1, year=2025):
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')
    writer.writerow(['IBOSnummer', 'Begrotingsjaar', 'VUO', 'Totaal', 'Hoofdstuknummer', 'Hoofdstuknaam',
                     'Artikelnummer', 'Artikelnaam', 'Instrumentnaam', 'Detailnaam', 'Realisatie', 'StandO1', 'StandSBS'])
    writer.writerow([f'{year}.1.1', year, 'U', 'J', 'I', 'Hoofdstuk', '1', 'Artikel', '', '', count, 99, count])
    for index in range(count):
        writer.writerow([f'{year}.1.1.0.{index}', year, 'U', 'N', 'I', 'Hoofdstuk', '1', 'Artikel', 'Bijdrage', f'Naam {index}', 1, 99, 1])
    raw = out.getvalue().encode()
    return raw, source_record('fixture.csv', raw, jaar=year, fase=phase)


class PipelineTests(unittest.TestCase):
    def test_sbs_uses_its_own_column(self):
        rows = parse(*fixture('SBS'))
        self.assertEqual(rows[0]['bedrag'], 1000)
        self.assertEqual(rows[0]['bedragkolom'], 'StandSBS')
        self.assertEqual(rows[0]['soort'], 'raming')

    def test_zero_code_and_terminal_instrument_retained(self):
        data = build([fixture()], [2025])
        self.assertEqual(len(data['instrumenten']), 1)
        self.assertEqual(data['grootste_regelingen'][0]['pad'], ('I', '1', '0', '0'))
        self.assertEqual(data['controle'], [])

    def test_all_detail_rows_survive(self):
        self.assertEqual(len(build([fixture(count=250)], [2025])['grootste_regelingen']), 250)

    def test_requested_year_cannot_disappear(self):
        with self.assertRaises(DataError):
            build([fixture()], [2024, 2025])

    def test_duplicate_file_not_double_counted(self):
        data = build([fixture(), fixture()], [2025])
        self.assertEqual(data['artikelen'][0]['bedrag'], 1000)

    def test_conflicting_same_phase_rejected(self):
        with self.assertRaises(DataError):
            build([fixture(), fixture(count=2)], [2025])

    def test_latest_phase_selected(self):
        data = build([fixture('SBS', 2), fixture('JV')], [2025])
        self.assertEqual(data['artikelen'][0]['bedrag'], 1000)

    def test_bad_amount_not_zero(self):
        for value in ('', 'onbekend', 'NaN', '1.234.567', 'Infinity'):
            with self.assertRaises(DataError):
                amount(value)
        self.assertEqual(amount('-1,5'), -1500)

    def test_source_discrepancy_does_not_change_reported_total(self):
        raw, source = fixture(count=2)
        raw = raw.replace(b';2;99;2', b';3;99;3')
        data = build([(raw, source)], [2025])
        self.assertEqual(data['artikelen'][0]['bedrag'], 3000)
        # Exactly one thousand is accepted as source rounding; larger isn't.
        raw = raw.replace(b';3;99;3', b';5;99;5')
        self.assertTrue(build([(raw, source)], [2025])['controle'])

    def test_recipient_amount_already_euros(self):
        rows = recipient_rows(json.dumps({'ontvangers': [{'naam': 'Centraal Bureau COA', 'realisatie': {'2024': 1234}}]}), 2024)
        self.assertEqual(rows[0]['bedrag'], 1234)
        self.assertEqual(rows[0]['organisatie'], 'COA')
        self.assertIsNone(organisation('Een coachingbureau'))

    def test_script_payload_is_escaped(self):
        html = render({'naam': '</script><script>alert(1)</script>'})
        self.assertNotIn('"naam": "</script>', html)
        self.assertIn('\\u003c/script>', html)


if __name__ == '__main__':
    unittest.main()
