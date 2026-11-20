# Agent notes
- Core simulation and headless mode must not import or initialize Ursina.
- Run `python3 -m unittest discover -s tests` after simulation changes.
- Preserve Contract v1.1 tick ordering, deterministic IDs, exact shade state names, and JSONL output.
- `--night 1|2|3` must use the standard map/tuning values documented in docs/spec/phase-2-acceptance.md.
- Keep dependencies and visual-only features out of the simulation contract.
- The ticket text is the source of truth for numbers; the contract `tuning` block only declares them. When they disagree (e.g. Night 3 shade speed 4.5, fall penalty), follow the ticket and update the contract.
- Every new ticket feature gets at least one headless scenario test in `tests/`.
- Work on a feature branch per phase and merge to `main` through a PR; tag the phase on the merge commit.
