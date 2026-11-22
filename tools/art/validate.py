"""One static check for the whole project (Godot NOT run). Run from anywhere: python3 tools/art/validate.py
Checks: JSON validity, every asset path referenced by data/scripts exists, vfx strip sizes (needs Pillow, optional),
status kinds/overlays, monster tints, GDScript brackets / tabs / indent, preload paths, VFX names used in scripts,
signal-connect targets in main.gd, map consistency, tileset masks."""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
errs, warn = [], []


def res(p): return os.path.join(ROOT, p.replace('res://', ''))
def need(p, why):
    if not os.path.isfile(res(p)): errs.append(f'MISSING {p} ({why})')
def J(rel):
    try: return json.load(open(os.path.join(ROOT, rel)))
    except Exception as e:
        errs.append(f'BAD/MISSING JSON {rel}: {e}'); return {}


# ---- JSON
for f in sorted(os.listdir(f'{ROOT}/data')):
    if f.endswith('.json'):
        try: json.load(open(f'{ROOT}/data/{f}'))
        except Exception as e: errs.append(f'BAD JSON data/{f}: {e}')
towers, mons, vfx, stat = J('data/towers.json'), J('data/monsters.json'), J('data/vfx.json'), J('data/status_effects.json')

# ---- towers / monsters assets
for tid, t in towers.items():
    need(f"res://assets/Towers/{t['folder']}/tower_{tid}_shadow.png", 'shadow')
    need(t['projectile'], 'projectile'); need(t['impact']['path'], 'impact')
    for L in range(1, 6):
        for suf in ('spawn', 'base_idle', 'destroyed', 'head_idle', 'head_attack', 'base', 'head_static'):
            need(f"res://assets/Towers/{t['folder']}/tower_{tid}_level_{L:02d}_{suf}.png", 'tower strip')
    for s in t.get('statuses', []):
        if s['kind'] not in stat: errs.append(f'{tid}: unknown status {s["kind"]}')
for mid, m in mons.items():
    b = f"res://assets/Monsters/Grassland/{m['folder']}"
    need(f'{b}/monster_{mid}_shadow.png', 'shadow'); need(f'{b}/Strips/monster_{mid}_spawn_E.png', 'spawn')
    for a in ('idle', 'walk', 'attack', 'hit', 'death'):
        for d in 'ESWN': need(f'{b}/Strips/monster_{mid}_{a}_{d}.png', 'strip')
    if len(m.get('tint', [1, 1, 1])) != 3: errs.append(mid + ': tint must have 3 values')

# ---- environment / grid
E = 'res://assets/Environment/Grassland/'
need(E + 'grassland_tileset_32.png', 'tileset')
for n in ['Effects/grassland_shadow_64', 'Objects/grassland_obj_tree_64', 'Objects/grassland_obj_boulder_64', 'Objects/grassland_obj_bush_64',
          'Objects/grassland_obj_fence_h_32', 'Decorations/grassland_deco_lilypad_32', 'Decorations/grassland_deco_arrow_right_32']:
    need(E + n + '.png', 'object')
for k in ['flower_red', 'flower_yellow', 'flower_white', 'flower_blue', 'tuft', 'mushroom', 'rock_small', 'stump']:
    need(E + f'Decorations/grassland_deco_{k}_32.png', 'decor')
G = 'res://assets/Environment/Shared/Grid/'
for n in ['grid_line_64', 'grid_range_ring_256'] + [f'grid_cell_{s}_64' for s in ('available', 'selected', 'invalid', 'occupied')] + \
         [f'grid_footprint_{s}_128' for s in ('selected', 'invalid')]:
    need(G + n + '.png', 'grid')
ts = J('data/grassland_tileset_32.json')
if ts and (len(ts['path_index_by_mask']) != 47 or len(ts['water_index_by_mask']) != 47): errs.append('tileset json must have 47 masks')
mp = J('data/map_grassland_01.json')
if mp and (len(mp['cells']) != mp['rows'] or len(mp['cells'][0]) != mp['cols']): errs.append('map size mismatch')

# ---- vfx
try:
    from PIL import Image
except ImportError:
    Image = None; warn.append('Pillow missing: vfx image sizes not checked')
for k, e in vfx.items():
    p = res(e['path'])
    if not os.path.isfile(p): errs.append('MISSING vfx ' + e['path']); continue
    if Image:
        im = Image.open(p)
        if im.size != (e['frame_w'] * e['frames'], e['frame_h']): errs.append(f'{k}: size {im.size} != {e["frames"]}x{e["frame_w"]}x{e["frame_h"]}')
        if im.mode != 'RGBA': errs.append(k + ' not RGBA')
for k in stat:
    if 'status_' + k not in vfx: errs.append('status without overlay vfx: ' + k)

# ---- scripts
defs = {}
for f in sorted(os.listdir(f'{ROOT}/scripts')):
    if not f.endswith('.gd'): continue
    src = open(f'{ROOT}/scripts/{f}').read(); defs[f] = src
    if '\t' in src: errs.append(f'{f}: contains tabs (project uses 4 spaces)')
    for ch, cl in ('()', '[]', '{}'):
        if src.count(ch) != src.count(cl): errs.append(f'{f}: unbalanced {ch}{cl} ({src.count(ch)} vs {src.count(cl)})')
    for m in re.finditer(r'(?:preload|load)\("(res://[^"%]+)"\)', src):
        p = m.group(1)
        if not p.endswith('/') and not os.path.exists(res(p)): errs.append(f'{f}: references missing {p}')
    for m in re.finditer(r'(?:play_once\([^,]+,\s*|make_loop\(|vfx_requested\.emit\(|_play_vfx\()"([a-z_]+)"\s*[,)]', src):
        if m.group(1) not in vfx: errs.append(f'{f}: vfx "{m.group(1)}" not in data/vfx.json')
    for i, line in enumerate(src.split('\n'), 1):
        ind = len(line) - len(line.lstrip(' '))
        if line.strip() and ind % 4 and not line.lstrip().startswith(('"', '#', ')', ']', '}')): warn.append(f'{f}:{i} indent {ind}')
if 'main.gd' in defs:
    for fn in re.findall(r'\.connect\((_[a-z_]+)', defs['main.gd']):
        if not re.search(rf'func {fn}\(', defs['main.gd']): errs.append(f'main.gd: connect to missing method {fn}')
for sig in ('vfx_requested', 'damaged', 'fired'):
    if f'signal {sig}' not in defs.get('monster.gd', '') + defs.get('tower.gd', ''): errs.append('missing signal ' + sig)
if not os.path.isfile(f'{ROOT}/scenes/main.tscn'): errs.append('MISSING scenes/main.tscn')

print(f'towers {len(towers)} | monsters {len(mons)} | vfx {len(vfx)} | scripts {len(defs)} | ERRORS {len(errs)} | WARNINGS {len(warn)}')
for e in errs: print('  ERR ', e)
for w in warn[:12]: print('  warn', w)
sys.exit(1 if errs else 0)
