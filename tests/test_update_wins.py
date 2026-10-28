import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_wins import parse_maxpreps_record, update_from_record, career_wins


def example(season='26-27', record='12-18'):
    return f'''<!doctype html><html><head><title>Schedule - Saint Viator Lions (Arlington Heights, IL) Volleyball {season}</title></head><body>
    <h1>Saint Viator Volleyball Schedule</h1><p>2026-27</p>
    <div>Overall <span>{record}</span> 0.400 Win Pct</div><div>Conference 1-5</div>
    <div>8/26 6:00pm Warren Township W 2-1</div></body></html>'''


class TestAutoUpdate(unittest.TestCase):
    def setUp(self):
        self.state = {'baseline_wins': 416, 'baseline_season': '2026-27', 'baseline_season_wins': 16,
                      'verified_floor': 416, 'season_records': {'2026-27': 16}}

    def test_parse_known_maxpreps_style(self):
        self.assertEqual(parse_maxpreps_record(example()), ('2026-27', 12, 18))

    def test_source_behind_baseline_does_not_subtract(self):
        update_from_record(self.state, '2026-27', 12)
        self.assertEqual(career_wins(self.state), 416)

    def test_second_2026_win_after_baseline(self):
        update_from_record(self.state, '2026-27', 17)
        self.assertEqual(career_wins(self.state), 417)

    def test_2027_new_season_sums_without_double_counting(self):
        update_from_record(self.state, '2026-27', 17)
        update_from_record(self.state, '2027-28', 4)
        self.assertEqual(career_wins(self.state), 421)
        update_from_record(self.state, '2027-28', 3)
        self.assertEqual(career_wins(self.state), 421)

    def test_verified_floor(self):
        self.state['verified_floor'] = 420
        self.assertEqual(career_wins(self.state), 420)
        update_from_record(self.state, '2027-28', 5)
        self.assertEqual(career_wins(self.state), 421)

    def test_rejects_different_team_and_missing_score(self):
        with self.assertRaises(ValueError):
            parse_maxpreps_record(example().replace('Saint Viator', 'Other school'))
        with self.assertRaises(ValueError):
            parse_maxpreps_record(example().replace('Overall', 'Conference'))

    def test_rejects_unreasonable_count(self):
        with self.assertRaises(ValueError):
            parse_maxpreps_record(example(record='999-0'))


if __name__ == '__main__':
    unittest.main()
