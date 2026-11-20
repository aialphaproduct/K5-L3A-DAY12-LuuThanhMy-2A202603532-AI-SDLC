"""Ticket-03 (Contract v1.2): lantern fuel, drain, dawn win rule, capacity, scoring."""
import unittest

from test_phase2_features import QUIET, events, run, snap


def lantern(row, lid):
    return next(l for l in row['lanterns'] if l['id'] == lid)


class Phase3Fuel(unittest.TestCase):
    def test_new_night_durations(self):
        for night, dur in ((1, 240), (2, 270), (3, 300)):
            self.assertEqual(snap(run(night, QUIET, [], 0), 0)['time_left_s'], dur)

    def test_light_sets_fuel_100_and_decays_1_per_second(self):
        sc = dict(QUIET, player={'carried': 10}, lanterns=[{'id': 'L1', 'pos': [0, 0, 1]}])
        rows = run(1, sc, [{'tick': 0, 'interact': True}], 61)
        lit = events(rows, 'lantern_lit')[0]
        self.assertEqual(lit['data'], {'lantern_id': 'L1', 'relight': False})
        self.assertEqual(lantern(snap(rows, 61), 'L1')['fuel'], 99.0)
        self.assertEqual(snap(rows, 61)['score'], 10 * 5 + 100)

    def test_lantern_goes_out_and_relight_costs_5(self):
        sc = dict(QUIET, player={'carried': 5}, lanterns=[{'id': 'L1', 'pos': [0, 0, 1], 'lit': True, 'fuel': 0.05}])
        rows = run(1, sc, [{'tick': 5, 'interact': True}], 6)
        self.assertEqual(events(rows, 'lantern_out')[0]['data'], {'lantern_id': 'L1'})
        l = lantern(snap(rows, 4), 'L1')
        self.assertEqual((l['lit'], l['fuel'], l['deposited'], l['ever_lit']), (False, 0, 0, True))
        relit = events(rows, 'lantern_lit')[0]['data']
        self.assertTrue(relit['relight'])
        end = lantern(snap(rows, 6), 'L1')
        self.assertEqual((end['lit'], end['relit_count']), (True, 1))
        self.assertEqual(snap(rows, 6)['score'], 5 * 5 + 40)

    def test_refuel_formula(self):
        # fuel 55 -> needs ceil(45/10)=5 motes; carrying 7 uses 5 and fills to 100
        sc = dict(QUIET, player={'carried': 7}, lanterns=[{'id': 'L1', 'pos': [0, 0, 1], 'lit': True, 'fuel': 55}])
        rows = run(1, sc, [{'tick': 0, 'interact': True}], 1)
        r = events(rows, 'refuel')[0]['data']
        self.assertEqual((r['amount'], r['fuel']), (5, 100.0))
        self.assertEqual(snap(rows, 1)['player']['carried'], 2)
        self.assertEqual(snap(rows, 1)['score'], 25)

    def test_tiny_gap_refuel_uses_one_mote(self):
        # Decay (tick step 2) runs before interact (step 5), so a lantern set to 100 is 99.98 when E lands:
        # it is not full, still the nearest receiver, and ceil(0.02/10) = 1 mote tops it up.
        sc = dict(QUIET, player={'carried': 4},
                  lanterns=[{'id': 'L1', 'pos': [0, 0, 1], 'lit': True, 'fuel': 100},
                            {'id': 'L2', 'pos': [0, 0, 1.5]}])
        rows = run(1, sc, [{'tick': 0, 'interact': True}], 1)
        r = events(rows, 'refuel')[0]['data']
        self.assertEqual((r['lantern_id'], r['amount'], r['fuel']), ('L1', 1, 100.0))

    def test_shade_drains_weak_lantern(self):
        sc = dict(QUIET, player={'pos': [0, 0, -30]},
                  lanterns=[{'id': 'L1', 'pos': [0, 0, 25], 'lit': True, 'fuel': 20}],
                  shades=[{'id': 'S1', 'pos': [1, 0, 25], 'state': 'wander'}])
        rows = run(1, sc, [], 62)
        self.assertEqual(snap(rows, 2)['shades'][0]['state'], 'drain')
        d = events(rows, 'fuel_drain')[0]['data']
        self.assertEqual((d['lantern_id'], d['shade_id']), ('L1', 'S1'))
        # 20 - 1/s decay - 5/s drain over ~1 s
        self.assertAlmostEqual(lantern(snap(rows, 62), 'L1')['fuel'], 14.0, delta=0.2)

    def test_safe_zone_kept_at_exactly_30(self):
        sc = dict(QUIET, player={'pos': [0, 0, -30]},
                  lanterns=[{'id': 'L1', 'pos': [0, 0, 25], 'lit': True, 'fuel': 31}],
                  shades=[{'id': 'S1', 'pos': [1, 0, 25], 'state': 'wander'}])
        rows = run(1, sc, [], 2)
        pos = snap(rows, 2)['shades'][0]['pos']
        self.assertGreaterEqual(((pos[0]) ** 2 + (pos[2] - 25) ** 2) ** 0.5, 5.99)

    def test_drain_to_chase_when_player_near(self):
        sc = dict(QUIET, player={'pos': [5, 0, 25]},
                  lanterns=[{'id': 'L1', 'pos': [0, 0, 25], 'lit': True, 'fuel': 20}],
                  shades=[{'id': 'S1', 'pos': [1, 0, 25], 'state': 'drain', 'target_lantern_id': 'L1'}])
        rows = run(1, sc, [], 1)
        self.assertEqual(snap(rows, 1)['shades'][0]['state'], 'chase')

    def test_pulse_on_draining_shade_scores_15(self):
        sc = dict(QUIET, player={'pos': [7, 0, 25], 'carried': 3},
                  lanterns=[{'id': 'L1', 'pos': [0, 0, 25], 'lit': True, 'fuel': 20}],
                  shades=[{'id': 'S1', 'pos': [3, 0, 25], 'state': 'drain', 'target_lantern_id': 'L1'}])
        rows = run(1, sc, [{'tick': 0, 'pulse': True}], 1)
        self.assertEqual(events(rows, 'pulse')[0]['data']['stunned_ids'], ['S1'])
        self.assertEqual(snap(rows, 1)['score'], 15)

    def test_stun_ends_in_wander(self):
        sc = dict(QUIET, player={'pos': [0, 0, -30]}, shades=[{'id': 'S1', 'pos': [30, 0, 0], 'state': 'stunned', 'state_ticks_left': 2}])
        rows = run(1, sc, [], 3)
        self.assertEqual(snap(rows, 3)['shades'][0]['state'], 'wander')

    def test_no_early_win_and_dawn_survived(self):
        lit = [{'id': f'L{i}', 'lit': True, 'fuel': 100} for i in (1, 2, 3)]
        sc = dict(QUIET, lanterns=lit, time_left_s=1)
        rows = run(1, sc, [], 120)
        go = events(rows, 'game_over')[0]
        self.assertEqual(go['data'], {'result': 'won', 'reason': 'dawn_survived'})
        self.assertEqual(go['tick'], 60)
        # bonus: 3 lanterns x (50 + floor(fuel)) + 3 flames x 50
        self.assertEqual(rows[-1]['score'], 3 * (50 + 99) + 150)

    def test_dawn_below_threshold_loses(self):
        lit = [{'id': f'L{i}', 'lit': True, 'fuel': 100} for i in (1, 2)]
        rows = run(1, dict(QUIET, lanterns=lit, time_left_s=1), [], 120)
        self.assertEqual(events(rows, 'game_over')[0]['data'], {'result': 'lost', 'reason': 'dawn'})

    def test_all_lit_does_not_end_night(self):
        lit = [{'id': f'L{i}', 'lit': True, 'fuel': 100} for i in range(1, 6)]
        rows = run(1, dict(QUIET, lanterns=lit), [], 10)
        self.assertEqual(rows[-1]['state'], 'playing')

    def test_capacity_grows_with_lights(self):
        sc = dict(QUIET, player={'successful_lights': 3})
        self.assertEqual(snap(run(1, sc, [], 0), 0)['player']['capacity'], 16)
        sc = dict(QUIET, player={'successful_lights': 9})
        self.assertEqual(snap(run(1, sc, [], 0), 0)['player']['capacity'], 20)

    def test_snapshot_fields_v12(self):
        row = snap(run(1, QUIET, [], 0), 0)
        l = row['lanterns'][0]
        for k in ('fuel', 'ever_lit', 'relit_count'):
            self.assertIn(k, l)
        self.assertEqual(l['fuel'], 0)
        self.assertIn('capacity', row['player'])


if __name__ == '__main__':
    unittest.main()
