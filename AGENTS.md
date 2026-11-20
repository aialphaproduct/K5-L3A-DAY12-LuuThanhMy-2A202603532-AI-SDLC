# Agent notes
- Core simulation and headless mode must not import or initialize Ursina.
- Run `python -m unittest discover -s tests` after simulation changes.
- Preserve Test Contract tick ordering, deterministic IDs, and JSONL output.
- Keep dependencies and visual-only features out of the simulation contract.
