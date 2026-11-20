"""One headless scenario per Ticket-02 feature (Contract v1.1)."""
import json
import os
import tempfile
import unittest

from simulation import run_headless


def run(night, scenario, frames, ticks, every=1, seed=3):
    paths = []
    try:
        for obj in (scenario, {'frames': frames}):
            fd, path = tempfile.mkstemp(suffix='.json')
            with os.fdopen(fd, 'w') as f:
                json.dump(obj, f)
            paths.append(path)
        return [json.loads(x) for x in run_headless(seed, ticks, every, paths[0], paths[1], night)]
    finally:
        for p in paths:
            os.unlink(p)


def events(rows, name):
    return [r for r in rows if r['type'] == 'event' and r['name'] == name]


def snap(rows, tick):
    return next(r for r in rows if r['type'] == 'snapshot' and r['tick'] == tick)


QUIET = {'random_motes': False, 'random_shades': False, 'random_drifters': False}


class Phase2Features(unittest.TestCase):
    def test_night_start_event(self):
        rows = run(1, QUIET, [], 2)
        ns = events(rows, 'night_start')
        self.assertEqual(len(ns), 1)
        self.assertEqual(ns[0]['tick'], 1)
        self.assertEqual(ns[0]['data'], {'night': 1})

    def test_score_on_deposit_not_pickup(self):
        sc = dict(QUIET, motes=[[0, 0, 0.5]], lanterns=[{'id': 'L1', 'pos': [0, 0, 1.5]}])
        rows = run(1, sc, [{'tick': 2, 'interact': True}], 4)
        self.assertEqual(snap(rows, 1)['score'], 0)  # picked up, not scored yet
        self.assertEqual(events(rows, 'deposit')[0]['data']['amount'], 1)
        # Ticket-03 replaced the per-mote deposit score: +10 (Ticket-02) -> +5. Still scored on deposit only.
        self.assertEqual(snap(rows, 4)['score'], 5)

    def test_night3_shade_speed_is_4_5(self):
        sc = dict(QUIET, player={'pos': [0, 0, -40]}, shades=[{'id': 'S1', 'pos': [10, 0, -40], 'state': 'chase'}])
        rows = run(3, sc, [], 60)
        moved = 10 - snap(rows, 60)['shades'][0]['pos'][0]
        self.assertAlmostEqual(moved, 4.5, places=2)

    def test_night1_shade_speed_is_4(self):
        sc = dict(QUIET, shades=[{'id': 'S1', 'pos': [10, 0, 0], 'state': 'chase'}])
        rows = run(1, sc, [], 60)
        self.assertAlmostEqual(10 - snap(rows, 60)['shades'][0]['pos'][0], 4.0, places=2)

    def test_fall_penalty_and_respawn(self):
        sc = dict(QUIET, player={'pos': [39.5, 0, 0], 'carried': 4})
        rows = run(1, sc, [{'tick': 0, 'move': [1, 0]}], 200)
        hits = events(rows, 'player_hit')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['data']['by'], 'fall')
        self.assertEqual(hits[0]['data']['lost'], 4)
        self.assertEqual(hits[0]['data']['flames'], 2)
        t = hits[0]['tick']
        waiting = snap(rows, t + 30)['player']
        self.assertEqual(waiting['carried'], 0)
        back = snap(rows, t + 60)['player']
        self.assertEqual(back['pos'], [0.0, 0.0, 0.0])
        self.assertGreater(back['invuln'], 1.4)

    def test_fall_with_last_flame_loses(self):
        sc = dict(QUIET, player={'pos': [39.5, 0, 0], 'flames': 1})
        rows = run(1, sc, [{'tick': 0, 'move': [1, 0]}], 200)
        self.assertEqual(rows[-1]['state'], 'lost')
        self.assertEqual(events(rows, 'game_over')[0]['data']['reason'], 'no_flames')

    def test_night2_jump_pad_lands_on_other_island(self):
        sc = dict(QUIET, player={'pos': [20, 0, 18]})
        rows = run(2, sc, [], 130)
        p = snap(rows, 130)['player']
        self.assertTrue(p['grounded'])
        self.assertLess(((p['pos'][0] - 70) ** 2 + p['pos'][2] ** 2) ** 0.5, 28)
        self.assertEqual(events(rows, 'player_hit'), [])

    def test_night3_pad_reaches_tier2(self):
        sc = dict(QUIET, player={'pos': [0, 3, 13]})
        rows = run(3, sc, [], 90)
        p = snap(rows, 90)['player']
        self.assertTrue(p['grounded'])
        self.assertEqual(p['pos'][1], 6.0)

    def test_night3_ramp_climbs_to_tier1(self):
        import math
        a = math.radians(30)
        start = [math.cos(a) * 31, 0, math.sin(a) * 31]
        sc = dict(QUIET, player={'pos': start})
        # walk inward along the ramp (towards the centre)
        rows = run(3, sc, [{'tick': 0, 'move': [-math.cos(a), -math.sin(a)]}], 70)
        self.assertGreaterEqual(snap(rows, 70)['player']['pos'][1], 2.9)

    def test_night3_cliff_blocks_walking_up(self):
        sc = dict(QUIET, player={'pos': [0, 0, 26]})
        rows = run(3, sc, [{'tick': 0, 'move': [0, -1]}], 60)
        p = snap(rows, 60)['player']
        self.assertEqual(p['pos'][1], 0.0)
        self.assertGreaterEqual(p['pos'][2], 24.0)

    def test_night3_start_stands_on_tier2_and_can_walk_out(self):
        rows = run(3, QUIET, [{'tick': 0, 'move': [0, -1]}], 40)
        self.assertEqual(snap(rows, 0)['player']['pos'], [0.0, 0.0, 0.0])  # contract start point
        self.assertEqual(snap(rows, 1)['player']['pos'][1], 6.0)           # stands on tier 2, not on the tower top
        self.assertLess(snap(rows, 40)['player']['pos'][2], -3.5)          # walked out of the tower footprint

    def test_night3_tower_blocks_from_outside(self):
        sc = dict(QUIET, player={'pos': [0, 6, -4]})
        rows = run(3, sc, [{'tick': 0, 'move': [0, 1]}], 60)
        self.assertLessEqual(snap(rows, 60)['player']['pos'][2], -2.0)

    def test_pulse_pushes_4m_and_overlap_pushes_plus_x(self):
        sc = dict(QUIET, player={'carried': 3}, shades=[{'id': 'S1', 'pos': [0, 0, 0], 'state': 'wander'}])
        rows = run(1, sc, [{'tick': 0, 'pulse': True}], 16)
        self.assertEqual(snap(rows, 1)['shades'][0]['state'], 'stunned')
        self.assertAlmostEqual(snap(rows, 16)['shades'][0]['pos'][0], 4.0, places=2)

    def test_shade_cap_per_night(self):
        rows = run(2, {'random_drifters': False}, [], 300 + 420 * 10, every=600)
        counts = [len(r['shades']) for r in rows if r['type'] == 'snapshot']
        self.assertEqual(max(counts), 8)

    def test_wind_cycle_30s_lasting_5s(self):
        rows = run(3, dict(QUIET, wind_enabled=True), [], 3700, every=1)
        active = [r['sim_tick'] for r in rows if r['type'] == 'snapshot' and r['wind']['active']]
        self.assertEqual(active[0], 1500)
        self.assertEqual(len([t for t in active if t < 1800]), 300)
        self.assertIn(3300, active)

    def test_drifter_returns_to_idle_when_condition_lost(self):
        sc = dict(QUIET, player={'carried': 5}, drifters=[{'id': 'D1', 'pos': [10, 0, 0], 'state': 'chase'}])
        # pulse costs 3 -> carried 2 < 5; the drifter is 10 m away (outside the 5 m pulse) so it is not hit
        rows = run(2, sc, [{'tick': 0, 'pulse': True}], 3)
        self.assertEqual(snap(rows, 3)['drifters'][0]['state'], 'idle')

    def test_drifter_steal(self):
        sc = dict(QUIET, player={'carried': 6}, drifters=[{'id': 'D1', 'pos': [1, 0, 0], 'state': 'chase'}])
        rows = run(2, sc, [], 2)
        st = events(rows, 'drifter_steal')[0]['data']
        self.assertEqual((st['amount'], st['carried']), (3, 3))

    def test_charm_pickup(self):
        sc = dict(QUIET, player={'pos': [35, 0, 0]})
        rows = run(2, sc, [], 2)
        self.assertEqual(events(rows, 'charm_picked')[0]['data'], {'charm_id': 'C1', 'charm_ticks': 600})

    def test_pause_events_have_empty_data(self):
        rows = run(1, QUIET, [{'tick': 0, 'pause': True}, {'tick': 1, 'pause': False}, {'tick': 2, 'pause': True}], 4)
        self.assertEqual(events(rows, 'paused')[0]['data'], {})
        self.assertEqual(events(rows, 'resumed')[0]['data'], {})


if __name__ == '__main__':
    unittest.main()
