import os, json, random, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = '/mnt/user-data/outputs/GameAssets'
T, CELL, S = 32, 64, 4          # art tile, logical cell, supersample
G = f'{ROOT}/Environment/Grassland'
SH = f'{ROOT}/Environment/Shared/Grid'
DOC = f'{ROOT}/Documentation'
for sub in ['Ground', 'Paths', 'Water', 'Decorations', 'Objects', 'Effects']:
    os.makedirs(f'{G}/{sub}', exist_ok=True)
os.makedirs(SH, exist_ok=True); os.makedirs(DOC, exist_ok=True)
os.makedirs(f'{ROOT}/Environment/Grassland/Preview', exist_ok=True)

def save(im, path): im.save(path)

# ---------------------------------------------------------------- ground
def grass(seed, dark=False):
    r = random.Random(seed)
    base = (104, 184, 66) if dark else (112, 192, 72)
    im = Image.new('RGBA', (T, T), base + (255,)); px = im.load()
    for _ in range(7):
        cx, cy, rad = r.randrange(T), r.randrange(T), r.randint(3, 6)
        col = r.choice([(124, 204, 80), (102, 180, 64)])
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if dx * dx + dy * dy <= rad * rad:
                    px[(cx + dx) % T, (cy + dy) % T] = col + (255,)
    for _ in range(26):
        x, y = r.randrange(T), r.randrange(T)
        col = r.choice([(152, 217, 96), (82, 152, 54), (140, 210, 90)])
        px[x, y] = col + (255,); px[x, (y - 1) % T] = col + (255,)
    for _ in range(2):
        x, y = r.randrange(T), r.randrange(T); px[x, y] = (214, 224, 110, 255)
    return im

# ---------------------------------------------------------------- blob autotile (47)
N, E, S_, W, NE, SE, SW, NW = 1, 2, 4, 8, 16, 32, 64, 128
def canon(m):
    if not (m & N and m & E): m &= ~NE
    if not (m & S_ and m & E): m &= ~SE
    if not (m & S_ and m & W): m &= ~SW
    if not (m & N and m & W): m &= ~NW
    return m
MASKS = sorted(set(canon(m) for m in range(256)))
assert len(MASKS) == 47

def solid(color, alpha_mask, mul=1.0):
    im = Image.new('RGBA', alpha_mask.size, color)
    im.putalpha(alpha_mask.point(lambda v: int(v * mul)))
    return im

def dirt_tex(r, size):
    im = Image.new('RGBA', (size, size), (212, 160, 98, 255)); d = ImageDraw.Draw(im)
    for _ in range(30):
        x, y, rr = r.randrange(size), r.randrange(size), r.randint(3, 7)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=r.choice([(194, 142, 82), (228, 182, 120), (182, 132, 76)]))
    for _ in range(5):
        x, y, rr = r.randrange(size), r.randrange(size), r.randint(4, 7)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(176, 170, 156), outline=(120, 112, 100), width=2)
    return im

