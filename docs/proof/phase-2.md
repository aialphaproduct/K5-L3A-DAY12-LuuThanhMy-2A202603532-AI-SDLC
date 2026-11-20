# Phase 2 evidence (Ticket-02, Contract v1.1)

Run: `python3 -m unittest discover -s tests` → 22 tests, all pass.

| Ticket-02 item | Evidence (test in `tests/`) |
|---|---|
| Standard tuning, nights 1–3 layouts, snapshot fields | `test_phase2_contract.test_night_layouts_and_snapshot_fields` |
| Dash event, pause freezes `sim_tick` | `test_phase2_contract.test_dash_event_and_pause_freezes_simulation` |
| Pause/resume events with `{}` data | `test_phase2_features.test_pause_events_have_empty_data` |
| `night_start {night}` at tick 1 | `test_night_start_event` |
| Score +10 per mote **deposited** (not on pickup) | `test_score_on_deposit_not_pickup` |
| Shade speed 4.0 m/s, Night 3 4.5 m/s | `test_night1_shade_speed_is_4`, `test_night3_shade_speed_is_4_5` |
| Fall off island: −1 flame, lose all motes, 60-tick wait, respawn at start with 90-tick invuln | `test_fall_penalty_and_respawn` |
| Fall on last flame loses immediately (`no_flames`) | `test_fall_with_last_flame_loses` |
| Night 2 jump pad (Y 14, 24 m/s) lands on the other island | `test_night2_jump_pad_lands_on_other_island` |
| Night 3 pad (Y 12, 8 m/s to −Z) lands on tier 2 (Y=6) | `test_night3_pad_reaches_tier2` |
| Night 3 ramps reach tier 1; tier edges are vertical cliffs | `test_night3_ramp_climbs_to_tier1`, `test_night3_cliff_blocks_walking_up` |
| Pulse pushes 4 m over 15 ticks; overlapping shade pushed along +X | `test_pulse_pushes_4m_and_overlap_pushes_plus_x` |
| Shade cap per night (6 / 8 / 10) and spawn interval (8 / 7 / 6 s) | `test_shade_cap_per_night` |
| Wind: 5 s gust every 30 s | `test_wind_cycle_30s_lasting_5s` |
| Gió Lạc steal min(3, carried); chase → idle when condition lost | `test_drifter_steal`, `test_drifter_returns_to_idle_when_condition_lost` |
| Bùa Gió pickup event | `test_charm_pickup` |

Full-night headless timing (21 600-tick budget, limit 30 s), measured on the dev laptop (Windows 11, Python 3.13):

| Night | Wall time |
|---|---|
| 1 | 1.01 s |
| 2 | 1.26 s |
| 3 | 1.84 s |

## Corrections made in this round

Re-reading Ticket-02 (not only the contract template) showed earlier drift that is now fixed:

- Night 3 shade speed had been set to 4.0 from the contract's single `shade_speed`; Ticket-02 says 4.5 on Night 3.
- Falling had been disabled from the old `fall_enabled: false`; Ticket-02 makes the fall penalty mandatory, so `fall_enabled` is now `true`.
- Motes were scored twice (pickup and deposit); Ticket-02 scores deposits only.
- Pulse knock-back was stored but never applied.
- Wind cycle was 35 s / 10 s instead of 30 s / 5 s.
- Shades were capped at 6 on every night.
- Jump pads, ramps and tier cliffs existed only in the 3D view, not in the simulation.

## AI log

Estimated usage for this round: ~60k tokens. Most of it went into reading the full ticket document and writing one scenario test per feature. The main error was trusting the contract template over the ticket text; AGENTS.md now says to check the ticket first.
