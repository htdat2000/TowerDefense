# ROADMAP (single task list). Game first. Tick only when tested by the user.

## Done (art, frozen)
Phases 1-5: art direction, Grassland (47-tile autotiles, grid layers), 3 towers x 5 levels, 5 monsters x 4 directions, 36 VFX. Details: `docs/ASSET_CATALOG.md`.

## Already written in Godot, not yet run
Level builder, grid logic/render/placement, tower (build/idle/attack/upgrade/destroy), monster (4-dir, path, hit, death), projectile, status effects (freeze/slow/stun/burning/poison), damage numbers, crit, VFX library, boss spawn debug key.

## GAME milestones
### M0 First run (do first)
- [ ] Open in Godot, import, run `main.tscn`; fix every error/warning.
- [ ] Verify: map, grid toggle, towers build+idle, wave start, monster directions, tower aiming/firing, impacts, hit/death, F1-F6 debug keys.
- [ ] Seams/filtering check; record oddities in KNOWN_ISSUES.
- [ ] Smoke test documented (`godot --headless --path . --quit-after 600`).
### M1 Core loop (DONE, play-tested by user: no major bugs)
- [x] Autoload `game_state.gd` (gold, lives, wave, speed + signals).
- [x] `data/waves_grassland_01.json` + wave manager, next-wave button.
- [x] Reaching the end costs lives; kills give gold (data-driven); win/lose.
- [x] Tower cost, sell refund, upgrade cost per level (data).
- Done when a 10-wave level can be won or lost with correct gold/lives.
### M2 Towers (WRITTEN, waiting for the user's test: tick each box only after it works in Godot)
- [ ] Per-level stat tables in data (`towers.json` levels[]; placeholder formulas removed from `tower.gd`).
- [ ] Targeting modes first/last/strongest/closest (`targeting.gd`); selected-tower panel (range ring, stats, targeting, upgrade, sell with confirm).
- [ ] Stone splash, Frost slow/freeze (also splash), Archer single target (data-driven).
- [ ] 2x2 footprint support in placement code (data `footprint`; no 2x2 art yet, test by setting `"footprint": [2, 2]` on one tower).
### M3 Monsters
- [ ] armor in data (hp/speed/reward/lives_cost already in `monsters.json` since M1); Boar burst, Mushroom spore, Treant armor.
- [ ] Health bars finalised; per-monster status tint.
### M4 UI (Control + Theme)
- [ ] `theme.tres`, HUD (lives, gold, wave, pause, speed x1-3), bottom tower bar with costs/disabled state.
- [ ] Pause, victory, defeat, main menu, level select (1 level), settings.
- [ ] Responsive at 1280x768, 1920x1080, mobile aspect.
### M5 Feel
- [ ] Wave banner, gold pop, sell effect, screen shake, pooling; touch + keyboard shortcuts.
### M6 Content
- [ ] 2 more Grassland layouts (data only), stars, save/load, difficulty.
### M7 Ship
- [ ] Export presets (Windows/Web/Android), icon, performance pass, build instructions.

## Art requests (filled by GAME chats; only these get art now)
Format: `- [ ] asset | size/frames/fps | file name | where used | placeholder meanwhile`
- (none yet)
Known leftovers worth requesting when M4/M2 need them: tower ghost sprite, selection highlight, UI skin and icons, gold/lives HUD icons.

## Deferred art backlog (frozen until M2 is done and user approves)
- Towers 4-10: Fire, Lightning, Poison, Cannon, Nature, Arcane, Sniper (5 levels each).
- Monsters: 15 (Mountain, Beach, Volcanic) + bosses; missing roles: flying, ranged, boss.
- Environments: Mountain Highlands, Tropical Beach, Volcanic Wasteland; map-edge details, ambient effects.
- Phase 6 UI skin, Phase 8 validation checklist.
- Open decision: keep vector-cartoon look or move to hand-painted textures (decide before scaling content).
- Extension recipes: `tools/art/README.md`.

## State (paste into a new chat if one is cut off)
Date: 2026-11-22  Mode: GAME  Milestone: M2 written, not yet tested
Done: M1 core loop. M2 code written: per-level data tables, targeting.gd, splash in projectile.gd, tower panel + range ring, 2x2 footprint path, left click opens panel, sell needs two clicks, Esc/right click cancel. Next: user tests M2 (checklist in chat), report errors; then M0 leftovers (seams check, headless smoke test doc), then M3. Decisions: top-level damage/range_cells/cooldown/statuses in towers.json stay as Lv1 summary for the art tools; levels[] wins in game. Balance is placeholder. Delta merged: no