def water_tex(r, size):
    im = Image.new('RGBA', (size, size), (70, 170, 228, 255)); d = ImageDraw.Draw(im)
    for _ in range(4):
        x, y = r.randrange(size), r.randrange(size); w = r.randint(20, 40)
        d.arc((x, y, x + w, y + w // 2), 200, 340, fill=(190, 235, 252, 255), width=4)
    for _ in range(6):
        x, y, rr = r.randrange(size), r.randrange(size), r.randint(2, 4)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(98, 192, 240, 255))
    return im

def blob_tile(mask, kind, seed=0):
    r = random.Random(seed * 1000 + mask)
    size = T * S; m = 4 * S; rad = 9 * S
    n, e, s, w = bool(mask & N), bool(mask & E), bool(mask & S_), bool(mask & W)
    x0 = 0 if w else m; x1 = size if e else size - m
    y0 = 0 if n else m; y1 = size if s else size - m
    M = Image.new('L', (size, size), 0); d = ImageDraw.Draw(M)
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
    if not n and not w:
        d.rectangle((x0, y0, x0 + rad, y0 + rad), fill=0); d.pieslice((x0, y0, x0 + 2 * rad, y0 + 2 * rad), 180, 270, fill=255)
    if not n and not e:
        d.rectangle((x1 - rad, y0, x1, y0 + rad), fill=0); d.pieslice((x1 - 2 * rad, y0, x1, y0 + 2 * rad), 270, 360, fill=255)
    if not s and not e:
        d.rectangle((x1 - rad, y1 - rad, x1, y1), fill=0); d.pieslice((x1 - 2 * rad, y1 - 2 * rad, x1, y1), 0, 90, fill=255)
    if not s and not w:
        d.rectangle((x0, y1 - rad, x0 + rad, y1), fill=0); d.pieslice((x0, y1 - 2 * rad, x0 + 2 * rad, y1), 90, 180, fill=255)
    for cond, c in [(n and w and not mask & NW, (0, 0)), (n and e and not mask & NE, (size, 0)),
                    (s and e and not mask & SE, (size, size)), (s and w and not mask & SW, (0, size))]:
        if cond: d.ellipse((c[0] - m, c[1] - m, c[0] + m, c[1] + m), fill=0)
    D2 = M.filter(ImageFilter.MaxFilter(25)); D1 = M.filter(ImageFilter.MaxFilter(13))
    Er = M.filter(ImageFilter.MinFilter(11)); rim = ImageChops.subtract(M, Er)
    if kind == 'path':
        tex, outc, rimc = dirt_tex(r, size), (132, 90, 52, 255), (244, 204, 150, 255)
    else:
        tex, outc, rimc = water_tex(r, size), (150, 112, 70, 255), (180, 232, 252, 255)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out = Image.alpha_composite(out, solid((40, 96, 40, 255), D2, 0.30))
    out = Image.alpha_composite(out, solid(outc, D1))
    t = tex.copy(); t.putalpha(M); out = Image.alpha_composite(out, t)
    out = Image.alpha_composite(out, solid(rimc, rim, 0.55))
    return out.resize((T, T), Image.LANCZOS)

# ---------------------------------------------------------------- decorations
def newc(w, h): return Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
def fin(im, w, h): return im.resize((w, h), Image.LANCZOS)
def circ(d, cx, cy, r, fill, outline=None, ow=1.2):
    if outline: d.ellipse(((cx - r - ow) * S, (cy - r - ow) * S, (cx + r + ow) * S, (cy + r + ow) * S), fill=outline)
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=fill)
def rrect(d, x0, y0, x1, y1, fill, outline, rad=1.5, ow=1.0):
    d.rounded_rectangle(((x0 - ow) * S, (y0 - ow) * S, (x1 + ow) * S, (y1 + ow) * S), radius=rad * S, fill=outline)
    d.rounded_rectangle((x0 * S, y0 * S, x1 * S, y1 * S), radius=rad * S, fill=fill)

FOL_O = (34, 88, 42, 255)
def foliage(w, seed, dark, mid, light, berries=False, n=7, ring=0.52, sub=0.40):
    r = random.Random(seed); im = newc(w, w); d = ImageDraw.Draw(im)
    c = w / 2; R = w * 0.44
    circ(d, c, c, R, dark, FOL_O, 1.4)
    for i in range(n):
        a = i / n * 2 * math.pi + r.random() * 0.4
        x, y = c + math.cos(a) * R * ring, c + math.sin(a) * R * ring
        circ(d, x, y, R * sub, mid, None)
        circ(d, x - R * 0.10, y - R * 0.12, R * sub * 0.5, light, None)
    circ(d, c - R * 0.05, c - R * 0.05, R * 0.38, mid)
    circ(d, c - R * 0.15, c - R * 0.17, R * 0.20, light)
    if berries:
        for _ in range(5):
            a = r.random() * 2 * math.pi; q = r.random() * R * 0.75
            circ(d, c + math.cos(a) * q, c + math.sin(a) * q, w * 0.035, (232, 70, 78, 255), (120, 28, 40, 255), 0.5)
    return fin(im, w, w)

