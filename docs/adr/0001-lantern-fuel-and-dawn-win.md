# ADR 0001: Lantern fuel state and the dawn win rule

Status: accepted (Phase 3, Ticket-03, Contract v1.2)

## Context

Up to Phase 2 a lantern had two states, unlit and lit, and the night ended as soon as every lantern was lit. Playtests showed strong players finished in about two minutes with nothing left to do. Ticket-03 changes the goal to "keep the island lit until dawn" and replaces three rules: lit lanterns can now go out, shades can enter a weak lantern's safe zone, and lighting all lanterns no longer ends the night.

## Decision

**Lantern state.** Each lantern now carries `lit`, `fu` (fuel), `ever_lit`, `relit_count` and `deposited`.
- Fuel is stored as an integer in 1/60 units (`fu`, 0–6000), so 1.0/s decay is exactly 1 unit per tick and drain is 5 units per tick per draining shade. Fuel is only converted to a float (one decimal) in the snapshot. This avoids float drift between runs.
- Light or relight sets `fu = 6000`. Each tick, during the counter step, fuel drops by `1 + 5 × draining shades`. Straight after that, any lantern at `fu ≤ 0` goes out: `lit = false`, `deposited = 0`, `lantern_out` is emitted, and `ever_lit` stays true.
- Relighting costs 5 motes if `ever_lit` is true, otherwise 10.
- Interact picks the nearest lantern that can receive, ties going to the lower id. A lantern can receive if it is unlit, or lit but not full. On a lit lantern, interact refuels with `used = min(carried, ceil((100 − fuel)/10))`.

**Safe zone.** The zone exists only while `fu ≥ 1800` (fuel 30). At exactly 30 the zone is kept.

**Shade states.** A `drain` state is added next to `spawning / wander / chase / recoil / stunned`.
- `wander` targets the nearest lit lantern with fuel < 30, or else the nearest unlit lantern, and walks toward it.
- Within 2 m of a weak target the shade switches to `drain` and stands still.
- `drain` leaves for `chase` when the player is within 6 m. It leaves for `wander` when the lantern goes out, is refuelled to ≥ 30, or the shade is more than 2 m away. Pulse stuns it as usual.
- Stun now always ends in `wander`. In Phase 2 it ended in `chase`.

**Win rule.** Win and loss are checked only after every other update in the tick.
- `no_flames` always loses first.
- When the timer reaches 0, the player wins with `dawn_survived` if lit lanterns ≥ `ceil(0.6 × total)`; otherwise they lose with `dawn`.
- `all_lit` is no longer emitted.

**Capacity.** `capacity = min(20, 10 + 2 × successful_lights)`. Relights count. Lanterns set lit by a scenario do not count.

## Consequences

- **Removed behaviour.** All tests that relied on an early `all_lit` win or on Phase 2 scores were updated:
  - `test_score_on_deposit_not_pickup` now expects +5 per mote, with the reason noted in the test.
  - No tests were skipped.
- **Interact order.** Fuel decays (step 2) before interact (step 5). A lantern set to fuel 100 is therefore never "full" when E is pressed: it is at 99.98 and takes 1 mote. This follows the ticket's tick order, and `test_tiny_gap_refuel_uses_one_mote` documents it.
- **Shade behaviour.** Shades now always move in `wander` (toward lanterns) instead of standing still, so the map feels more alive and lanterns attract danger.
- **Web client.** The Three.js client got a fuel bar that blinks at 1 Hz below 30, a hidden safe-zone ring when fuel < 30, a refuel prompt, capacity-sized mote slots, and a colour-blind palette setting.
