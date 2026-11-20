# Phase 2 acceptance criteria

| Area | Criterion | Verification |
|---|---|---|
| Contract | `game.contract.json` is v1.1 and exposes standard tuning | Parse JSON and compare constants |
| Nights | `--night 1`, `--night 2`, and `--night 3` initialize the correct duration and lantern layout | Headless snapshots |
| Movement | Running, jump, dash and cooldown use 60 Hz deterministic ticks | Scenario with input edge frames |
| Pause | Pause toggles state while `tick` advances and `sim_tick`, time and gameplay counters stay fixed | Pause scenario |
| Motes | Capacity 10, radius 1 m pickup, 240-tick refill, dropped TTL | Pickup and dropped-mote scenarios |
| Lanterns | Nearest eligible lantern receives up to 10 motes and becomes lit | Deposit scenario |
| Pulse | Costs 3, has 180-tick cooldown, stuns shades for 120 ticks and awards 5 points per shade per pulse | Pulse scenario |
| Shades | Required state names and scheduled spawning are emitted | Spawn scenario |
| Drifters | Night 2/3 drifters chase, steal, flee and emit steal/drop events | Drifter scenario |
| Charm | Charm pickup grants 600 ticks and respawns after 2700 ticks | Charm scenario |
| Wind | Night 3 emits deterministic wind state and applies movement drift | Wind-enabled scenario |
| End state | No flames always loses; all lanterns lit wins before dawn; dawn otherwise loses | End-state scenarios |

The browser preview remains visual-only; the headless simulation is authoritative for contract verification.
