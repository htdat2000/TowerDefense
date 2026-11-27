# ARCHITECTURE
Godot 4.3+ (dev 4.7.x), GL Compatibility, 1280x768, `canvas_items`, keep aspect. Linear texture filter by default; the three tile layers use Nearest. PNGs import lossless, no mipmaps.
Status: everything below is written; M0-M2 were run by the user, M3 and the M4 refactor are not yet run.

## Gameplay model
- One controllable character (`player.gd`). Monsters chase it; its death ends the run. Only the character and monsters have HP. Towers have none.
- Prepare phase (no monsters), then timed continuous waves until defeat. Endless generator after the listed waves.
- The player builds anywhere buildable within `build_radius_cells` of the character (not under it), also during waves.
- Solidity: monsters are blocked by water, blocked cells and towers (`grid.walkable`, occupancy); the player only by water and blocked cells (`grid.is_solid_for_player`).
- Pathing: 4-direction flow field (`flow_field.gd`) on the 64 px grid, source = character cell, owned by `level.gd` (`level.flow`). Step cost = cost of the entered cell: free = `free_cost`, tower = `tower_cost` (data/ai.json, very high), so towers are only crossed when no free route exists. Recomputed by `level.refresh_flow(cell)` when the character changes cell and when a tower is placed, sold or destroyed.
- Monsters ask `flow.next_cell(cell)` every frame and walk to that cell centre. If the next cell holds a tower they stop within `tower_range` px, play the attack and at frame 4 emit `attacked_tower`; `main._destroy_tower` frees the cell at once, calls `tower.destroy()`, recomputes the field. No refund.
- A monster within `attack_range` px of the character stops, attacks, and at frame 4 emits `attacked_player`; `main` calls `player.take_damage`.
- `Targeting` first/last use `monster.path_left` (route distance to the character in px).
- The old `enemy_path` of `map_grassland_01.json` only gives the monster entry (`level.entry_cell`, `level.spawn_point`, one cell outside the map) and the decals.

## Scene / layer stack (`level.gd`, bottom to top by z_index)
Ground 0, Water 1, Path 2 (TileMapLayer) | Shadows 3, Decals 3, SmallDecor 4, Objects 5 (y-sort) | Grid 10 | Placement 11 | Actors 20 (towers, monsters, player, y-sort) | Projectiles 25 | Vfx 30 | UI (CanvasLayer, includes the tower panel) | Result overlay (CanvasLayer 10, always processing).
Grid lines are never baked into tiles. Hiding the grid or changing placement state never touches tile layers.
Health bars are children (z_index 2 relative) so they draw above every actor and below projectiles. The player uses the same `health_bar.gd`, always visible.

## Autoloads
| Name | Script | Role |
|---|---|---|
| `GameState` | `game_state.gd` | gold, wave (= score), speed (sets `Engine.time_scale`), `finished`; signals `gold_changed`, `wave_changed(wave)`, `speed_changed`, `game_over(wave_reached)`. `reset(start_gold)` is called by `main.gd`. `defeat()` ends the run. No lives. Connect with methods, never lambdas. |

## Scripts
| Script | Role |
|---|---|
| `main.gd` | controller: UI, tower panel, placement (build radius), economy, selling, tower destruction, monster spawning, defeat overlay, per-frame targeting, HUD timer |
| `player.gd` | character: WASD/arrows, collision, hp, build radius, drawn placeholder; emits `hp_changed`, `cell_changed`, `damaged`, `died` |
| `flow_field.gd` | Dijkstra over the grid from the character cell; `dist_at`, `reachable`, `next_cell` |
| `wave_manager.gd` | `data/waves_*.json`: prepare countdown, timed waves, endless generator, wave bonus; emits `spawn_requested(id, hp_mult, boss)`, `wave_started`, `wave_bonus`; `call_next_wave()`, `in_prep()`, `time_to_next()` |
| `level.gd` | builds layers, tileset, autotiling, decor; owns `grid`, `flow`, `ai`, `player_cfg`, `entry_cell`, `spawn_point`; `refresh_flow`, `available_cells(center, radius_px, exclude)` |
| `grid_manager.gd` | grid LOGIC only: types, occupancy, `walkable`, `is_solid_for_player`, `build_types`, `can_place` |
| `grid_renderer.gd`, `placement_layer.gd` | grid lines; build ring, available/occupied/selected/invalid overlays, ghost, range ring, selected placed tower |
| `tower.gd` | base + head + shadow; build/idle/attack/upgrade/destroy; stats from data; prices; `targeting`; `destroy()` is safe at any time; emits `fired`, `vfx_requested`, `state_changed`, `destroyed_done` |
| `targeting.gd` | static `Targeting.pick(mode, pos, range_px, monsters)`; first / last / strongest / closest |
| `monster.gd` | 4-dir animation, flow-field chase, attacks (character, blocking tower), hit/death, status effects, armor, abilities (burst, spore), health bar; emits `damaged`, `healed`, `died`, `attacked_player`, `attacked_tower`, `vfx_requested` |
| `health_bar.gd` | floating hp bar: hidden at full hp (bosses and the player always shown), colour by hp, shield icon when armored |
| `projectile.gd`, `vfx_one_shot.gd`, `vfx_library.gd`, `damage_number.gd` | projectiles (damage, statuses, splash), impacts, VFX helper, floating numbers (normal / crit / heal; crit style also used for damage taken by the character) |
| `sprite_frames_builder.gd`, `data.gd` | strip -> SpriteFrames, JSON loader |
| `smoke_test.gd`, `smoke_checks.gd` | headless data/asset/flow-field/gameplay checks |
Signals go up; `main.gd` plays VFX, spawns projectiles and monsters, applies gold, damages the character, destroys towers.

