# ROADMAP (single task list). Game first. Tick only when tested by the user.

## Done (art, frozen)
Phases 1-5: art direction, Grassland (47-tile autotiles, grid layers), 3 towers x 5 levels, 5 monsters x 4 directions, 36 VFX. Details: `docs/ASSET_CATALOG.md`.

## Already written in Godot, not yet run
Level builder, grid logic/render/placement, tower (build/idle/attack/upgrade/destroy), monster (4-dir, path, hit, death), projectile, status effects (freeze/slow/stun/burning/poison), damage numbers, crit, VFX library, boss spawn debug key.

## GAME milestones
### M0 First run (do first)
- [ ] Open in Godot, import, run `main.tscn`; fix every error/warning.
- [ ] Verify: map, grid toggle, 3 towers build+idle, "Send wave", monster directions, tower aiming/firing, impacts, hit/death, F1-F6 debug keys.
- [ ] Seams/filtering check; record oddities in KNOWN_ISSUES.
- [ ] Smoke test documented (`godot --headless --path . --quit-after 600`).
### M1 Core loop
- [ ] Autoload `game_state.gd` (gold, lives, wave, speed + signals).
- [ ] `data/waves_grassland_01.json` + wave manager, next-wave button.
- [ ] Reaching the end costs lives; kills give gold (data-driven); win/lose.
- [ ] Tower cost, sell refund, upgrade cost per level (data).
- Done when a 10-wave level can be won or lost with correct gold/lives.
### M2 Towers
- [ ] Per-level stat tables in data (remove placeholder formulas in `tower.gd`).
- [ ] Targeting modes (first/last/strongest/closest); selected-tower panel (range ring, upgrade, sell).
- [ ] Stone splash, Frost slow/freeze, Archer single target (data-driven).
- [ ] 2x2 footprint support in placement code.
### M3 Monsters
- [ ] hp/speed/armor/reward/lives cost in data; Boar burst, Mushroom spore, Treant armor.
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
Known leftovers worth requesting when M4/M2 need them: tower ghost sprite, selection highlight, UI skin and icons.

## Deferred art backlog (frozen until M2 is done and user approves)
- Towers 4-10: Fire, Lightning, Poison, Cannon, Nature, Arcane, Sniper (5 levels each).
- Monsters: 15 (Mountain, Beach, Volcanic) + bosses; missing roles: flying, ranged, boss.
- Environments: Mountain Highlands, Tropical Beach, Volcanic Wasteland; map-edge details, ambient effects.
- Phase 6 UI skin, Phase 8 validation checklist.
- Open decision: keep vector-cartoon look or move to hand-painted textures (decide before scaling content).
- Extension recipes: `tools/art/README.md`.

## State (paste into a new chat if one is cut off)
Date: ____  Mode: GAME/ART  Milestone: ____
Done: ____  Not finished / next: ____  Decisions: ____  Delta merged: yes/no
