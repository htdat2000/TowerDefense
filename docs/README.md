# Tower Defense (Godot)

Open this folder in **Godot 4.3+** (developed against 4.7.x), wait for the import, press **F5**.

## Controls
Pick a tower -> hover (green valid, red invalid) -> left click to place. Left click a tower with nothing selected to upgrade (Lv1-5). Right click cancels. "Send wave" spawns 5 monsters. "Toggle grid" shows/hides the grid. Debug: F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun, F6 boss Treant.

## Build / export
Project > Export. Presets are not created yet (ROADMAP M7).

## Folders
`scripts/ scenes/ data/ assets/` = the game. `docs/` = documentation. `tools/art/` = Python art generators (not shipped).

## Working with Claude (one Claude Project, 3 knowledge files)
Knowledge: `CLAUDE.md`, `docs/ROADMAP.md`, `docs/ART_BIBLE.md`. Project instruction: see `docs/CLAUDE_PROJECT_INSTRUCTION.txt`.
Starter lines:
- `GAME mode. Milestone M0: I ran it in Godot 4.x and got: <exact error text + what I did>. Return a delta zip.`
- `GAME mode. Do milestone M1 from ROADMAP. List what I should test. Return a delta zip.`
- `ART mode. Art request: <line from ROADMAP>. Show one preview, wait for approval, then delta zip.`
After each chat: unzip the delta over this folder, `git commit`, run the game, report back.
If a chat is cut off, paste the "State" block at the bottom of `docs/ROADMAP.md` into the new chat.
