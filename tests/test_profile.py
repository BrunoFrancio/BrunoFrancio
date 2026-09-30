import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from profile import parse_contributions


class ContributionsTest(unittest.TestCase):
    def test_matches_tooltips_by_id_and_sorts_dates(self):
        source = '''<td id="b" data-date="2026-09-30" data-level="4"></td>
        <td id="a" data-date="2026-09-29" data-level="0"></td>
        <tool-tip for="a">No contributions on September 29th.</tool-tip>
        <tool-tip for="b">1,234 contributions on September 30th.</tool-tip>'''
        self.assertEqual(parse_contributions(source), [
            {'date': '2026-09-29', 'count': 0, 'level': 0},
            {'date': '2026-09-30', 'count': 1234, 'level': 4},
        ])

    def test_rejects_missing_counts_instead_of_fabricating_zero(self):
        with self.assertRaises(ValueError):
            parse_contributions('<td id="a" data-date="2026-09-30" data-level="3"></td>')

    def test_rejects_error_pages(self):
        with self.assertRaises(ValueError):
            parse_contributions('<html>Too many requests</html>')


if __name__ == '__main__':
    unittest.main()
