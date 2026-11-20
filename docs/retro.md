# Retro — Đảo Đèn Lồng, Day 12 AI SDLC

## What the four phases looked like

| Phase | Outcome | Evidence |
|---|---|---|
| 1 · PRD-0 | Playable Night 1 and a deterministic headless runner following Contract v1.0 | `docs/proof/phase-1.md` |
| 2 · Ticket-02 | Three standard maps, dash, jump pads, ramps and cliffs, fall penalty, Gió Lạc, charms, wind, pause; web 3D client | `docs/proof/phase-2.md`, 24 tests |
| 3 · Ticket-03 | Lantern fuel, drain shades, dawn win rule, growing capacity, new scoring, colour-blind palette | `docs/proof/phase-3.md`, ADR 0001, CHANGELOG |
| 4 · Ticket-04 | Bench, soak, local leaderboard, key rebinding, captions, reduced motion, large text, release docs | `docs/proof/phase-4.md`, 45 tests |

## What worked with AI

- **One headless scenario test per ticket bullet.** Writing tests straight from the ticket tables turned "the agent says it works" into a yes or no answer. In Phase 3, only one old test had to change, and the reason is recorded in the test itself.
- **Keeping one authoritative simulation.** The 2D canvas, the Three.js client and the Ursina bench all render the same `Game` object. Each new rule landed once and showed up everywhere.
- **Branch → PR → merge → tag per phase.** This gave a clean history the grader can follow, and it made each phase's tag point at reviewed code.
- **Scripted patches instead of free-hand edits.** For the dense simulation file, each change was a small assert-guarded replace script. A wrong anchor failed loudly instead of silently editing the wrong line.

## Where AI got it wrong, and how it was caught

| Mistake | How it was caught | Fix |
|---|---|---|
| Night 3 shade speed flattened to 4.0, and the fall penalty disabled, because the contract template was trusted over the ticket text | Re-reading the whole ticket document line by line against the code | Followed the ticket and updated the contract. AGENTS.md now says "ticket text is the source of truth" |
| Motes scored twice (pickup and deposit); pulse knock-back stored but never applied; wind cycle 35 s/10 s | Same ticket re-read, then one scenario test per rule | Fixed, with tests |
| The isometric 2D preview moved the player diagonally for a single arrow key | The user noticed it in play | Switched to a straight top-down projection; all 4 directions checked with numbers and screenshots |
| A variable named `cap` shadowed the new caption function, and the poll loop reported the crash as "server unreachable" | The browser showed the wrong error; the console showed the real one after splitting the try/catch | Renamed the variable; network errors and render errors are now reported separately |
| The Night 3 start (0,0,0) is inside the bell tower, so Mây spawned on the 14 m tower top | Visual inspection of a screenshot | She stands on tier 2 (assumption documented in code), with tests |
| Bench numbers swung between 8 and 105 FPS | Repeated 30 s runs | The browser preview was competing for the GPU, and Windows throttles the window when it is not in the foreground |
| A paid third-party "OpenAI-compatible" endpoint was tried as an agent backend | The service refused non-whitelisted clients | Dropped it rather than spoof a client identity. The key was kept out of the repo and stored outside it |

## Harness that helped most

1. **AGENTS.md rules:**
   - Keep Ursina out of headless.
   - Run the tests after every simulation change.
   - The ticket is the source of truth.
   - One test per feature.
   - Branch and PR per phase.

   The rules added after a mistake (ticket over contract) stopped the same class of error in Phases 3 and 4.
2. **The browser pane with a launch config:** it gave real evidence (screenshots, console errors, live `/api/state` reads) instead of describing UI changes.
3. **A scratchpad for patch scripts and run outputs,** so experiments never landed in the repo by accident.

## Tokens and cost

| Phase | Estimated tokens |
|---|---|
| 1 | ~12k |
| 2 (including the first web client and fixes) | ~120k |
| 3 | ~45k |
| 4 | ~80k |
| **Total** | **~260k** |

What saved tokens:
- Reading the ticket once into one file instead of re-reading it in chat.
- Scripted patches instead of re-printing whole files.
- Running tests with `grep` on the summary lines only.
- Measuring the bench with short 4–5 s runs before 30 s ones.

What wasted tokens:
- Early UI polish before the rules were complete.
- Several Ursina window debugging rounds that a browser client made unnecessary.

## If I did it again

- Read the full ticket document before Phase 2, and keep a checklist file mapping each bullet to a test from the start.
- Choose the web client on day one instead of Ursina for play, and keep Ursina only for the bench.
- Write the bench early and run it on every phase, so the shadow-pass p1_low issue shows up while there is still time to fix it (lower shadow resolution or instanced shades).
- Record the demo video from the start of Phase 4, not at the end.
