# Tower Defense (Godot)

Open this folder in **Godot 4.3+** (developed against 4.7.x), wait for the import, press **F5**.

## How to play
You control a character. Monsters chase and attack it; if it dies the run ends. You get a prepare phase (30 s, no monsters), then waves keep coming on a timer, endless.
- **WASD / arrows**: move (water and trees stop you, towers do not).
- Pick a tower button (cost shown), hover a cell **inside the yellow ring** around the character (green = valid and affordable, red = not), left click to build. You cannot build under the character.
- Left click a placed tower (nothing picked): panel with stats, targeting (First / Last / Strongest / Closest), Upgrade (Lv1-5) and Sell (click twice, refund). Right click or Esc cancels or closes.
- Monsters cannot pass towers. If you wall yourself in, they attack the cheapest tower (one hit destroys it, no refund) until a route opens. Leave a gap and towers are safe.
- "Call next wave" skips the countdown. "Speed" cycles x1/x2/x3. "Toggle grid" shows/hides the grid.
- Debug: F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun, F6 boss Treant, 7 boar, 8 mushroom, 9 hit all.

## Smoke test (headless)
```
godot --headless --path . --import
godot --headless --path . --fixed-fps 60 -s res://scripts/smoke_test.gd
```
Checks data, assets, flow field logic, then plays the scene (build, wave, statuses, upgrades, panel, sell, tower destruction, character damage, defeat, restart). Exit code 0 = all passed. Manual list: `docs/M4_CHECKLIST.md`. Static (no Godot): `python3 tools/art/validate.py`.

## Build / export
Project > Export. Presets are not created yet (ROADMAP M8).

## Folders
`scripts/ scenes/ data/ assets/` = the game. `docs/` = documentation. `tools/art/` = Python art generators (not shipped).

## Working with Claude (one Claude Project, 3 knowledge files)
Knowledge: `CLAUDE.md`, `docs/ROADMAP.md`, `docs/ART_BIBLE.md`. Project instruction: see `docs/CLAUDE_PROJECT_INSTRUCTION.txt`.
Starter lines:
- `GAME mode. M4: I ran it in Godot 4.x and got: <exact error text + what I did>. Return a delta zip.`
- `GAME mode. Do milestone M5 from ROADMAP. List what I should test. Return a delta zip.`
- `ART mode. Art request: <line from ROADMAP>. Show one preview, wait for approval, then delta zip.`
After each chat: unzip the delta over this folder, `git commit`, run the game, report back.
If a chat is cut off, paste the "State" block at the bottom of `docs/ROADMAP.md` into the new chat.
