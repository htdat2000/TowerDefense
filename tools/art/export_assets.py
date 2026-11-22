"""Safe exporter: copies generated art into the Godot project (this repo).

Writes ONLY: assets/**, data/vfx.json, data/grassland_tileset_32.json (generated).
Copies data/map_*.json only if missing (or with --overwrite-maps).
NEVER touches scripts/, scenes/, towers.json, monsters.json, status_effects.json.

Usage: python3 tools/art/export_assets.py --src /mnt/user-data/outputs/GameAssets [--dest .] [--clean] [--overwrite-maps]
"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return 1


def copy_pngs(src_dir, dst_dir):
    n = 0
    if not os.path.isdir(src_dir):
        print('  skip (missing):', src_dir)
        return 0
    for f in sorted(os.listdir(src_dir)):
        p = os.path.join(src_dir, f)
        if os.path.isfile(p) and f.endswith('.png'):
            n += cp(p, os.path.join(dst_dir, f))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.environ.get('GAME_ASSETS_ROOT', '/mnt/user-data/outputs/GameAssets'))
    ap.add_argument('--dest', default=REPO)
    ap.add_argument('--clean', action='store_true', help='delete assets/ before copying (assets only)')
    ap.add_argument('--overwrite-maps', action='store_true')
    a = ap.parse_args()
    src, dest = a.src, os.path.abspath(a.dest)
    A, D = os.path.join(dest, 'assets'), os.path.join(dest, 'data')
    if not os.path.isdir(src):
        sys.exit('source folder not found: ' + src)
    if a.clean and os.path.isdir(A):
        shutil.rmtree(A)
    os.makedirs(D, exist_ok=True)
    n = 0

    # environment
    E = os.path.join(src, 'Environment', 'Grassland')
    n += cp(f'{E}/grassland_tileset_32.png', f'{A}/Environment/Grassland/grassland_tileset_32.png')
    for sub in ('Decorations', 'Objects', 'Effects'):
        n += copy_pngs(f'{E}/{sub}', f'{A}/Environment/Grassland/{sub}')
    n += copy_pngs(f'{src}/Environment/Shared/Grid', f'{A}/Environment/Shared/Grid')
    cp(f'{E}/grassland_tileset_32.json', f'{D}/grassland_tileset_32.json')   # generated
    for f in sorted(os.listdir(E)):
        if f.startswith('map_') and f.endswith('.json'):
            if a.overwrite_maps or not os.path.exists(f'{D}/{f}'):
                cp(f'{E}/{f}', f'{D}/{f}'); print('  map written:', f)
            else:
                print('  map kept (hand-edited data, use --overwrite-maps to replace):', f)

    # towers: png files in each tower folder (SpriteSheets/Preview subfolders are skipped)
    tower_ids = []
    tdir = os.path.join(src, 'Towers')
    for fo in sorted(os.listdir(tdir)):
        p = os.path.join(tdir, fo)
        if fo in ('Preview',) or not os.path.isdir(p):
            continue
        n += copy_pngs(p, f'{A}/Towers/{fo}')
        for f in os.listdir(p):
            if f.startswith('tower_') and f.endswith('_shadow.png'):
                tower_ids.append(f[len('tower_'):-len('_shadow.png')])

    # monsters: shadow + Strips only
    mon_ids = []
    mroot = os.path.join(src, 'Monsters', 'Grassland')
    for m in sorted(os.listdir(mroot)):
        b = os.path.join(mroot, m)
        if not os.path.isdir(b):
            continue
        mid = m.lower(); mon_ids.append(mid)
        n += cp(f'{b}/monster_{mid}_shadow.png', f'{A}/Monsters/Grassland/{m}/monster_{mid}_shadow.png')
        n += copy_pngs(f'{b}/Strips', f'{A}/Monsters/Grassland/{m}/Strips')

    # projectiles + vfx, then vfx.json (generated from the art atlas)
    n += copy_pngs(f'{src}/Projectiles', f'{A}/Projectiles')
    n += copy_pngs(f'{src}/VFX', f'{A}/VFX')
    atlas_p = f'{src}/Documentation/vfx_atlas.json'
    if os.path.isfile(atlas_p):
        eff = json.load(open(atlas_p))['effects']
        out = {k: dict(path='res://assets/' + e['file'], group=e['group'], frames=e['frames'], frame_w=e['frame_w'],
                       frame_h=e['frame_h'], fps=e['fps'], loop=e['loop'], tintable=e['tintable'], event_frame=e['event_frame'])
               for k, e in eff.items()}
        json.dump(out, open(f'{D}/vfx.json', 'w'), indent=1)
        print('  vfx.json:', len(out), 'effects')
    else:
        print('  WARNING: vfx_atlas.json not found, data/vfx.json left unchanged')
    print('exported', n, 'png files to', A)

    # tell the Godot side what still needs a data entry
    def keys(name):
        p = f'{D}/{name}'
        return set(json.load(open(p)).keys()) if os.path.isfile(p) else set()
    for label, ids, have in (('towers', tower_ids, keys('towers.json')), ('monsters', mon_ids, keys('monsters.json'))):
        missing = sorted(set(ids) - have)
        if missing:
            print(f'  NOTE: art exists for {label} with no data entry yet: {missing} -> add to data/{label}.json')


if __name__ == '__main__':
    main()
