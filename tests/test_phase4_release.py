"""Ticket-04 (Contract v1.3): leaderboard, soak, bench scene."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Leaderboard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['DDL_LEADERBOARD'] = str(Path(self.tmp.name) / 'lb.json')

    def tearDown(self):
        os.environ.pop('DDL_LEADERBOARD', None)
        self.tmp.cleanup()

    def test_sort_top10_and_ties(self):
        import leaderboard as L
        for i in range(12):
            L.add(f'p{i:02d}x', i * 10, 1, 7)
        L.add('first', 500, 3, 7)
        L.add('second', 500, 2, 7)  # same score, achieved later -> below
        e = L.load()
        self.assertEqual(len(e), 10)
        self.assertEqual([x['name'] for x in e[:2]], ['first', 'second'])
        self.assertEqual(set(e[0]), {'name', 'score', 'nights_won', 'achieved_at', 'seed'})
        self.assertRegex(e[0]['achieved_at'], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$')

    def test_name_rules(self):
        import leaderboard as L
        for bad in ('ab', 'x' * 13, 'a b c', 'a-b-c'):
            with self.assertRaises(ValueError):
                L.add(bad, 1, 0, 1)
        L.add('Mây_Đăng', 1, 0, 1)  # Vietnamese letters accepted (bonus)

    def test_export_cli(self):
        import leaderboard as L
        L.add('alpha', 10, 1, 1)
        out = Path(self.tmp.name) / 'out.json'
        r = subprocess.run([sys.executable, 'main.py', '--export-leaderboard', str(out)], cwd=ROOT, env=os.environ.copy())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['entries'][0]['name'], 'alpha')


class Soak(unittest.TestCase):
    def test_soak_reports_shape_and_no_crash(self):
        from perf import soak
        with tempfile.TemporaryDirectory() as d:
            r = soak(7, 3, str(Path(d) / 'soak.json'))
            self.assertEqual(json.loads((Path(d) / 'soak.json').read_text())['nights'], 3)
        self.assertEqual(r['crashes'], 0)
        self.assertEqual(len(r['results']), 3)
        self.assertLessEqual(r['mem_end_mb'], 1.2 * r['mem_start_mb'])


class BenchScene(unittest.TestCase):
    def test_standard_scene(self):
        from simulation import bench_game
        g = bench_game(42)
        self.assertEqual(len(g.shades), 200)
        self.assertEqual(len(g.motes), 100)
        self.assertEqual([l['lit'] for l in g.lanterns], [True, True, True, False, False])
        self.assertTrue(all(l['fu'] == 6000 for l in g.lanterns[:3]))
        for _ in range(600):
            g.step()
        self.assertEqual(g.state, 'playing')                      # no end condition
        self.assertEqual({s['state'] for s in g.shades}, {'wander'})  # still wandering
        self.assertEqual(len(g.shades), 200)                      # no spawning
        self.assertEqual(g.flames, 3)                             # no damage
        self.assertTrue(all(l['fu'] == 6000 for l in g.lanterns[:3]))  # no fuel decay

    def test_scene_is_seeded(self):
        from simulation import bench_game
        a, b = bench_game(42), bench_game(42)
        self.assertEqual([s['pos'] for s in a.shades], [s['pos'] for s in b.shades])


if __name__ == '__main__':
    unittest.main()
