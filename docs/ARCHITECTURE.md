# ARCHITECTURE
Godot 4.3+ (dev 4.7.x), GL Compatibility, 1280x768, `canvas_items`, keep aspect. Linear texture filter by default; the three tile layers use Nearest. PNGs import lossless, no mipmaps.

## Scene / layer stack (`level.gd`, bottom to top by z_index)
Ground 0, Water 1, Path 2 (TileMapLayer) | Shadows 3, Decals 3, SmallDecor 4, Objects 5 (y-sort) | Grid 10 | Placement 11 | Actors 20 (towers+monsters, y-sort) | Projectiles 25 | Vfx 30 | UI (CanvasLayer) | Result overlay (CanvasLayer 10, always processing).
Grid lines are never baked into tiles. Hiding the grid or changing placement state never touches tile layers.

## Autoloads
| Name | Script | Role |
|---|---|---|
| `GameState` | `game_state.gd` | gold, lives, wave, speed (sets `Engine.time_scale`), `finished`; signals `gold_changed`, `lives_changed`, `wave_changed`, `speed_changed`, `game_over(won)`. `reset()` is called by `main.gd` with values from the level data. Connect to it with methods, never lambdas. |

## Scripts
| Script | Role |
|---|---|
| `main.gd` | demo controller: UI, placement, economy (charges GameState), selling, monster spawning, win/lose overlay, targeting (to be split in M2/M4) |
| `wave_manager.gd` | reads `data/waves_*.json`, schedules spawns, emits `spawn_requested`, `wave_started`, `wave_cleared`, `all_waves_cleared`; main calls `monster_resolved()` |
| `level.gd` | builds layers, tileset, autotiling, decor, enemy `Curve2D` from data |
| `grid_manager.gd` | grid LOGIC only (types, occupancy, can_place) |
| `grid_renderer.gd`, `placement_layer.gd` | grid lines; available/occupied/selected/invalid overlays, ghost, range ring |
| `tower.gd` | base + head + shadow; build/idle/attack/upgrade/destroy; prices (`upgrade_cost`, `sell_value`, `invested`); emits `fired`, `vfx_requested` |
| `monster.gd` | 4-dir animation, path follow, hit/death, status effects; emits `damaged`, `died`, `reached_end`, `vfx_requested` |
| `projectile.gd`, `vfx_one_shot.gd`, `vfx_library.gd`, `damage_number.gd` | projectiles, impacts, VFX helper, floating numbers |
| `sprite_frames_builder.gd`, `data.gd` | strip -> SpriteFrames, JSON loader |
Signals go up (`fired`, `damaged`, `died`, `reached_end`, `vfx_requested`); `main.gd` plays VFX, spawns projectiles and applies gold/lives.

## Economy and wave flow (M1)
- Start gold, start lives, optional `start_towers` and the wave list come from `data/waves_grassland_01.json`.
- Place: `main` spends `towers.json.cost`. Upgrade: spends `upgrade_costs[level-1]`. Sell: refunds `floor(invested * sell_refund)`; `invested` = cost + paid upgrades (computed in `tower.setup`, grown in `tower.upgrade`).
- Kill: `monsters.json.reward` added on `died`. Leak: `monsters.json.lives_cost` removed on `reached_end`. Wave clear: `bonus` gold from the wave entry.
- Wave monsters carry meta `counted = true`; only those are reported to `wave_manager.monster_resolved()` (debug F6 boss is not counted).
- Win = last wave cleared with lives > 0 (`GameState.win()`); lose = lives reach 0. Both pause the tree and show the overlay; Restart unpauses and reloads the scene.

## Data (`data/`)
`towers.json` (+ `cost`, `sell_refund`, `upgrade_costs[4]`), `monsters.json` (+ `reward`, `lives_cost`), `status_effects.json`, `waves_grassland_01.json` (Godot-owned); `vfx.json`, `grassland_tileset_32.json` (generated); `map_grassland_01.json` (logic grid + `enemy_path`), `map_decor.json`.

## Asset -> node mapping
- Tileset `grassland_tileset_32.png` (32 px, 8 columns; row 0 grass, rows 1-6 path, rows 7-12 water). Bitmask N1 E2 S4 W8 NE16 SE32 SW64 NW128; corners count only if both adjacent edges set; outside map = connected. JSON maps mask -> index.
- Tower strips (96x96, pivot centre) in `assets/Towers/<Name>/tower_<id>_level_0N_<suffix>.png`: base node = `spawn` (build), `base_idle`, `destroyed`; head node = `head_idle`, `head_attack`. Event frames: stone 3, archer 5, frost 5. Frost head does not rotate; archer idle sweep done in code.
- Monster strips: `assets/Monsters/Grassland/<Name>/Strips/monster_<id>_<anim>_<dir>.png` (+ `spawn_E`). fps: idle 8, walk 12, attack 14, hit 12, death 12, spawn 12. Walk `speed_scale = speed / (stride * 12/8)`. Attack damage frame 4. Direction from path tangent.
- Projectiles face EAST: rotate by travel angle. VFX are horizontal strips described in `vfx.json`.
- Sizes: monster frames 64/80/96, VFX per `vfx.json`. Full list: `docs/ASSET_CATALOG.md` (generated).

## Conventions for new content
1. New asset family: art tool output -> `export_assets.py` -> data entry (`data/*.json`) -> integration (data first, code second) -> `validate.py` passes.
2. Towers/monsters are registry-driven: adding an id to `towers.json`/`monsters.json` should need no new code unless behaviour is new (new towers also need `cost`, `sell_refund`, `upgrade_costs`; monsters `reward`, `lives_cost`).
3. Review-only outputs (GIFs, labeled sheets) never enter `res://`.
