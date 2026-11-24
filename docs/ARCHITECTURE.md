# ARCHITECTURE
Godot 4.3+ (dev 4.7.x), GL Compatibility, 1280x768, `canvas_items`, keep aspect. Linear texture filter by default; the three tile layers use Nearest. PNGs import lossless, no mipmaps.

## Scene / layer stack (`level.gd`, bottom to top by z_index)
Ground 0, Water 1, Path 2 (TileMapLayer) | Shadows 3, Decals 3, SmallDecor 4, Objects 5 (y-sort) | Grid 10 | Placement 11 | Actors 20 (towers+monsters, y-sort) | Projectiles 25 | Vfx 30 | UI (CanvasLayer, includes the tower panel) | Result overlay (CanvasLayer 10, always processing).
Grid lines are never baked into tiles. Hiding the grid or changing placement state never touches tile layers.
Monster health bars are children of the monster with z_index 2 (relative), so they draw above every actor and below projectiles.

## Autoloads
| Name | Script | Role |
|---|---|---|
| `GameState` | `game_state.gd` | gold, lives, wave, speed (sets `Engine.time_scale`), `finished`; signals `gold_changed`, `lives_changed`, `wave_changed`, `speed_changed`, `game_over(won)`. `reset()` is called by `main.gd` with values from the level data. Connect to it with methods, never lambdas. |

## Scripts
| Script | Role |
|---|---|
| `main.gd` | demo controller: UI, tower panel, placement, economy (charges GameState), selling, monster spawning, win/lose overlay, per-frame targeting (to be split in M4) |
| `wave_manager.gd` | reads `data/waves_*.json`, schedules spawns, emits `spawn_requested`, `wave_started`, `wave_cleared`, `all_waves_cleared`; main calls `monster_resolved()` |
| `level.gd` | builds layers, tileset, autotiling, decor, enemy `Curve2D` from data |
| `grid_manager.gd` | grid LOGIC only (types, occupancy, can_place for any footprint) |
| `grid_renderer.gd`, `placement_layer.gd` | grid lines; available/occupied/selected/invalid overlays, ghost, range ring, selected placed tower |
| `tower.gd` | base + head + shadow; build/idle/attack/upgrade/destroy; stats from data (`stat`, `stat_at`, `damage`, `range_px`, `cooldown`, `splash_*`, `statuses`); prices (`upgrade_cost`, `sell_value`, `invested`); `targeting` mode, `cell`, `footprint`; emits `fired`, `vfx_requested`, `state_changed` |
| `targeting.gd` | static `Targeting.pick(mode, pos, range_px, monsters)`; modes first / last / strongest / closest |
| `monster.gd` | 4-dir animation, path follow, hit/death, status effects, armor, abilities (burst, spore), health bar; emits `damaged`, `healed`, `died`, `reached_end`, `vfx_requested` |
| `health_bar.gd` | floating hp bar child of a monster: hidden at full hp (bosses always shown), colour by hp, shield icon when armored |
| `projectile.gd`, `vfx_one_shot.gd`, `vfx_library.gd`, `damage_number.gd` | projectiles (damage, statuses, splash), impacts, VFX helper, floating numbers (normal / crit / heal) |
| `sprite_frames_builder.gd`, `data.gd` | strip -> SpriteFrames, JSON loader |
Signals go up (`fired`, `damaged`, `healed`, `died`, `reached_end`, `vfx_requested`, `state_changed`); `main.gd` plays VFX, spawns projectiles, shows numbers and applies gold/lives.

## Economy and wave flow (M1)
- Start gold, start lives, optional `start_towers` and the wave list come from `data/waves_grassland_01.json`.
- Place: `main` spends `towers.json.cost`. Upgrade: spends `upgrade_costs[level-1]`. Sell: refunds `floor(invested * sell_refund)`; `invested` = cost + paid upgrades (computed in `tower.setup`, grown in `tower.upgrade`).
- Kill: `monsters.json.reward` added on `died`. Leak: `monsters.json.lives_cost` removed on `reached_end`. Wave clear: `bonus` gold from the wave entry.
- Wave monsters carry meta `counted = true`; only those are reported to `wave_manager.monster_resolved()` (debug spawns F6/F7/Q are not counted).
- Win = last wave cleared with lives > 0 (`GameState.win()`); lose = lives reach 0. Both pause the tree and show the overlay; Restart unpauses and reloads the scene.

