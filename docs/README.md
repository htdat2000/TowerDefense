# Tower Defense (Godot)

Open this folder in **Godot 4.3+** (developed against 4.7.x), wait for the import, press **F5**.

## Controls
Pick a tower (button shows its cost) -> hover (green = valid and affordable, red = not) -> left click to place. Left click a placed tower (with nothing picked) to open its panel: current and next-level stats, targeting mode (First / Last / Strongest / Closest), Upgrade (Lv1-5, costs gold) and Sell (click twice to confirm, refund from data). Right click or Esc cancels the picked tower or closes the panel. "Start wave N" sends the next wave; the level is won after wave 10 is cleared and lost when lives reach 0. "Speed" cycles x1/x2/x3. "Toggle grid" shows/hides the grid. Debug: F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun, F6 boss Treant.

## Build / export
Project > Export. Presets are not created yet (ROADMAP M7).

## Folders
`scripts/ scenes/ data/ assets/` = the game. `docs/` = documentation. `tools/art/` = Python art generators (not shipped).

## Working with Claude (one Claude Project, 3 knowledge files)
Knowledge: `CLAUDE.md`, `docs/ROADMAP.md`, `docs/ART_BIBLE.md`. Project instruction: see `docs/CLAUDE_PROJECT_INSTRUCTION.txt`.
Starter lines:
- `GAME mode. Milestone M2: I ran it in Godot 4.x and got: <exact error text + what I did>. Return a delta zip.`
- `GAME mode. Do milestone M3 from ROADMAP. List what I should test. Return a delta zip.`
- `ART mode. Art request: <line from ROADMAP>. Show one preview, wait for approval, then delta zip.`
After each chat: unzip the delta over this folder, `git commit`, run the game, report back.
If a chat is cut off, paste the "State" block at the bottom of `docs/ROADMAP.md` into the new chat.
