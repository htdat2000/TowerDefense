# ROADMAP (single task list). Game first. Tick only when tested by the user.

## Done (art, frozen)
Phases 1-5: art direction, Grassland (47-tile autotiles, grid layers), 3 towers x 5 levels, 5 monsters x 4 directions, 36 VFX. Details: `docs/ASSET_CATALOG.md`.

## GAME milestones
### M0 First run (DONE, user-verified 2026-11-24)
Smoke test 621 checks / 0 failed, headless import and run clean, validate.py 0 errors, manual checklist and seams check pass.
### M1 Core loop, M2 Towers (DONE, play-tested). Their gold/upgrade/sell/targeting/splash/status features are kept.
### M3 Monsters (WRITTEN 2026-11-24, NOT yet run) - armor, boar burst, mushroom spore heal, health bars, status tints. Kept inside M4 code.
### M4 Chase-and-survive refactor (WRITTEN 2026-11-25, NOT yet run or tested)
One refactor of the whole game to the new rules (`CLAUDE.md` "Gameplay rules"). Test list: `docs/M4_CHECKLIST.md`.
- [ ] Character: `player.gd`, WASD/arrows, collision (water + blocked only, towers walkable), hp, placeholder drawn sprite, hp bar, damage number. Data: `data/player.json`.
- [ ] Build radius: towers only inside the yellow ring around the character, never under it; ring follows the character; `build_on_path` option.
- [ ] Flow field: `flow_field.gd`, recomputed on character cell change and on tower place / sell / destroy. Data: `data/ai.json`.
- [ ] Monsters chase through the flow field, attack the character (`damage`, `attack_cooldown`, damage frame 4), `Targeting` first/last use route distance.
- [ ] Siege: no free route -> monster walks to the tower on its cheapest route, attacks, tower destroyed in one hit (no refund), field recomputed.
- [ ] Timed endless waves: prepare countdown, waves every `wave_interval`, no clear gating, endless generator + hp scaling, wave bonus on survival, "Call next wave" button.
- [ ] GameState without lives; defeat = character dead; score = waves reached.
- [ ] Smoke test rewritten (`smoke_checks.gd` flow-field unit tests, `smoke_test.gd` gameplay timeline).
- Debug keys changed: F1-F5 statuses, F6 boss, 7 boar, 8 mushroom, 9 hit all (WASD is movement now).
- Done when: the user plays a full run (prepare, waves, walling off, siege, defeat, restart) without errors.
### M5 UI (Control + Theme)
- [ ] `theme.tres`, HUD (character hp bar, gold, wave + countdown, pause, speed x1-3), bottom tower bar with costs/disabled state.
- [ ] Pause, defeat/result (score), main menu, settings. Responsive at 1280x768, 1920x1080, mobile aspect (virtual joystick decision).
### M6 Feel
- [ ] Wave banner, gold pop, screen shake, pooling, touch + keyboard shortcuts, character attack/build feedback, monster separation.
### M7 Content
- [ ] 2 more Grassland layouts (data only), save/load (best score), difficulty, character upgrades or abilities.
### M8 Ship
- [ ] Export presets (Windows/Web/Android), icon, performance pass, build instructions.

## Art requests (filled by GAME chats; only these get art now)
Format: `- [ ] asset | size/frames/fps | file name | where used | placeholder meanwhile`
- [ ] Player character | 64 or 80 px frame, 4 directions E,S,W,N; idle 6@8, walk 8@12, hit 4@12, death 10@12 (+ optional build 8@14) | `Characters/Hero/Strips/hero_<anim>_<dir>.png` + `hero_shadow.png` | `player.gd` | circle drawn in `_draw`
- Known leftovers worth requesting when M5 needs them: tower ghost sprite, selection highlight, UI skin and icons, HP/gold HUD icons, build-radius indicator art.

## Deferred art backlog (frozen until the user approves)
- Towers 4-10: Fire, Lightning, Poison, Cannon, Nature, Arcane, Sniper (5 levels each).
- Monsters: 15 (Mountain, Beach, Volcanic) + bosses; missing roles: flying, ranged, boss.
- Environments: Mountain Highlands, Tropical Beach, Volcanic Wasteland; map-edge details, ambient effects.
- Phase 6 UI skin, Phase 8 validation checklist.
- Open decision: keep vector-cartoon look or move to hand-painted textures (decide before scaling content).
- Extension recipes: `tools/art/README.md`.

## State (paste into a new chat if one is cut off)
Date: 2026-11-25  Mode: GAME  Milestone: M4 chase-and-survive refactor written, NOT run
Done: M0, M1, M2. M3 and M4 written in one refactor, never run in Godot (no Godot in chat).
Design: controllable character, monsters chase via flow field, prepare time then timed endless waves, towers walkable only by the player, towers no HP (one-hit destroyed when monsters are walled off), see CLAUDE.md.
Next: user runs the smoke test and `docs/M4_CHECKLIST.md`, reports exact errors; fix; then M5 UI (needs approval). Balance is placeholder. Delta merged: no