def tree64(): return foliage(64, 1, (52, 128, 56, 255), (84, 168, 70, 255), (150, 216, 96, 255), True, 8, 0.55, 0.38)
def bush64(): return foliage(64, 2, (66, 150, 62, 255), (100, 186, 78, 255), (170, 228, 110, 255), False, 6, 0.5, 0.42)
def bush32(): return foliage(32, 3, (66, 150, 62, 255), (100, 186, 78, 255), (170, 228, 110, 255), True, 5, 0.5, 0.42)

def rock(w, seed, big=False):
    r = random.Random(seed); im = newc(w, w); d = ImageDraw.Draw(im); c = w / 2
    R = w * (0.42 if big else 0.34); n = 9
    pts = [(c + math.cos(i / n * 6.283) * R * (0.85 + r.random() * 0.25), c + math.sin(i / n * 6.283) * R * (0.8 + r.random() * 0.25)) for i in range(n)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=(150, 154, 172, 255), outline=(66, 68, 90, 255), width=int(1.4 * S))
    inner = [(c + (x - c) * 0.72 - R * 0.06, c + (y - c) * 0.72 - R * 0.08) for x, y in pts]
    d.polygon([(x * S, y * S) for x, y in inner], fill=(186, 190, 206, 255))
    d.polygon([(x * S, y * S) for x, y in [(p[0] * 0.55 + c * 0.45 - R * .1, p[1] * 0.55 + c * 0.45 - R * .12) for p in pts]], fill=(214, 218, 230, 255))
    if big:
        d.line([(c * S, (c + 2) * S), ((c + 6) * S, (c + 8) * S), ((c + 4) * S, (c + 13) * S)], fill=(90, 92, 112, 255), width=2 * S)
    return fin(im, w, w)

def flower(col, seed):
    r = random.Random(seed); im = newc(32, 32); d = ImageDraw.Draw(im)
    for (cx, cy) in [(10 + r.randint(-2, 2), 11), (21 + r.randint(-2, 2), 15), (12, 23 + r.randint(-1, 2))]:
        circ(d, cx - 3, cy + 4, 1.6, (70, 150, 56, 255))
        for k in range(5):
            a = k / 5 * 6.283
            circ(d, cx + math.cos(a) * 2.5, cy + math.sin(a) * 2.5, 1.9, col, (255, 255, 255, 60), 0.4)
        circ(d, cx, cy, 1.5, (255, 214, 64, 255), (190, 130, 20, 255), 0.4)
    return fin(im, 32, 32)

def tuft():
    im = newc(32, 32); d = ImageDraw.Draw(im)
    for dx, ang, h, col in [(-5, -25, 10, (76, 150, 52)), (0, 0, 13, (96, 176, 64)), (5, 25, 10, (76, 150, 52)), (-2, -10, 9, (136, 204, 84)), (3, 12, 9, (136, 204, 84))]:
        bx, by = 16 + dx, 24
        tx, ty = bx + math.sin(math.radians(ang)) * h, by - math.cos(math.radians(ang)) * h
        d.polygon([((bx - 2) * S, by * S), ((bx + 2) * S, by * S), (tx * S, ty * S)], fill=col + (255,), outline=(44, 110, 44, 255))
    return fin(im, 32, 32)

def mushroom():
    im = newc(32, 32); d = ImageDraw.Draw(im)
    for (cx, cy, r) in [(13, 15, 8), (23, 21, 5)]:
        circ(d, cx, cy, r, (228, 72, 72, 255), (122, 30, 42, 255), 1.2)
        circ(d, cx - r * .25, cy - r * .3, r * .55, (244, 112, 104, 255))
        for a in (0.5, 2.3, 4.1):
            circ(d, cx + math.cos(a) * r * .55, cy + math.sin(a) * r * .55, r * .18, (255, 250, 240, 255))
    return fin(im, 32, 32)

