"""Exports Godot-friendly tower layers: base_idle (animated base without head) and head_idle (head only).
Reuses the drawing functions of build_towers.py (everything above its BUILD & EXPORT marker)."""
import json, os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_towers.py')).read().split('# ------------------------------------------------------------ BUILD & EXPORT')[0]
exec(compile(src, 'build_towers_defs', 'exec'))
FOLDERS = {'stone': 'Stone', 'archer': 'Archer', 'frost': 'Frost'}
for L in range(1, 6):
    for name, fo in FOLDERS.items():
        d = f"{ROOT}/Towers/{fo}"; tag = f'tower_{name}_level_{L:02d}'
        if name == 'stone':
            base = [stone_base(L, i / 8) for i in range(8)]; head = [stone_head(L)]
        elif name == 'archer':
            base = [archer_base(L)]; head = [archer_head(L, 0.0)]
        else:
            base = [comp(frost_base(L), twinkles(i)) for i in range(8)]
            head = [frost_head(L, 0.2 + 0.2 * math.sin(i / 8 * 6.2832), i * 6) for i in range(8)]
        strip(base).save(f'{d}/{tag}_base_idle.png'); strip(head).save(f'{d}/{tag}_head_idle.png')
spec_p = f'{ROOT}/Documentation/tower_animation_spec.json'; spec = json.load(open(spec_p))
for name in FOLDERS:
    sh = spec['towers'][name]['sheets']
    sh['base_idle'] = dict(frames=1 if name == 'archer' else 8, fps=8, loop=True, composite=False, note='Godot: base layer only (flag/twinkles). Pair with head layer.')
    sh['head_idle'] = dict(frames=8 if name == 'frost' else 1, fps=8, loop=True, composite=False, note='Godot: head layer only, faces EAST. Archer idle sweep is done by engine rotation.')
json.dump(spec, open(spec_p, 'w'), indent=1)
print('godot strips done')
