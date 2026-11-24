# M0 CHECKLIST (first-run verification). Written, not run: you run it, then report.

## 1. Automated (about 1 minute)
```
godot --headless --path . --import
godot --headless --path . --fixed-fps 60 -s res://scripts/smoke_test.gd
godot --headless --path . --quit-after 600
python3 tools/art/validate.py
```
- Smoke test: expect `== N checks passed, 0 failed ==` and exit code 0. Every `FAIL` line names the broken file/key.
- Also look in the output of every command for `SCRIPT ERROR`, `Parser Error`, `ERROR:`, `WARNING:`. Paste them to the next chat.
- A `WARN no monster died` line is not a failure (balance/range hint only).
- If `-s` complains that `GameState` is missing, tell me the exact message (autoload timing for script main loops).

## 2. Manual run (F5, about 5 minutes) - tick what you saw
- [ ] Map: ground, water, path blend with no gaps; trees/boulders/fence/lilypads placed.
- [ ] "Toggle grid" shows/hides lines; towers still place with the grid hidden.
- [ ] Each tower type: ghost + range ring, green/red cell, builds, idles (archer head sweeps, frost twinkles).
- [ ] Wave start: all 5 monster types walk with correct facing at every corner (E/S/W/N); feet do not slide.
- [ ] Towers aim, fire at the animation event frame; projectiles hit; impact VFX; damage numbers; crits.
- [ ] Monsters: hit flash, death animation, no leftover sprites.
- [ ] F1 freeze, F2 slow, F3 burning, F4 poison, F5 stun overlays + tint; F6 boss Treant + appearance VFX.
- [ ] Speed x1/x2/x3, win overlay, defeat overlay, Restart returns to a clean state.

## 3. Seams / filtering check
1. Run at the default window, then drag-resize to non-integer scales (for example 1100x660, 1500x900, a tall narrow window).
2. Look for 1 px hairlines between ground tiles, along path/water edges and around object shadows.
3. Result goes to KNOWN_ISSUES. If seams show, say at which size; likely fixes (to be done in a GAME chat, not yet applied):
   integer stretch scale (`display/window/stretch/scale_mode="integer"`), pixel snapping of 2D transforms, or extruded atlas padding (ART task).

## 4. Report back
Paste: smoke test output (or the FAIL lines), engine ERROR/WARNING lines, which manual boxes failed, seam result.
Then I tick M0 in ROADMAP and fix what failed.