def stump():
    im = newc(32, 32); d = ImageDraw.Draw(im)
    circ(d, 16, 16, 11, (150, 100, 58, 255), (84, 52, 30, 255), 1.3)
    circ(d, 16, 16, 8, (222, 178, 118, 255)); circ(d, 16, 16, 5, (208, 160, 100, 255)); circ(d, 16, 16, 2, (222, 178, 118, 255))
    return fin(im, 32, 32)

def fence(horizontal=True):
    im = newc(32, 32); d = ImageDraw.Draw(im)
    if horizontal:
        rrect(d, 0, 12.5, 32, 19.5, (198, 142, 82, 255), (88, 56, 30, 255), 1)
        d.rectangle((0, 15 * S, 32 * S, 16.2 * S), fill=(224, 176, 112, 255))
        for x in (3, 29): rrect(d, x - 3, 10, x + 3, 22, (160, 108, 60, 255), (88, 56, 30, 255), 1.2)
    else:
        rrect(d, 12.5, 0, 19.5, 32, (198, 142, 82, 255), (88, 56, 30, 255), 1)
        d.rectangle((15 * S, 0, 16.2 * S, 32 * S), fill=(224, 176, 112, 255))
        for y in (3, 29): rrect(d, 10, y - 3, 22, y + 3, (160, 108, 60, 255), (88, 56, 30, 255), 1.2)
    return fin(im, 32, 32)

def bridge(horizontal=True):
    im = newc(32, 32); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 32 * S, 32 * S), fill=(88, 56, 30, 255))
    for i in range(4):
        a = i * 8
        if horizontal: rrect(d, a + 0.8, 4, a + 7.2, 28, (200, 146, 86, 255), (110, 72, 40, 255), 0.8, 0.6)
        else: rrect(d, 4, a + 0.8, 28, a + 7.2, (200, 146, 86, 255), (110, 72, 40, 255), 0.8, 0.6)
    if horizontal:
        d.rectangle((0, 0, 32 * S, 4 * S), fill=(150, 100, 56, 255)); d.rectangle((0, 28 * S, 32 * S, 32 * S), fill=(150, 100, 56, 255))
    else:
        d.rectangle((0, 0, 4 * S, 32 * S), fill=(150, 100, 56, 255)); d.rectangle((28 * S, 0, 32 * S, 32 * S), fill=(150, 100, 56, 255))
    return fin(im, 32, 32)

def lilypad():
    im = newc(32, 32); d = ImageDraw.Draw(im)
    d.ellipse((6 * S, 6 * S, 26 * S, 26 * S), fill=(80, 170, 84, 255), outline=(34, 92, 50, 255), width=int(1.3 * S))
    d.pieslice((6 * S, 6 * S, 26 * S, 26 * S), -20, 20, fill=(70, 160, 205, 255))
    circ(d, 13, 13, 2.2, (255, 160, 190, 255), (200, 90, 130, 255), 0.6)
    return fin(im, 32, 32)

def ruin_pillar():
    im = newc(32, 32); d = ImageDraw.Draw(im)
    circ(d, 16, 16, 13, (176, 176, 190, 255), (70, 70, 92, 255), 1.4)
    circ(d, 15, 15, 9, (208, 208, 220, 255)); circ(d, 15, 15, 4.5, (176, 176, 190, 255), (110, 110, 132, 255), 0.8)
    d.line([(20 * S, 8 * S), (23 * S, 14 * S), (21 * S, 19 * S)], fill=(90, 90, 112, 255), width=int(1.3 * S))
    return fin(im, 32, 32)

def arrow():
    im = newc(32, 32); d = ImageDraw.Draw(im)
    for off in (-5, 3):
        d.line([((11 + off) * S, 9 * S), ((19 + off) * S, 16 * S), ((11 + off) * S, 23 * S)], fill=(255, 245, 215, 210), width=int(3 * S), joint='curve')
    return fin(im, 32, 32)

def shadow(w):
    im = newc(w, w); d = ImageDraw.Draw(im)
    d.ellipse((w * .12 * S, w * .22 * S, w * .88 * S, w * .88 * S), fill=(20, 40, 20, 70))
    return fin(im, w, w).filter(ImageFilter.GaussianBlur(0.8))

