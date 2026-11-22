"""Generates docs/ASSET_CATALOG.md from data/*.json and assets/ (replaces the hand-written ASSET_SPECS).
Run after export_assets.py: python3 tools/art/gen_catalog.py"""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
def J(n):
    p = f'{ROOT}/data/{n}'
    return json.load(open(p)) if os.path.isfile(p) else {}
def count(sub):
    return sum(len([f for f in fs if f.endswith('.png')]) for _, _, fs in os.walk(f'{ROOT}/assets/{sub}'))
T, M, V, S = J('towers.json'), J('monsters.json'), J('vfx.json'), J('status_effects.json')
o = ['# ASSET CATALOG (GENERATED - do not edit; run tools/art/gen_catalog.py)\n',
     f"PNG files: environment {count('Environment')}, towers {count('Towers')}, monsters {count('Monsters')}, projectiles {count('Projectiles')}, vfx {count('VFX')}.\n",
     '## Towers (96x96, pivot centre, 5 levels, head faces EAST)',
     '| id | folder | head rotates | event frame | projectile | range (cells) | cooldown | damage |', '|---|---|---|---|---|---|---|---|']
for k, t in T.items():
    o.append(f"| {k} | {t['folder']} | {t['head_rotates']} | {t['event_frame']} | {os.path.basename(t['projectile'])} | {t['range_cells']} | {t['cooldown']} | {t['damage']} |")
o += ['\nStrips per level: spawn, base_idle, head_idle, head_attack, destroyed, base, head_static. Anim fps: build 14, idle 8, attack 16, destroyed 12.\n',
      '## Monsters (4 directions E,S,W,N; strips in Strips/)', '| id | frame | role | stride | hp | speed |', '|---|---|---|---|---|---|']
for k, m in M.items():
    o.append(f"| {k} | {m['frame']} | {m['role']} | {m['stride']} | {m['hp']} | {m['speed']} |")
o += ['\nFrames/fps: idle 6 @8 loop, walk 8 @12 loop, attack 8 @14 (damage frame 4), hit 4 @12, death 10 @12, spawn 10 @12 (E only).\n',
      '## Status effects', '| kind | speed mult | dps |', '|---|---|---|']
for k, s in S.items():
    o.append(f"| {k} | {s.get('speed_mult', 1)} | {s.get('dps', 0)} |")
o += ['\n## VFX (horizontal strips, pivot centre)', '| name | group | frames | frame size | fps | loop | tintable |', '|---|---|---|---|---|---|---|']
for k, e in V.items():
    o.append(f"| {k} | {e['group']} | {e['frames']} | {e['frame_w']}x{e['frame_h']} | {e['fps']} | {e['loop']} | {e['tintable']} |")
o.append('\nEnvironment: grassland_tileset_32.png (32 px tiles, 8 columns; row 0 grass, rows 1-6 path, rows 7-12 water); decorations, objects, shadows and shared grid sprites under assets/Environment/.')
open(f'{ROOT}/docs/ASSET_CATALOG.md', 'w').write('\n'.join(o) + '\n')
print('wrote docs/ASSET_CATALOG.md')
