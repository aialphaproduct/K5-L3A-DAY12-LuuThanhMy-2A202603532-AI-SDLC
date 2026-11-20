# Phase 3 evidence (Ticket-03, Contract v1.2)

Run: `python3 -m unittest discover -s tests` → 37 tests, all pass (15 new in `tests/test_phase3_fuel.py`).

| Ticket-03 item | Test |
|---|---|
| Night lengths 240 / 270 / 300 s | `test_new_night_durations` |
| Light sets fuel 100, decays 1/s, scores +5/mote +100 | `test_light_sets_fuel_100_and_decays_1_per_second` |
| Lantern goes out (`lantern_out`, deposited 0, `ever_lit` kept); relight costs 5, +40, `relit_count` | `test_lantern_goes_out_and_relight_costs_5` |
| Refuel `used = min(carried, ceil((100−fuel)/10))` | `test_refuel_formula`, `test_tiny_gap_refuel_uses_one_mote` |
| Wander shade drains a lantern with fuel < 30; `fuel_drain` every 60 ticks; 1/s + 5/s | `test_shade_drains_weak_lantern` |
| Safe zone kept at fuel ≥ 30 | `test_safe_zone_kept_at_exactly_30` |
| `drain` → `chase` when the player is within 6 m | `test_drain_to_chase_when_player_near` |
| Pulse on a draining shade = +15 | `test_pulse_on_draining_shade_scores_15` |
| Stun ends in `wander` | `test_stun_ends_in_wander` |
| No early win; `dawn_survived` at tick 0 of the timer with ≥ 60 % lit; dawn bonus | `test_no_early_win_and_dawn_survived`, `test_all_lit_does_not_end_night` |
| Below threshold at dawn → `dawn` | `test_dawn_below_threshold_loses` |
| Capacity 10 + 2 × lights, max 20 | `test_capacity_grows_with_lights` |
| Snapshot v1.2 fields | `test_snapshot_fields_v12` |

Tests changed by the new rules (none skipped):
- `test_phase2_features.test_score_on_deposit_not_pickup` now expects +5. Ticket-03 replaced the +10 per-mote score.

Full-night headless (seed 2): Night 1 in 1.28 s, Night 3 in 2.5 s. Two runs with the same seed give byte-identical output.

Design note: `docs/adr/0001-lantern-fuel-and-dawn-win.md`. Breaking changes: `CHANGELOG.md`.

## Web client
Checked at 1280×720 in the browser pane: the night timer starts at 04:00, the mote bar follows `capacity`, and there are no console errors. The fuel bar, the 1 Hz low-fuel blink and the colour-blind palette are in the code but were not checked on a lit lantern in this round.

## AI log
Estimated ~45k tokens. The patch was applied as a scripted rewrite of the affected methods, and the tests were written straight from the ticket tables. Only one existing test needed updating.