def buildpad():
    im = newc(64, 64); d = ImageDraw.Draw(im)
    rrect(d, 5, 5, 59, 59, (126, 202, 84, 255), (160, 222, 112, 255), 10, 1.2)
    rrect(d, 8, 8, 56, 56, (118, 196, 78, 255), (104, 178, 68, 255), 8, 0.8)
    for x, y in [(8, 8), (56, 8), (8, 56), (56, 56)]:
        circ(d, x, y, 2.6, (176, 178, 190, 255), (92, 94, 112, 255), 0.8)
    return fin(im, 64, 64)

# ---------------------------------------------------------------- grid overlays (separate layer)
def ov(wc, hc, fill, border, bw, rad=8, cross=False, pad=2):
    w, h = wc * CELL, hc * CELL
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    box = (pad * S, pad * S, (w - pad) * S - 1, (h - pad) * S - 1)
    d.rounded_rectangle(box, radius=rad * S, fill=fill, outline=border, width=bw * S)
    if cross:
        c = (255, 235, 235, 200)
        for cx in range(wc):
            for cy in range(hc):
                x, y = cx * CELL + 32, cy * CELL + 32
                d.line([((x - 8) * S, (y - 8) * S), ((x + 8) * S, (y + 8) * S)], fill=c, width=4 * S)
                d.line([((x - 8) * S, (y + 8) * S), ((x + 8) * S, (y - 8) * S)], fill=c, width=4 * S)
    return im.resize((w, h), Image.LANCZOS)

def grid_line():
    im = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0)); px = im.load()
    for i in range(CELL):
        px[CELL - 1, i] = (24, 56, 24, 70); px[i, CELL - 1] = (24, 56, 24, 70)
        px[CELL - 2, i] = (255, 255, 255, 26); px[i, CELL - 2] = (255, 255, 255, 26)
    return im

