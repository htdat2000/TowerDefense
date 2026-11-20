# GAME TASKS - from art prototype to playable game
Work top to bottom. Tick boxes when done AND verified (smoke test + manual notes). Anything needing new art goes to `ART_REQUESTS.md`.

## M0 - First run (must pass before anything else)
- [ ] Open in Godot 4.3+, import assets, run `main.tscn`. Fix every script error/warning.
- [ ] Confirm: map renders (grass, autotiled path + ponds, trees), grid lines show/hide, 3 pre-placed towers build and idle, "Send wave" spawns 5 monsters that walk the path in the right directions, towers rotate/fire, projectiles + impacts play, monsters take hit and die.
- [ ] Fix tile seams / texture filtering if visible. Record anything odd in `KNOWN_ISSUES.md`.
- [ ] Add a headless smoke-test script (`tests/smoke_test.gd` or CLI command documented in README).
**Done when:** smoke test prints no errors and the manual checks above are confirmed by the user.

## M1 - Core game loop
- [ ] Autoload `game_state.gd`: gold, lives, wave number, game speed, signals (`gold_changed`, `lives_changed`, `wave_changed`, `game_over`, `victory`).
- [ ] Wave data (`data/waves_grassland_01.json`): list of waves -> monster id, count, spawn interval, delay. Wave manager spawns them; "Next wave" button + optional auto start.
- [ ] Monsters that reach the end cost lives (data-driven); kills give gold (data-driven); win = all waves cleared; lose = lives 0.
- [ ] Tower costs and sell refunds from data; placement requires enough gold; upgrade costs per level (Lv1-5).
**Done when:** a full 10-wave level can be won or lost with correct gold/lives.

## M2 - Towers (real gameplay)
- [ ] Per-level stats table per tower in data (damage, range, cooldown, projectile speed); remove placeholder formulas.
- [ ] Range via `Area2D`/distance, targeting modes (first / last / strongest / closest) with a UI toggle.
- [ ] Frost: slow/freeze effect; Stone: splash damage (small radius); Archer: fast single target. Data-driven.
- [ ] Selecting a placed tower shows range ring + selected-tower panel (stats, upgrade, sell).
- [ ] Support 2x2 footprints in placement code (even if no 2x2 tower exists yet).

## M3 - Monsters
- [ ] Stats in data: hp, speed, armor, reward, lives cost.
- [ ] Behaviours: Boar speed burst, Mushroom spore (area slow/damage to towers' fire rate or healing aura - pick simple, data-driven), Treant high hp/armor. Use existing attack animations where they make sense.
- [ ] Status effects on monsters (slow, freeze, burn, poison) with tint shader / modulate until overlay art exists; health bars finalised.

## M4 - UI / UX (Control scenes + Theme)
- [ ] `theme.tres` (placeholder StyleBoxFlat now, textured later). HUD: lives, gold, wave, pause, speed x1/x2/x3, next-wave button.
- [ ] Bottom tower bar with icons (placeholder = tower head sprite), cost, disabled state when too poor.
- [ ] Selected-tower panel, enemy info panel (name, hp, role), pause menu, victory + defeat screens (restart / menu).
- [ ] Main menu and simple level select (1 real level; others locked placeholders). Settings with volume sliders (audio buses created, no sounds required).
- [ ] Responsive layout (anchors/containers); works at 1280x768 and 1920x1080 and a mobile-like aspect.
**Art needed:** real UI skin, icons, buttons -> add to `ART_REQUESTS.md`.

## M5 - Feel and polish
- [ ] Damage numbers, gold pop, tower build/upgrade effect (existing tween; swap for art when available), sell effect, wave banner.
- [ ] Screen shake on life loss, hit flash, pooling for projectiles/VFX.
- [ ] Input: mouse + touch; keyboard shortcuts (1-3 towers, Space next wave, Esc pause).

## M6 - Content and progression
- [ ] Second and third Grassland layouts (data-only: map JSON + path) using the same tileset; level select unlocks.
- [ ] Star rating per level, save/load (`user://save.json`), settings persistence.
- [ ] Difficulty variants (lives, gold, wave scaling).

## M7 - Ship
- [ ] Export presets (Windows, Web, Android) + icon + app name; test export on the user's platform.
- [ ] Performance pass (draw calls, node counts), final README, build instructions.

## Blocked on new art (see backlog in the art project)
Remaining 7 towers, 15 monsters, bosses, 3 more environments, Phase 5 VFX (fireball, lightning, poison, status effects, upgrade effect, damage numbers), full UI skin. When new assets arrive, run the exporter (`04_SOURCE_SCRIPTS/export_godot_project.py`), then integrate by data entry first, code second.
