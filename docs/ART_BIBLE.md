# ART BIBLE - Approved (Phases 1-4)

## Concept
Original casual fantasy cartoon tower defense, top-down. Colourful, cute, friendly, rounded shapes, clean silhouettes, soft shadows, rich-but-not-cluttered detail. Inspired by the general quality of Kingdom Rush / Plants vs Zombies / Clash Royale; **never copy** their characters, art or UI.
Rendering style as built: clean vector-cartoon (shape + soft highlight + dark outline), not painterly. *Open decision: a more hand-painted texture look would change the pipeline (see roadmap).*

## Camera, grid, sizes
| Item | Value |
|---|---|
| Perspective | True top-down, no exceptions |
| Art tile | 32 x 32 px |
| Logical gameplay cell | 64 x 64 px (= 2x2 art tiles) |
| Enemy path width | 1 logical cell (2 art tiles) |
| Tower footprint | 1x1 cell (64 px); 2x2 (128 px) supported |
| Tower frame | 96 x 96, pivot (48,48) |
| Monster frames | Slime 64, Mushroom 64, Goblin 80, Boar 80, Treant 96; pivot = frame centre |
| Sample map | 20 x 12 cells = 1280 x 768 px |

## Layers (bottom to top)
1 ground  2 water  3 path  4 path decals (direction chevrons)  5 small ground decor  6 large objects (trees, boulders, fences)  [grid logic = data only]  7 grid rendering  8 placement states  9 ghost + range ring  then towers / monsters, then UI.
Grid overlay sprites live in `Environment/Shared/Grid/` and are drawn on top of the ground. Ground tiles never contain grid lines.

## Lighting and rendering rules
- Light from the **top-left**; shadows fall bottom-right (offset about +1.5 / +3.5 px, blurred, alpha about 80). Shadows are separate PNGs.
- Draw at **4x supersample, downscale with LANCZOS**.
- One dark outline colour for characters and objects: RGB (52,40,50). Foliage outline (34,88,42). Outline weight about 1.2-1.6 px at 1x.
- Every form: base colour + lighter top-left highlight + darker outline. Small bright specular dots on eyes/gems.
- Direction art is **re-drawn per direction** (not rotated bitmaps) so lighting stays top-left. Tower heads are the exception: they are rotated by the engine.

## Palette (RGB, as used)
**Grassland ground:** grass (112,192,72); light blotch (124,204,80); dark blotch (102,180,64); blades (152,217,96)/(82,152,54). Path dirt (212,160,98), path border (132,90,52), rim light (244,204,150). Water (70,170,228), light ripple (190,235,252), bank (150,112,70).
**Stone/materials:** stone wall (150,154,172), light (196,200,214), floor (206,208,220); wood (178,122,70), dark (118,76,44), light (220,168,106); gold (255,210,84); red accent (226,66,74).
**Ice/frost:** ice (140,218,252), light (226,248,255), deep (64,142,222), glow (120,220,255).
**Monsters:** slime green (96,204,100); goblin skin (128,190,78), cap (196,76,66); boar (156,102,68), snout (242,168,168); mushroom cap (226,78,86), cream (252,236,204); treant bark (124,84,54), leaves (46,122,58)/(84,168,70)/(152,218,98).
**Future environments (not built):** Mountain = grey, blue-grey, forest green, snow white, muted brown. Beach = turquoise, sand yellow, coral pink, tropical green, ocean blue. Volcanic = charcoal, deep red, orange, bright yellow, dark purple.

## Tower design principles
Distinct silhouette + colour identity + role per tower. Base fixed, only attack head animates/rotates. Five visual levels:
- Lv1 simple recognisable silhouette
- Lv2 extra components, more decoration
- Lv3 gold/premium trim, stronger silhouette
- Lv4 additional systems (second banner, inner keep, cape, floating shards, glow)
- Lv5 premium final form with magical glow and the most elaborate silhouette
All levels must be distinguishable at normal gameplay zoom.

## Monster design principles
Cute and charming, not scary. Strong top-down silhouette, readable facing direction, distinctive colour per species, consistent scale. Roles: normal, fast, tank, flying, ranged, special ability, elite, boss. Every monster has idle, walk, attack, hit, spawn, death.

## Environment principles
Every environment: unique palette and atmosphere, same grid/tile architecture, buildable vs non-buildable terrain clearly distinguishable by art (and by logic data), path clearly different from buildable ground, modular autotiles.

## UI direction (not yet built)
Friendly, colourful, modern, rounded corners, playful icons, soft shadows, large buttons, clear hierarchy, desktop + mobile responsive, no information overload.

## Naming
snake_case. Examples: `grassland_ground_01.png`, `grassland_path_12_m030.png`, `tower_stone_level_03_idle.png`, `tower_archer_level_05_head_attack.png`, `monster_slime_walk_E.png`, `projectile_ice_shard.png`, `vfx_ice_explosion.png`, `grid_cell_invalid_64.png`, `ui_button_play.png`.
