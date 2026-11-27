# M4 CHECKLIST: chase-and-survive refactor. Written, not run: you run it, then report.

## 1. Automated
```
godot --headless --path . --import
godot --headless --path . --fixed-fps 60 -s res://scripts/smoke_test.gd
godot --headless --path . --quit-after 600
python3 tools/art/validate.py
```
- Expect `== N checks passed, 0 failed ==`, exit code 0. Every `FAIL` line names the broken check.
- Look for `SCRIPT ERROR`, `Parser Error`, `ERROR:`, `WARNING:` in every command and paste them. `WARN no monster died` is only a balance hint.
- validate.py may still read old keys; paste any ERR line.

## 2. Manual run (F5, about 10 minutes) - tick what you saw
- [x] Start: HUD shows HP, Gold, Wave 0, "Prepare: 30 s". No monsters during prepare.
- [x] WASD and arrows move the character in 8 directions; it stops at water, trees, boulders, map edge; it walks over towers.
- [x] Pick a tower: yellow build ring around the character follows it; green cells only inside the ring; clicking outside says "Too far from the character"; the character cell is refused.
- [x] Towers build, idle, aim, fire; panel (click tower), upgrade, sell (two clicks, refund) still work.
- [x] "Call next wave" or the countdown starts wave 1; waves keep coming every 25 s without clearing; wave bonus message when the next wave starts.
- [x] Monsters walk in from the left edge, chase the moving character around towers (not along the old road only), face the right direction at corners.
- [x] Monsters stop next to the character, play the attack, the character loses HP with a red number, HP in the HUD drops, HP bar over the character.
- [ ] Wall the character in completely (towers + water/trees): monsters walk to a tower, attack it, it is destroyed in one hit with rubble, no gold back, then they pour through. Leave a gap: towers are never attacked.
- [x] Tower targeting "First" shoots the monster closest to the character.
- [x] Character dies: DEFEAT overlay with waves reached, Restart returns to a clean prepare phase.
- [x] Wave 11 onward (endless): more monsters, Treant every third wave, stronger hp. Speed x1/x2/x3 works.
- [x] Debug: F1-F5 statuses, F6 boss, 7 boar (burst), 8 mushroom (spores heal), 9 hit all.
- [ ] Armor numbers, boar burst, spore heal, health bars from M3 still behave.

## 3. Report back
Paste: smoke test output (or FAIL lines), engine ERROR/WARNING lines, which manual boxes failed, and how the balance feels (too easy / too hard, where).
