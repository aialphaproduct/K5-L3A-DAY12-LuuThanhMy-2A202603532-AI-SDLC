# Changelog

## Phase 4 — "Bình minh: v1.0.0" (Ticket-04, Contract v1.3)
- `python3 main.py --bench`: the standard 1280×720 scene (200 wander shades, 100 motes, L1–L3 lit, orbiting camera), with vsync off. It writes `bench.json` with avg/p1-low FPS, p95 frame time, load time and peak RSS.
- `python3 main.py --soak`: N headless nights in one process with seeded random input. It writes `soak.json` (crashes, results, RSS at start and end).
- Local top-10 leaderboard saved on disk. It has a menu screen, name entry after Bình Minh or a loss, and `--export-leaderboard`.
- Accessibility:
  - Rebind every action, with duplicate-key warning and restore defaults.
  - Captions with an edge arrow for shade spawns, wind, the last 10 s and lantern oil.
  - Reduced motion.
  - UI text at least 18 px, plus a large-text option.
- `python3 main.py` now opens the web 3D game. The Ursina client moved to `--native`.
- Fixes:
  - Night 3 start inside the bell tower.
  - Camera sliding over Mây.
  - HUD crash from a shadowed `cap` variable.
- README rewrite, CREDITS, LICENSE (MIT), Dockerfile, retro, `docs/proof/phase-4.md`.

## Phase 3 — "Đèn cạn dầu" (Ticket-03, Contract v1.2)

### Breaking changes
- **Win rule:** the night no longer ends when every lantern is lit. The player wins with `dawn_survived` if, at dawn, at least `ceil(0.6 × lanterns)` are lit (3/5, 4/6, 5/7). `all_lit` is no longer emitted.
- **Night length** is now 240 / 270 / 300 s (was 300 / 330 / 360).
- **Scoring:**
  - +5 per mote deposited, for lighting, relighting or refuelling (was +10).
  - +100 for a first light, +40 for a relight.
  - Pulse scores +5 per shade, or +15 if the shade was draining.
  - At dawn on a win: +50 + floor(fuel) per lit lantern, and +50 per flame left.
  - The time bonus is removed.
- **Lanterns:** a lit lantern burns fuel (100 max, −1/s) and goes out at 0 (`lantern_out`). Relighting costs 5 motes. Interact on a lit lantern refuels it (`refuel`).
- **Safe zone:** it is lost when fuel < 30.
- **Shades:**
  - New `drain` state: a shade drains a weak lantern at 5 fuel/s.
  - When a stun ends, the shade returns to `wander` (was `chase`).
  - In `wander`, shades walk toward lanterns.
- **Snapshot / scenario / events:**
  - Lanterns gain `fuel`, `ever_lit` and `relit_count`. The player gains `capacity`.
  - Scenario accepts `lanterns[].fuel/ever_lit`, `player.successful_lights` and `shades[].target_lantern_id`.
  - New events: `refuel`, `lantern_out`, `fuel_drain`. `lantern_lit` now carries `relight`.

### Added
- Carry capacity grows by 2 per successful light, up to 20.
- Colour-blind palette setting: shade rim and eyes in `#00B3FF`, white UI warnings with ⚠. Unlit lanterns sag 20 % and show a tear. Low-fuel lanterns blink.
- Fuel bar above lit lanterns in the web client.
- `docs/adr/0001-lantern-fuel-and-dawn-win.md` and 15 new headless tests (`tests/test_phase3_fuel.py`).

## Phase 2 — "Ba hòn đảo" (Ticket-02, Contract v1.1)
- Three nights with the standard maps (Đảo Bến, Đảo Cau, Đảo Chuông).
- Standard tuning: dash, jump pads, ramps and tier cliffs, and the fall penalty.
- Gió Lạc, Bùa Gió, wind gusts, pause, and the `night_start` event.
- Score is counted only when motes are deposited. Night 3 shades move at 4.5 m/s. Shades per night are capped at 6 / 8 / 10.
- Web 3D client (Three.js) driven by the Python simulation. It has a menu, night intros, the Ticket-02 HUD, a pause menu, settings and sound.
- 2D canvas preview at `/2d`.

## Phase 1 — PRD-0 (Contract v1.0)
- Playable Night 1 with a deterministic headless runner that follows Test Contract v1.0.