def range_ring(rpx=124):
    sz = (rpx + 4) * 2; im = Image.new('RGBA', (sz * S, sz * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = sz * S // 2
    d.ellipse((c - rpx * S, c - rpx * S, c + rpx * S, c + rpx * S), fill=(255, 255, 255, 34), outline=(255, 255, 255, 210), width=3 * S)
    return im.resize((sz, sz), Image.LANCZOS)

STATES = {
    'available': dict(fill=(70, 230, 90, 92), border=(40, 200, 70, 200), bw=2),
    'selected': dict(fill=(120, 255, 130, 105), border=(214, 255, 214, 240), bw=3),
    'invalid': dict(fill=(232, 72, 72, 96), border=(206, 52, 52, 210), bw=2, cross=True),
    'occupied': dict(fill=(40, 28, 16, 70), border=(255, 224, 140, 150), bw=2),
}

# ================================================================= BUILD
manifest = {'tile_size': T, 'logical_cell': CELL, 'assets': {}}

grass_tiles = []
for i in range(1, 9):
    im = grass(i, dark=(i > 6)); grass_tiles.append(im); save(im, f'{G}/Ground/grassland_ground_{i:02d}.png')

path_idx, water_idx, path_tiles, water_tiles = {}, {}, [], []
for k, m in enumerate(MASKS):
    p = blob_tile(m, 'path'); wt = blob_tile(m, 'water')
    path_tiles.append(p); water_tiles.append(wt); path_idx[m] = k; water_idx[m] = k
    save(p, f'{G}/Paths/grassland_path_{k:02d}_m{m:03d}.png'); save(wt, f'{G}/Water/grassland_water_{k:02d}_m{m:03d}.png')

COLS = 8
atlas = Image.new('RGBA', (COLS * T, 13 * T), (0, 0, 0, 0))
for i, t in enumerate(grass_tiles): atlas.paste(t, ((i % COLS) * T, (i // COLS) * T))
for k, t in enumerate(path_tiles): atlas.paste(t, ((k % COLS) * T, (1 + k // COLS) * T))
for k, t in enumerate(water_tiles): atlas.paste(t, ((k % COLS) * T, (7 + k // COLS) * T))
save(atlas, f'{G}/grassland_tileset_32.png')
save(atlas.resize((atlas.width * 3, atlas.height * 3), Image.NEAREST), f'{G}/Preview/grassland_tileset_32_preview_3x.png')

meta = {'tileset': 'grassland_tileset_32.png', 'tile_size': T, 'columns': COLS,
        'rows': {'grass': 0, 'path_first_row': 1, 'water_first_row': 7},
        'bitmask': {'N': 1, 'E': 2, 'S': 4, 'W': 8, 'NE': 16, 'SE': 32, 'SW': 64, 'NW': 128,
                    'note': 'Corner bits only count if both adjacent edge bits are set. 47 unique tiles.'},
        'path_index_by_mask': {str(m): k for m, k in path_idx.items()},
        'water_index_by_mask': {str(m): k for m, k in water_idx.items()}}
json.dump(meta, open(f'{G}/grassland_tileset_32.json', 'w'), indent=1)

deco = {
    'Decorations/grassland_deco_flower_red_32': flower((236, 76, 96, 255), 1),
    'Decorations/grassland_deco_flower_yellow_32': flower((255, 220, 72, 255), 2),
    'Decorations/grassland_deco_flower_white_32': flower((250, 248, 250, 255), 3),
    'Decorations/grassland_deco_flower_blue_32': flower((110, 160, 255, 255), 4),
    'Decorations/grassland_deco_tuft_32': tuft(),
    'Decorations/grassland_deco_mushroom_32': mushroom(),
    'Decorations/grassland_deco_rock_small_32': rock(32, 5),
    'Decorations/grassland_deco_stump_32': stump(),
    'Decorations/grassland_deco_lilypad_32': lilypad(),
    'Decorations/grassland_deco_arrow_right_32': arrow(),
    'Objects/grassland_obj_bush_32': bush32(),
    'Objects/grassland_obj_fence_h_32': fence(True),
    'Objects/grassland_obj_fence_v_32': fence(False),
    'Objects/grassland_obj_bridge_h_32': bridge(True),
    'Objects/grassland_obj_bridge_v_32': bridge(False),
    'Objects/grassland_obj_ruin_pillar_32': ruin_pillar(),
    'Objects/grassland_obj_tree_64': tree64(),
    'Objects/grassland_obj_bush_64': bush64(),
    'Objects/grassland_obj_boulder_64': rock(64, 7, True),
    'Objects/grassland_obj_buildpad_64': buildpad(),
    'Effects/grassland_shadow_32': shadow(32),
    'Effects/grassland_shadow_64': shadow(64),
}
for name, im in deco.items(): save(im, f'{G}/{name}.png')
arrows = {k: deco['Decorations/grassland_deco_arrow_right_32'].rotate(a) for k, a in [('r', 0), ('u', 90), ('l', 180), ('d', 270)]}

# contact sheet for review
names = list(deco.keys()); cs = Image.new('RGBA', (8 * 80, 3 * 80), (112, 192, 72, 255))
for i, n in enumerate(names):
    im = deco[n]; cs.alpha_composite(im, ((i % 8) * 80 + (80 - im.width) // 2, (i // 8) * 80 + (80 - im.height) // 2))
save(cs.resize((cs.width * 2, cs.height * 2), Image.NEAREST), f'{G}/Preview/grassland_objects_contact_sheet.png')

# grid assets
grid = grid_line(); save(grid, f'{SH}/grid_line_64.png')
for st, kw in STATES.items():
    save(ov(1, 1, **kw), f'{SH}/grid_cell_{st}_64.png'); save(ov(2, 2, **kw), f'{SH}/grid_footprint_{st}_128.png')
ring = range_ring(); save(ring, f'{SH}/grid_range_ring_256.png')

# ---------------------------------------------------------------- logic map
COLSL, ROWSL = 20, 12
pts = [(0, 2), (4, 2), (4, 8), (9, 8), (9, 3), (14, 3), (14, 9), (19, 9)]
path_cells = []
for a, b in zip(pts, pts[1:]):
    dx, dy = (b[0] > a[0]) - (b[0] < a[0]), (b[1] > a[1]) - (b[1] < a[1])
    x, y = a
    while (x, y) != b:
        path_cells.append((x, y, dx, dy)); x += dx; y += dy
path_cells.append((*pts[-1], 1, 0))
PATH = {(x, y) for x, y, _, _ in path_cells}
WATER = {(x, y) for x in range(6, 9) for y in range(4, 7)} | {(x, y) for x in range(16, 19) for y in range(5, 8)}
TREES = [(1, 0), (2, 0), (7, 0), (11, 0), (13, 0), (17, 0), (18, 0), (0, 5), (0, 6), (1, 10), (2, 11), (7, 10), (11, 11), (19, 5), (19, 6), (5, 0)]
BOULDERS = [(5, 5), (12, 6), (10, 10), (15, 1), (2, 7)]
BUSHES = [(6, 8 + 2), (16, 10), (3, 5)]
FENCE = [(14, 11), (15, 11), (16, 11)]
BLOCKED = set(TREES) | set(BOULDERS) | set(BUSHES) | set(FENCE)
cells = []
for y in range(ROWSL):
    row = []
    for x in range(COLSL):
        if (x, y) in PATH: t = 'path'
        elif (x, y) in WATER: t = 'water'
        elif (x, y) in BLOCKED: t = 'blocked'
        else: t = 'buildable'
        row.append(t)
    cells.append(row)
logic = {'name': 'grassland_01', 'cell_px': CELL, 'cols': COLSL, 'rows': ROWSL, 'cells': cells,
         'occupancy': [[None] * COLSL for _ in range(ROWSL)],
         'enemy_path': [[x, y] for x, y, _, _ in path_cells],
         'grid_visibility': 'default',
         'note': 'Logic only. Rendering reads this; hiding the grid never changes it.'}
json.dump(logic, open(f'{G}/map_grassland_01.json', 'w'))

# ---------------------------------------------------------------- render layers
TW, TH = COLSL * 2, ROWSL * 2; PW, PH = COLSL * CELL, ROWSL * CELL
rr = random.Random(42)
ground = Image.new('RGBA', (PW, PH))
for ty in range(TH):
    for tx in range(TW):
        ground.paste(grass_tiles[rr.choice([0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3])], (tx * T, ty * T))
def tileset_of(cellset):
    ts = set()
    for (x, y) in cellset:
        for a in (0, 1):
            for b in (0, 1): ts.add((x * 2 + a, y * 2 + b))
    return ts
def blob_layer(ts, tiles, idx):
    lay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    def has(x, y):
        if x < 0 or y < 0 or x >= TW or y >= TH: return True
        return (x, y) in ts
    for (x, y) in ts:
        m = 0
        for bit, (dx, dy) in [(N, (0, -1)), (E, (1, 0)), (S_, (0, 1)), (W, (-1, 0)), (NE, (1, -1)), (SE, (1, 1)), (SW, (-1, 1)), (NW, (-1, -1))]:
            if has(x + dx, y + dy): m |= bit
        lay.alpha_composite(tiles[idx[canon(m)]], (x * T, y * T))
    return lay
path_layer = blob_layer(tileset_of(PATH), path_tiles, path_idx)
water_layer = blob_layer(tileset_of(WATER), water_tiles, water_idx)
# path direction decals
decal = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
for i, (x, y, dx, dy) in enumerate(path_cells):
    if i % 2 == 0 and 0 < i < len(path_cells) - 1:
        k = {(1, 0): 'r', (-1, 0): 'l', (0, 1): 'd', (0, -1): 'u'}[(dx, dy)]
        decal.alpha_composite(arrows[k], (x * CELL + 16, y * CELL + 16))
# objects layer
obj = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
sh32, sh64 = deco['Effects/grassland_shadow_32'], deco['Effects/grassland_shadow_64']
def place(sprite, shd, cx, cy, ox=0, oy=0):
    if shd: obj.alpha_composite(shd, (cx * CELL + ox + 2, cy * CELL + oy + 4))
    obj.alpha_composite(sprite, (cx * CELL + ox, cy * CELL + oy))
for c in TREES: place(deco['Objects/grassland_obj_tree_64'], sh64, *c)
for c in BOULDERS: place(deco['Objects/grassland_obj_boulder_64'], sh64, *c)
for c in BUSHES: place(deco['Objects/grassland_obj_bush_64'], sh64, *c)
for c in FENCE:
    obj.alpha_composite(deco['Objects/grassland_obj_fence_h_32'], (c[0] * CELL, c[1] * CELL + 16))
    obj.alpha_composite(deco['Objects/grassland_obj_fence_h_32'], (c[0] * CELL + 32, c[1] * CELL + 16))
for (x, y) in [(7, 5)]:
    obj.alpha_composite(deco['Decorations/grassland_deco_lilypad_32'], (x * CELL + 8, y * CELL + 8))
obj.alpha_composite(deco['Decorations/grassland_deco_lilypad_32'], (17 * CELL + 20, 6 * CELL + 10))
# small ground decor (cosmetic; may sit under towers)
small = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
keys = ['flower_red', 'flower_yellow', 'flower_white', 'flower_blue', 'tuft', 'tuft', 'mushroom', 'rock_small', 'stump']
used = set()
for _ in range(110):
    tx, ty = rr.randrange(TW), rr.randrange(TH); cx, cy = tx // 2, ty // 2
    if (tx, ty) in used or cells[cy][cx] in ('path', 'water') or (cx, cy) in BLOCKED: continue
    k = rr.choice(keys)
    if k in ('mushroom', 'rock_small', 'stump') and cells[cy][cx] != 'buildable' and False: continue
    near_path = any((cx + a, cy + b) in PATH or (cx + a, cy + b) in WATER for a in (-1, 0, 1) for b in (-1, 0, 1))
    if k in ('mushroom', 'rock_small', 'stump') and near_path: continue
    used.add((tx, ty)); small.alpha_composite(deco[f'Decorations/grassland_deco_{k}_32'], (tx * T, ty * T))
# grid layer
gridlay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
for y in range(ROWSL):
    for x in range(COLSL): gridlay.alpha_composite(grid, (x * CELL, y * CELL))
# placement layer
def cellov(layer, wc, hc, st, x, y): layer.alpha_composite(ov(wc, hc, **STATES[st]), (x * CELL, y * CELL))
place_lay = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
for y in range(ROWSL):
    for x in range(COLSL):
        if cells[y][x] == 'buildable' and any((x + a, y + b) in PATH for a in (-1, 0, 1) for b in (-1, 0, 1)):
            cellov(place_lay, 1, 1, 'available', x, y)
cellov(place_lay, 2, 2, 'occupied', 2, 3)
ghost = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
ghost.alpha_composite(ring, (12 * CELL - ring.width // 2, 5 * CELL - ring.height // 2))
cellov(ghost, 2, 2, 'selected', 11, 4)
cellov(ghost, 2, 2, 'invalid', 13, 2)

def compose(layers):
    im = Image.new('RGBA', (PW, PH))
    for l in layers: im.alpha_composite(l)
    return im.convert('RGB')
base = [ground, water_layer, path_layer, decal, small, obj]
P = f'{G}/Preview'
os.makedirs(f'{P}/layers', exist_ok=True)
compose(base).save(f'{P}/prototype_grid_hidden.png')
compose(base + [gridlay]).save(f'{P}/prototype_grid_default.png')
compose(base + [gridlay, place_lay, ghost]).save(f'{P}/prototype_placement_states.png')
for n, l in [('1_ground', ground), ('2_water', water_layer), ('3_path', path_layer), ('4_path_decals', decal),
             ('5_small_decor', small), ('6_objects', obj), ('7_grid', gridlay), ('8_placement', place_lay), ('9_ghost_range', ghost)]:
    l.save(f'{P}/layers/layer_{n}.png')
print('ok', len(MASKS), PW, PH)
