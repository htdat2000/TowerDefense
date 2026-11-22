# tools/art - Python art generators (Pillow). Not shipped in the game.

## Pipeline order
`build_grassland.py` -> `build_towers.py` (also writes Godot strips, replacing `build_godot_strips.py`; see TODO) -> `build_monsters.py` -> `build_vfx.py` -> `export_assets.py` -> `validate.py` -> `gen_catalog.py`.
Scripts write to a work folder (`GameAssets/`, default `/mnt/user-data/outputs/GameAssets`; they currently hard-code it). `export_assets.py` copies the Godot-relevant files into this repo's `assets/`.

## Safe exporter
`python3 tools/art/export_assets.py --src /path/to/GameAssets`  (default dest = repo root)
Writes only `assets/**`, `data/vfx.json`, `data/grassland_tileset_32.json`. It never touches scripts, `towers.json`, `monsters.json`, `status_effects.json`. `data/map_*.json` is copied only if missing (`--overwrite-maps` to force). `--clean` deletes `assets/` first. It prints towers/monsters found in art that have no data entry yet.

## Moving the scripts in (TODO for an ART chat)
Copy the existing `build_*.py` here and (1) replace the hard-coded `ROOT` with an env var `GAME_ASSETS_ROOT`, (2) move shared helpers into `common.py` and import it instead of the `exec(split(...))` trick in `build_godot_strips.py`, (3) call the strip export at the end of `build_towers.py`. Keep behaviour identical; regenerate once and diff.

## Rules for every script
Draw at 4x supersample, downscale with LANCZOS; polygons with alpha < 255 must be alpha-composited; light from top-left; outline (52,40,50); naming and palette in `docs/ART_BIBLE.md`.

## Extending
- New tower: add `<name>_base(L)`, `<name>_head(L, ...)`, an 8-frame attack table, idle, spawn, rubble kind, shadow shape; register in `TOWERS`. Add projectile + impact. Then add the entry to `data/towers.json`.
- New monster: write `<name>(ang, mode, k)` with modes idle/walk/atk/hit; add an entry to `MON` (frame, shadow, stride, role, death/spawn config). Then add `data/monsters.json`.
- New environment: copy `build_grassland.py`, change palette/textures, keep the 47-tile bitmask autotile and the grid sprites; produce atlas + JSON + logic map.
- Animation standards: document name, frames, fps, loop, frame size, pivot, directions; verify visually before delivering.
