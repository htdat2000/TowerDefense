# How to let Claude Code build the game on your computer

Claude Code is an agentic coding tool: it reads your project folder, edits files and runs commands (like running Godot) in a loop. It asks permission by default. "Fully automatic in one go" is not recommended: work milestone by milestone, and you test the game between milestones.

## 1. One-time setup
1. Install **Godot 4.3 or newer** (standard, not .NET). Make sure you can run it from a terminal (`godot --version`; on some systems the command is `godot4`, or you use the full path to the app).
2. Install **Claude Code** (needs a paid Claude plan or API account). From Anthropic's setup docs:
   - macOS / Linux / WSL: `curl -fsSL https://claude.ai/install.sh | bash`
   - Homebrew: `brew install --cask claude-code`   - Windows (WinGet): `winget install Anthropic.ClaudeCode`
   - Or install the desktop app and use its Code tab. Details: https://code.claude.com/docs
3. Unzip `TowerDefense_Godot_Project.zip` somewhere you control, e.g. `~/games/td`. Turn it into a git repo (Claude Code can then checkpoint/undo safely):
   `cd ~/games/td/TowerDefense_Godot_Project && git init && git add -A && git commit -m "start"`
4. Optional but recommended: keep the full package (`TowerDefense_Project`) next to it so the Python art scripts and docs are available.

## 2. Start a session
```
cd ~/games/td/TowerDefense_Godot_Project
claude
```
`CLAUDE.md` in this folder is read automatically (it holds the rules, verification commands and working agreement). Do NOT run /init (it would overwrite the idea of the provided file).

## 3. Recommended loop (per milestone)
1. **Plan first.** Start with `claude --permission-mode plan` (or press Shift+Tab to cycle modes). Prompt:
   > Read CLAUDE.md and GAME_TASKS.md. Do milestone M0. Show me a plan first.
2. Review the plan. Approve it, choosing "auto-accept edits" so it can edit files without asking each time (acceptEdits mode). Keep command approval on, approving `godot ...` and `git` commands as they come (you can add them to the allow list via `/permissions`).
3. Claude Code edits, runs the Godot smoke test, reads errors, fixes, repeats. It commits when green.
4. **You run the game (F5 in Godot)** and report what looks or feels wrong, in plain words. Paste into the session. Headless runs cannot judge visuals.
5. Next: `Do milestone M1.` and so on. Use `/rewind` or `git` to undo a bad step.

## 4. Starter prompts
- First run: `Read CLAUDE.md and GAME_TASKS.md. Do M0: import, run the headless smoke test, fix every error, then tell me exactly what to check by hand.`
- Next milestones: `Do M1 (core game loop). Plan first, implement, run the smoke test, then tell me what to test manually.`
- Bugs: `Here is the Godot error: <paste>. Fix it and re-run the smoke test.`
- Art gaps: `List everything you needed but did not have in ART_REQUESTS.md.` Take that list back to the art project chat.

## 5. Hands-off runs (optional, advanced)
Claude Code can run non-interactively: `claude -p "Do milestone M1 and stop" --permission-mode acceptEdits`. The same `--permission-mode` flag works with `-p`. Cap what it may do with `/permissions` or a project `.claude/settings.json`. Higher-autonomy modes (auto, bypassPermissions) exist; auto mode availability depends on your plan, and bypassPermissions should only be used in a sandbox/VM or a throwaway repo. For this project `acceptEdits` + git checkpoints is the sensible limit.

## 6. What it can and cannot do
- Can: write GDScript/scenes/data, run Godot headless, read errors, fix, refactor, write tests, update docs, use git.
- Cannot judge looks/feel without you, and cannot create new art (sprites, UI skins, effects). New art comes from the art Project chat; then run `04_SOURCE_SCRIPTS/export_godot_project.py` and tell Claude Code to integrate it.
- Quality of the result depends on your feedback each milestone. Expect several rounds.

## 7. Two-project workflow
Art chat (claude.ai Project): generates and reviews assets, exports to `05_GODOT_PROJECT/assets` + data. Code session (Claude Code): builds the game with those assets, logs missing art in `ART_REQUESTS.md`. Alternate between them.
