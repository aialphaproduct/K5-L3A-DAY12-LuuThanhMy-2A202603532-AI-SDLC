# Agent notes
- Core simulation and headless mode must not import or initialize Ursina.
- Run `python3 -m unittest discover -s tests` after simulation changes.
- Preserve Contract v1.1 tick ordering, deterministic IDs, exact shade state names, and JSONL output.
- `--night 1|2|3` must use the standard map/tuning values documented in docs/spec/phase-2-acceptance.md.
- Keep dependencies and visual-only features out of the simulation contract.
