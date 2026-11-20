# Credits

## Characters, story and rules
Đảo Đèn Lồng, Mây, Ông Đăng, Bóng Mực and Gió Lạc are the original lab world from the Day 12 AI SDLC brief (PRD-0, Ticket-02 to Ticket-04).

## Code libraries
| Library | Use | License |
|---|---|---|
| [three.js](https://threejs.org) r160 (loaded from unpkg) | Web 3D rendering | MIT |
| [Ursina](https://www.ursinaengine.org) 7 | Native client and benchmark window | MIT |
| [Panda3D](https://www.panda3d.org) 1.10 (Ursina dependency) | Native renderer | Modified BSD |
| Python standard library | Simulation, server, soak, leaderboard | PSF |

## Fonts
| Font | Use | License |
|---|---|---|
| Be Vietnam Pro (Google Fonts) | UI text | SIL Open Font License 1.1 |
| Lora (Google Fonts) | Titles and quotes | SIL Open Font License 1.1 |

## Art and sound
- All 3D models are built in code from primitive shapes (cylinders, spheres, cones, boxes). No external model files are used.
- All sound effects and the night ambience are synthesized at runtime with the WebAudio API. No audio files are used.
- Icons (flames, arrows) are inline SVG written for this project.

## AI tools
- **Claude (Anthropic) via Claude Code:** used for implementation, tests, documentation and refactoring throughout all four phases. Every change was reviewed, run and verified with headless tests and browser checks. The prompts, decisions and mistakes are recorded in `docs/proof/` and `docs/retro.md`.
- No AI-generated images or audio are included.