## Towers (M2)
- `towers.json` per tower: `levels[]` (5 entries, index 0 = Lv1) with `damage`, `range_cells`, `cooldown`, optional `crit_chance`, `crit_mult`, `statuses[]`, `splash_radius_cells`, `splash_mult`, `splash_statuses`. A key missing in a level falls back to the tower's top-level key (`tower.stat_at`). The top-level `damage`, `range_cells`, `cooldown`, `statuses` are the Lv1 summary that `gen_catalog.py` / `validate.py` read; the game uses `levels[]`.
- Other keys: `footprint` `[w, h]` (cells, default `[1, 1]`), `targeting` default mode, `cost`, `sell_refund`, `upgrade_costs[4]`.
- Targeting runs every frame in `main._process`: for each built tower `Targeting.pick(t.targeting, ...)`. `first` / `last` use `monster.dist` (distance along the path), `strongest` uses current `hp`, `closest` uses distance to the tower. The player cycles the mode in the panel.
- Splash: `main._on_tower_fired` builds `{radius_px, mult, statuses}` from the tower and passes it to `projectile.setup`. On hit the target takes full damage and statuses; other monsters in group `monsters` within the radius take `damage * mult` (no crit), statuses only if `splash_statuses` is true. Monsters join the group in `main._spawn_monster`.
- Panel: left click a placed tower (no tower picked) -> `main._select_placed`. Shows current -> next-level values, upgrade (disabled when busy, max level or unaffordable), sell (two clicks), targeting. `placement_layer.select_cell` draws the footprint highlight and range ring. Right click / Esc / Close / click on empty ground closes it.
- Footprints: `main._footprint(id)` reads data; `grid.can_place` / `place` / `footprint_center` already handle any size. The cursor cell is the top-left cell of the footprint. Tower art is 96 px, so a 2x2 tower will look small until 2x2 art exists.

## Monsters (M3, written, not yet play-tested)
All keys live in `monsters.json` (Godot-owned):
- `armor` 0..0.9: `monster.take_damage` removes that fraction of DIRECT damage before `damaged` is emitted (so numbers show the reduced value). Burning / poison DoT calls `_apply_damage` directly and ignores armor.
- `ability` (optional dictionary, `kind` selects behaviour; `first_delay` and `cooldown` in seconds, optional `vfx`, `vfx_scale`, `vfx_tint`):
  - `burst` (Boar): `duration`, `speed_mult`. Plays the attack animation as telegraph, multiplies speed (and walk animation speed) for `duration`.
  - `spore` (Mushroom): `windup`, `radius_cells`, `heal_frac`. Only starts when an injured living ally is in range; after `windup` heals every other monster in the radius by `heal_frac * max_hp` through `monster.heal()`, which emits `healed(m, amount)`; `main` shows a green "+N" via `damage_number.gd` kind `heal`.
  - Ability timers wait while the monster is frozen or stunned (status speed multiplier 0).
- Status tint: `status_tint_strength` (0..1, lerp from white toward the status colour) and `status_tints` (per-status colour override) on top of the global colours in `status_effects.json`.
- Health bar: see `health_bar.gd`; fraction updated in `_apply_damage` and `heal`, hidden on death.
- Animation lock: `_hit_playing` is true while a hit or attack animation plays; direction changes during it are applied when the animation ends.
- Debug keys: F6 boss treant, F7 boar, Q mushroom, W 10 damage to all.

## Data (`data/`)
`towers.json`, `monsters.json` (+ `reward`, `lives_cost`, `armor`, `ability`, tint keys), `status_effects.json`, `waves_grassland_01.json` (Godot-owned); `vfx.json`, `grassland_tileset_32.json` (generated); `map_grassland_01.json` (logic grid + `enemy_path`), `map_decor.json`.

## Asset -> node mapping
- Tileset `grassland_tileset_32.png` (32 px, 8 columns; row 0 grass, rows 1-6 path, rows 7-12 water). Bitmask N1 E2 S4 W8 NE16 SE32 SW64 NW128; corners count only if both adjacent edges set; outside map = connected. JSON maps mask -> index.
- Tower strips (96x96, pivot centre) in `assets/Towers/<Name>/tower_<id>_level_0N_<suffix>.png`: base node = `spawn` (build), `base_idle`, `destroyed`; head node = `head_idle`, `head_attack`. Event frames: stone 3, archer 5, frost 5. Frost head does not rotate; archer idle sweep done in code.
- Monster strips: `assets/Monsters/Grassland/<Name>/Strips/monster_<id>_<anim>_<dir>.png` (+ `spawn_E`). fps: idle 8, walk 12, attack 14, hit 12, death 12, spawn 12. Walk `speed_scale = speed / (stride * 12/8)`. Attack damage frame 4. Direction from path tangent.
- Projectiles face EAST: rotate by travel angle. VFX are horizontal strips described in `vfx.json`.
- Sizes: monster frames 64/80/96, VFX per `vfx.json`. Full list: `docs/ASSET_CATALOG.md` (generated).

## Conventions for new content
1. New asset family: art tool output -> `export_assets.py` -> data entry (`data/*.json`) -> integration (data first, code second) -> `validate.py` passes.
2. Towers/monsters are registry-driven: adding an id to `towers.json`/`monsters.json` should need no new code unless behaviour is new (new towers also need `cost`, `sell_refund`, `upgrade_costs`, `levels[]`; monsters `reward`, `lives_cost`, optional `armor` / `ability`).
3. Review-only outputs (GIFs, labeled sheets) never enter `res://`.
