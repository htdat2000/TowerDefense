# ROADMAP (single task list). Game first. Tick only when tested by the user.

## Done (art, frozen)
Phases 1-5: art direction, Grassland (47-tile autotiles, grid layers), 3 towers x 5 levels, 5 monsters x 4 directions, 36 VFX. Details: `docs/ASSET_CATALOG.md`.

## Already written in Godot
Level builder, grid logic/render/placement, tower (build/idle/attack/upgrade/destroy), monster (4-dir, path, hit, death), projectile, status effects (freeze/slow/stun/burning/poison), damage numbers, crit, VFX library, boss spawn debug key. M1 and M2 features were play-tested by the user.

## GAME milestones
### M0 First run (DONE, user-verified 2026-11-24: automated checks, manual checklist and seams check all pass)
Run by user 2026-11-24: smoke test 621 checks / 0 failed, import and 600-frame headless run with no errors or warnings, validate.py 0 errors. Written: `scripts/smoke_test.gd` + `scripts/smoke_checks.gd` (headless data/asset/gameplay checks), `docs/M0_CHECKLIST.md` (commands, manual list, seams procedure).
- [x] Open in Godot, import, run `main.tscn`; fix every error/warning. (Headless import + run clean; prep fix: `damage_number.gd` `set_name` shadow warning.)
- [x] Verify: map, grid toggle, towers build+idle, wave start, monster directions, tower aiming/firing, impacts, hit/death, F1-F6 debug keys (list in `docs/M0_CHECKLIST.md` section 2).
- [x] Seams/filtering check; record oddities in KNOWN_ISSUES (procedure: checklist section 3).
- [x] Smoke test documented AND run: command in README, output reported (`godot --headless --path . --fixed-fps 60 -s res://scripts/smoke_test.gd`).
### M1 Core loop (DONE, play-tested by user: no major bugs)
- [x] Autoload `game_state.gd` (gold, lives, wave, speed + signals).
- [x] `data/waves_grassland_01.json` + wave manager, next-wave button.
- [x] Reaching the end costs lives; kills give gold (data-driven); win/lose.
- [x] Tower cost, sell refund, upgrade cost per level (data).
- Done when a 10-wave level can be won or lost with correct gold/lives.
### M2 Towers (DONE, play-tested by user: features work, no noticeable bugs)
- [x] Per-level stat tables in data (`towers.json` levels[]; placeholder formulas removed from `tower.gd`).
- [x] Targeting modes first/last/strongest/closest (`targeting.gd`); selected-tower panel (range ring, stats, targeting, upgrade, sell with confirm).
- [x] Stone splash, Frost slow/freeze (also splash), Archer single target (data-driven).
- [x] 2x2 footprint support in placement code (data `footprint`; no 2x2 art yet, test by setting `"footprint": [2, 2]` on one tower).
### M3 Monsters (WRITTEN 2026-11-24, NOT yet run or tested by the user)
- [ ] `armor` in `monsters.json` (0..0.9 fraction of direct damage removed; DoT ignores it). Treant 0.35, Boar 0.1. Damage numbers show the reduced value.
- [ ] Boar burst (`ability.kind = "burst"`): periodic speed burst with attack-anim telegraph and dust puff.
- [ ] Mushroom spore (`ability.kind = "spore"`): heals injured allies in radius by a fraction of max hp, shows green "+N" numbers.
- [ ] Treant armor (data only, shield icon on its health bar).
- [ ] Health bars finalised (`health_bar.gd`): drawn above all actors, colour by hp, shield icon for armored, always visible for bosses.
- [ ] Per-monster status tint (`status_tint_strength`, `status_tints` in data).
- Debug keys added: F7 boar, Q mushroom, W hit all for 10. Test list: see the M3 hand-off message.
- Done when: the user plays waves 5-10 and the abilities, armor and bars behave as described.
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
- (none yet) M3 reuses existing VFX: `enemy_spawn_particles` (boar dust) and `poison_splash` (spores), both tinted in data.
Known leftovers worth requesting when M4/M2 need them: tower ghost sprite, selection highlight, UI skin and icons, gold/lives HUD icons.

## Deferred art backlog (frozen until M2 is done and user approves)
- Towers 4-10: Fire, Lightning, Poison, Cannon, Nature, Arcane, Sniper (5 levels each).
- Monsters: 15 (Mountain, Beach, Volcanic) + bosses; missing roles: flying, ranged, boss.
- Environments: Mountain Highlands, Tropical Beach, Volcanic Wasteland; map-edge details, ambient effects.
- Phase 6 UI skin, Phase 8 validation checklist.
- Open decision: keep vector-cartoon look or move to hand-painted textures (decide before scaling content).
- Extension recipes: `tools/art/README.md`.

## State (paste into a new chat if one is cut off)
Date: 2026-11-24  Mode: GAME  Milestone: M3 written, untested
Done: M0 (smoke 621/0, manual checklist and seams pass), M1, M2. M3 written (armor, boar burst, mushroom spore heal, treant armor, health bar script, per-monster status tint, debug keys F7, Q, W); NOT run in Godot. Next: user tests M3 and reports; re-run the smoke test (it may need updating if it assumes undamped monster damage); then M4 UI (needs user approval). Decisions: top-level damage/range_cells/cooldown/statuses in towers.json stay as Lv1 summary for the art tools; levels[] wins in game. Balance is placeholder. Delta merged: no
