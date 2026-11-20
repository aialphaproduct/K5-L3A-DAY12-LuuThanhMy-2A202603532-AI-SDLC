import json
import tempfile
import unittest
from simulation import run_headless

class Phase2ContractTests(unittest.TestCase):
    def run_case(self, night, scenario, frames, ticks=5):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as sf, tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as inf:
            json.dump(scenario, sf); json.dump({'frames': frames}, inf)
            sf.flush(); inf.flush()
            return [json.loads(x) for x in run_headless(11, ticks, 1, sf.name, inf.name, night)]

    def test_night_layouts_and_snapshot_fields(self):
        for night, count in ((1, 5), (2, 6), (3, 7)):
            rows = self.run_case(night, {'random_motes': False, 'random_shades': False, 'random_drifters': False}, [], 1)
            snap = rows[0]
            self.assertEqual(snap['night'], night)
            self.assertEqual(len(snap['lanterns']), count)
            self.assertIn('wind', snap); self.assertIn('drifters', snap); self.assertIn('charms', snap)
            self.assertIn('dash_cd_s', snap['player'])

    def test_dash_event_and_pause_freezes_simulation(self):
        rows = self.run_case(1, {'random_motes': False, 'random_shades': False}, [{'tick': 0, 'dash': True}, {'tick': 1, 'dash': False}, {'tick': 2, 'pause': True}, {'tick': 3, 'pause': False}], 5)
        self.assertTrue(any(r.get('name') == 'dash' for r in rows if r['type'] == 'event'))
        paused = next(r for r in rows if r.get('name') == 'paused')
        snap = [r for r in rows if r['type'] == 'snapshot' and r['tick'] == 3][0]
        self.assertEqual(snap['state'], 'paused')
        self.assertEqual(snap['sim_tick'], paused['tick'] - 1)

    def test_pulse_uses_v11_cost(self):
        rows = self.run_case(1, {'player': {'carried': 3}, 'random_motes': False, 'random_shades': False, 'shades': [{'id':'S1','pos':[2,0,0]}]}, [{'tick':0,'pulse':True}], 2)
        self.assertTrue(any(r.get('name') == 'pulse' for r in rows if r['type'] == 'event'))

if __name__ == '__main__': unittest.main()