## Economy and wave flow
- Start gold, `prepare_time`, `wave_interval`, `hp_scale_per_wave`, `endless` block, optional `start_towers` and the wave list: `data/waves_grassland_01.json`.
- Wave i starts at `prepare_time + i * wave_interval` (or earlier via Call next wave). Groups spawn at start + delay + n * interval. Waves overlap freely, nothing waits for clears.
- Wave bonus: paid when the next wave starts. After the listed waves, `_endless_wave(k)` makes waves with more monsters, shorter intervals, `hp_mult = 1 + hp_scale * (k + 1)` and a boss group (flag `boss`) every `boss_every` waves.
- Place: spends `towers.json.cost`. Upgrade: `upgrade_costs[level-1]`. Sell: refunds `floor(invested * sell_refund)`. Destroyed by a monster: no refund. Kill: `monsters.json.reward`.
- Defeat only: the character reaches 0 hp -> `GameState.defeat()` -> overlay, tree paused. Restart reloads the scene.

## Towers
- `towers.json` per tower: `levels[]` (5 entries, index 0 = Lv1) with `damage`, `range_cells`, `cooldown`, optional `crit_chance`, `crit_mult`, `statuses[]`, `splash_radius_cells`, `splash_mult`, `splash_statuses`; missing keys fall back to the top-level key (`tower.stat_at`). Top-level `damage`, `range_cells`, `cooldown`, `statuses` are a Lv1 summary for the art tools.
- Other keys: `footprint`, `targeting`, `cost`, `sell_refund`, `upgrade_costs[4]`.
- Targeting runs every frame in `main._process`. Splash: `main._on_tower_fired` passes `{radius_px, mult, statuses}` to the projectile.
- Panel: left click a placed tower (nothing picked). Right click / Esc / Close / click on empty ground closes it.
- Placement rule (`main._build_block_reason`): footprint buildable and free, not on the character cell, footprint centre within `build_radius_cells * 64` px of the character.

## Monsters (data/monsters.json)
- Combat: `damage`, `attack_cooldown`, optional `attack_range`, `tower_range` (px; defaults in `data/ai.json`).
- `armor` 0..0.9 removes that fraction of DIRECT damage (DoT ignores it).
- `ability`: `burst` (Boar: `duration`, `speed_mult`), `spore` (Mushroom: `windup`, `radius_cells`, `heal_frac`); ability timers wait while frozen / stunned or attacking.
- Status tint: `status_tint_strength`, `status_tints`.
- Animation lock: `_hit_playing` (hit / attack / ability animation), `_attacking` (real attack: no movement). Hit does not interrupt an attack; starting an attack replaces a hit animation. Walk speed_scale = speed / (stride * 12/8), 0 when frozen.
- Debug keys: F1-F5 statuses, F6 boss treant, 7 boar, 8 mushroom, 9 hit all for 10.

## Data (`data/`)
Godot-owned: `towers.json`, `monsters.json`, `status_effects.json`, `waves_grassland_01.json`, `player.json` (hp, speed, collision_radius, build_radius_cells, build_on_path, start_cell, regen_per_sec), `ai.json` (free_cost, tower_cost, default_attack_range_px, tower_attack_range_px). Generated: `vfx.json`, `grassland_tileset_32.json`. Hand-edited: `map_grassland_01.json` (logic grid + `enemy_path`), `map_decor.json`.

## Asset -> node mapping
- Tileset `grassland_tileset_32.png` (32 px, 8 columns; row 0 grass, rows 1-6 path, rows 7-12 water). Bitmask N1 E2 S4 W8 NE16 SE32 SW64 NW128; corners count only if both adjacent edges set; outside map = connected.
- Tower strips (96x96, pivot centre) in `assets/Towers/<Name>/tower_<id>_level_0N_<suffix>.png`: base node = `spawn` (build), `base_idle`, `destroyed`; head node = `head_idle`, `head_attack`. Event frames: stone 3, archer 5, frost 5.
- Monster strips: `assets/Monsters/Grassland/<Name>/Strips/monster_<id>_<anim>_<dir>.png` (+ `spawn_E`). fps: idle 8, walk 12, attack 14, hit 12, death 12, spawn 12. Attack damage frame 4. Direction from movement.
- Projectiles face EAST: rotate by travel angle. VFX are horizontal strips described in `vfx.json`.
- Player art: none yet (art request in ROADMAP).
- Full list: `docs/ASSET_CATALOG.md` (generated).

## Conventions for new content
1. New asset family: art tool output -> `export_assets.py` -> data entry (`data/*.json`) -> integration (data first, code second) -> `validate.py` passes.
2. Towers/monsters are registry-driven: adding an id to `towers.json`/`monsters.json` should need no new code unless behaviour is new (monsters need `damage` and `attack_cooldown`).
3. Review-only outputs (GIFs, labeled sheets) never enter `res://`.
