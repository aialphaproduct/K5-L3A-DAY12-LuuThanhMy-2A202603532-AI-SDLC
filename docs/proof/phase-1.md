# Phase 1 evidence

The contract runner is deterministic and emits the required initial snapshot and final `end` record. The automated checks in `tests/test_contract.py` verify deterministic replay and mote pickup. Run:

```bash
python3 -m unittest discover -s tests
python3 main.py --headless --seed 1 --night 1 --ticks 120 --out proof.jsonl
```

Assumptions: the five lanterns each require 5 motes; the interact action deposits all carried motes up to the remaining cost; a pulse consumes one carried mote. Fall damage is disabled in Phase 1. Visual play uses a simple warm-night prototype scene; the headless simulation is the authoritative contract.

## AI log

Phase 1 used a small implementation prompt and local verification. Estimated usage: 12k tokens. Savings came from separating deterministic simulation from optional rendering and testing the contract before polishing visuals.
