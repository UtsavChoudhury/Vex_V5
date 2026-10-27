# Development Timeline

Reconstructed from VS Code window/extension logs, VS Code local file history, VEX extension device logs, GitHub Copilot and Claude Code session transcripts, and git history. Times are local (EEST until 25 Oct, EET after).

| Day | Approx time | What was done | Active windows |
|---|---|---|---|
| Tue 08 Sep 2026 | ~10 m | Created the VEXcode Python project and installed the SDK; tried to run/download with no brain connected | 19:02–19:13 |
| Wed 09 Sep 2026 | ~1 h 10 m | First session with the brain connected; downloaded and ran the starting program | 14:47–15:54 (robot connected) |
| Fri 11 Sep 2026 | ~5 m | Opened the project briefly; no edits | 15:31–15:36 |
| Fri 18 Sep 2026 | ~2 h | Wrote drive/turn helpers, autonomous test sequences and inverted-joystick driver control; tested distances and turns on the robot | 14:35–16:38 |
| Mon 21 Sep 2026 | ~1 h 10 m | Fixed motor directions, added a motor-identification diagnostic, speed scaling and acceleration limiting | 14:40–15:52 |
| Tue 22 Sep 2026 | ~2 h 40 m | Added arm/claw controls and speed modes; reworked drive geometry and turn accuracy; added AI Vision cone detection, split into modules, set up git | 11:03–12:14, 14:38–16:06 |
| Fri 25 Sep 2026 | ~1 h | Debugged AI Vision detecting nothing; added a port scanner and tried to view the camera feed | 15:31–16:32 |
| Thu 22 Oct 2026 | ~1 h 35 m | Fixed user-control vision/port bug, built slow colour-search autonomous with cone approach and micro-centring (Copilot), then tuned alignment (Claude) | 16:08–17:41 |
| Fri 23 Oct 2026 | ~2 h 05 m | Iterated the autonomous scan → align → approach loop; detection unreliable at range | 15:45–17:52 |
| Sun 25 Oct 2026 | ~10 m | Replaced AI autonomous with deterministic wall-square path; moved cone assist to driver buttons | 08:25–08:34 |
| Mon 26 Oct 2026 | ~30 m | Set up the GitHub repo; wrote development log and LaTeX report, removed chapters 7–9 | 10:05–10:11, 18:18–18:43 |
| Tue 27 Oct 2026 | ~10 m | Bumper-triggered wall-square (ports B/E) before the L path | 12:20–12:29 |

**Total:** ~12 h 45 m across 12 days.
