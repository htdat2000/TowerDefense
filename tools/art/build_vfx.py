"""Phase 5 - Gameplay VFX library. Same pipeline as the other scripts: draw at S=4, LANCZOS downscale, one outline colour.
Outputs: Projectiles/*.png (single frame, face EAST), VFX/vfx_*.png (horizontal strips), Documentation/vfx_atlas.json,
VFX/Preview/DEMO_*.gif + vfx_overview.png (review only, never go to res://)."""
import os, math, random, json
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4
ROOT = '/mnt/user-data/outputs/GameAssets'
OUT = (52, 40, 50, 255)
for p in ('Projectiles', 'VFX', 'VFX/Preview', 'Documentation'): os.makedirs(f'{ROOT}/{p}', exist_ok=True)
try: FONT = ImageFont.load_default(size=13)
except Exception: FONT = ImageFont.load_default()

# ------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def sm(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def cv(w, h=None): return Image.new('RGBA', (w * S, (h or w) * S), (0, 0, 0, 0))
def fin(im, w, h=None): return im.resize((w, h or w), Image.LANCZOS)
def comp(*ims):
    o = Image.new('RGBA', ims[0].size, (0, 0, 0, 0))
    for i in ims: o.alpha_composite(i)
    return o
def fade(im, a):
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a))); return im
def strip(frames):
    w, h = frames[0].size; s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames): s.paste(f, (i * w, 0))
    return s
def mix(c1, c2, t): return tuple(int(lerp(a, b, clamp(t))) for a, b in zip(c1, c2))
def ramp(stops, t):
    t = clamp(t) * (len(stops) - 1); i = min(int(t), len(stops) - 2); return mix(stops[i], stops[i + 1], t - i)
def circ(d, cx, cy, r, fill, out=OUT, ow=1.0):
    if out: d.ellipse(((cx - r - ow) * S, (cy - r - ow) * S, (cx + r + ow) * S, (cy + r + ow) * S), fill=out)
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=fill)
def poly(d, pts, fill, out=OUT, ow=1.0):
    q = [(x * S, y * S) for x, y in pts]
    if fill is not None: d.polygon(q, fill=fill)
    if out: d.line(q + [q[0]], fill=out, width=max(1, int(ow * S)), joint='curve')
def line(d, p, q, col, w): d.line((p[0] * S, p[1] * S, q[0] * S, q[1] * S), fill=col, width=max(1, int(w * S)))
def pl(d, pts, col, w): d.line([(x * S, y * S) for x, y in pts], fill=col, width=max(1, int(w * S)), joint='curve')
def arc(d, cx, cy, r, a0, a1, col, w): d.arc(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), a0, a1, fill=col, width=max(1, int(w * S)))
def blob(im, x, y, r, col, rx=None):
    t = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(t).ellipse(((x - r) * S, (y - (rx or r)) * S, (x + r) * S, (y + (rx or r)) * S), fill=col); im.alpha_composite(t)
def glow(w, h, cx, cy, r, col, a):
    r = min(r, min(w, h) / 2 / 2.5)  # keep blur inside canvas (no clipped box edges)
    l = cv(w, h); ImageDraw.Draw(l).ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=col + (int(a),))
    return l.filter(ImageFilter.GaussianBlur(r * S * 0.45))
def star4(d, x, y, r, col, out=None, ow=0.7, k=0.38):
    pts = [(x + math.cos(math.radians(j * 45 - 90)) * (r if j % 2 == 0 else r * k), y + math.sin(math.radians(j * 45 - 90)) * (r if j % 2 == 0 else r * k)) for j in range(8)]
    poly(d, pts, col, out, ow)
def spark(d, x, y, r, col): star4(d, x, y, r, col, None)
def zig(p, q, rng, seg=5, amp=3.0):
    pts = [p]; dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
    for k in range(1, seg):
        u = k / seg; o = rng.uniform(-amp, amp); pts.append((p[0] + dx * u + nx * o, p[1] + dy * u + ny * o))
    pts.append(q); return pts
def leaf(d, x, y, ang, ln, wd, col, out=(34, 88, 42, 255)):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a); pts = []
    for k in range(12):
        u = k / 11 * math.pi; px, py = (1 - math.cos(u)) / 2 * ln, math.sin(u) * wd / 2
        pts.append((x + px * c - py * s, y + px * s + py * c))
    for k in range(12):
        u = k / 11 * math.pi; px, py = (1 + math.cos(u)) / 2 * ln, -math.sin(u) * wd / 2
        pts.append((x + px * c - py * s, y + px * s + py * c))
    poly(d, pts, col, out, 0.8)
def coin(d, x, y, r, sx=1.0):
    rx = max(0.5, r * abs(sx))
    d.ellipse(((x - rx - 1) * S, (y - r - 1) * S, (x + rx + 1) * S, (y + r + 1) * S), fill=OUT)
    d.ellipse(((x - rx) * S, (y - r) * S, (x + rx) * S, (y + r) * S), fill=(255, 210, 84, 255))
    if rx > 2: d.ellipse(((x - rx * .62) * S, (y - r * .62) * S, (x + rx * .62) * S, (y + r * .62) * S), fill=(255, 232, 140, 255), outline=(214, 150, 40, 255), width=int(0.7 * S))

FIRE = [(255, 246, 180), (255, 196, 64), (244, 104, 40), (150, 52, 44)]
BLUE, BLUE_L, BLUE_D = (110, 170, 255, 255), (230, 245, 255, 255), (60, 100, 220, 255)
PG, PG_L, PG_D = (110, 204, 70, 255), (190, 240, 120, 255), (50, 128, 50, 255)
MG, MG_L, MG_D = (170, 110, 240, 255), (236, 204, 255, 255), (96, 52, 176, 255)
ICE, ICE_L, ICE_D = (140, 218, 252, 255), (226, 248, 255, 255), (64, 142, 222, 255)
BK, BK_D = (124, 84, 54, 255), (66, 42, 30, 255)
GOLD = (255, 210, 84, 255)

REG = {}   # name -> atlas entry
def reg(name, group, frames, fps, loop, folder='VFX', note='', tint=False, event=None, pivot=None, hold=False):
    w, h = frames[0].size
    path = f'{ROOT}/{folder}/{"" if folder == "Projectiles" else "vfx_"}{name}.png'
    (frames[0] if len(frames) == 1 else strip(frames)).save(path)
    REG[name] = dict(file=os.path.relpath(path, ROOT), group=group, frames=len(frames), frame_w=w, frame_h=h, fps=fps, loop=loop,
                     duration_s=round(len(frames) / fps, 3) if fps else 0, pivot=pivot or [w // 2, h // 2], tintable=tint,
                     event_frame=event, note=note)
    return frames
def fx(n, w, h, fn, loop=False):
    return [fin(fn((i / n) if loop else (i / (n - 1)), i), w, h) for i in range(n)]

# ============================================================ PROJECTILES (face EAST)
def p_fireball():
    im = cv(32); d = ImageDraw.Draw(im); im = comp(glow(32, 32, 20, 16, 11, (255, 140, 40), 130)); d = ImageDraw.Draw(im)
    poly(d, [(2, 16), (11, 8.5), (24, 7), (24, 25), (11, 23.5)], (244, 104, 40, 255), (150, 52, 44, 255), 1.0)
    poly(d, [(7, 16), (14, 11.5), (22, 11), (22, 21), (14, 20.5)], (255, 196, 64, 255), None)
    circ(d, 21, 16, 7.4, (255, 150, 50, 255), (150, 52, 44, 255), 1.2); circ(d, 21.5, 16, 4.6, (255, 226, 120, 255), None); circ(d, 22.5, 15, 2.2, (255, 255, 230, 255), None)
    return fin(im, 32)
def p_lightning():
    im = cv(48, 16); rng = random.Random(3); pts = zig((3, 8), (45, 8), rng, 7, 3.4); d = ImageDraw.Draw(im)
    im = comp(glow(48, 16, 24, 8, 9, (110, 170, 255), 120)); d = ImageDraw.Draw(im)
    pl(d, pts, BLUE_D, 4.4); pl(d, pts, BLUE, 2.8); pl(d, pts, (255, 255, 235, 255), 1.1); spark(d, 45, 8, 3.5, (255, 255, 235, 255))
    return fin(im, 48, 16)
def p_poison():
    im = cv(32); d = ImageDraw.Draw(im)
    poly(d, [(3, 16), (11, 11), (11, 21)], PG, PG_D, 1.0)
    circ(d, 18, 16, 8.4, PG, PG_D, 1.3); circ(d, 15.5, 13, 3.0, PG_L, None); circ(d, 21.5, 19, 1.8, (74, 160, 60, 255), None)
    circ(d, 24, 11, 2.4, PG_L, PG_D, 0.7); circ(d, 12, 22, 1.5, PG_L, PG_D, 0.6); circ(d, 14, 12.2, 1.1, (255, 255, 255, 220), None)
    return fin(im, 32)
def p_cannonball():
    im = cv(32); d = ImageDraw.Draw(im)
    circ(d, 16, 16, 8.2, (74, 76, 92, 255), OUT, 1.4); circ(d, 14.5, 14.5, 5.4, (104, 108, 128, 255), None)
    circ(d, 13, 12.8, 2.4, (190, 196, 214, 255), None); arc(d, 16, 16, 6.4, 20, 80, (46, 48, 62, 255), 1.2)
    return fin(im, 32)
def p_magic():
    im = comp(cv(32), glow(32, 32, 16, 16, 13, (180, 120, 255), 150)); d = ImageDraw.Draw(im)
    circ(d, 16, 16, 7.2, MG, MG_D, 1.3); circ(d, 16, 16, 4.6, MG_L, None); circ(d, 14.5, 14.4, 1.8, (255, 255, 255, 255), None)
    arc(d, 16, 16, 10.5, 200, 330, MG_L, 1.1); arc(d, 16, 16, 10.5, 20, 150, MG_L, 1.1)
    star4(d, 27, 7, 2.6, (255, 255, 255, 255)); star4(d, 6, 25, 2.0, MG_L)
    return fin(im, 32)
def p_nature():
    im = cv(32, 16); d = ImageDraw.Draw(im)
    poly(d, [(3, 8), (10, 3.5), (21, 3.2), (27, 8), (21, 12.8), (10, 12.5)], (84, 168, 70, 255), (34, 88, 42, 255), 1.2)
    poly(d, [(6, 8), (11, 5), (21, 4.8), (24, 8)], (152, 218, 98, 255), None); line(d, (5, 8), (24, 8), (46, 122, 58, 255), 0.9)
    poly(d, [(31, 8), (24, 5.2), (24, 10.8)], (240, 226, 190, 255), OUT, 0.9)
    for sy in (-1, 1): poly(d, [(14, 8 + sy * 4.5), (17, 8 + sy * 7), (19, 8 + sy * 4.3)], (240, 226, 190, 255), OUT, 0.6)
    return fin(im, 32, 16)
def p_sniper():
    im = cv(48, 12); d = ImageDraw.Draw(im)
    for k, a in enumerate((40, 90, 150)): line(d, (2 + k * 4, 6), (22, 6), (255, 255, 255, a), 1.6 - k * 0.3)
    poly(d, [(44, 6), (36, 3.2), (22, 3.2), (22, 8.8), (36, 8.8)], (226, 176, 70, 255), OUT, 1.1)
    poly(d, [(44, 6), (38, 4.2), (38, 7.8)], (200, 204, 216, 255), OUT, 0.8); line(d, (24, 4.4), (36, 4.4), (255, 240, 180, 255), 0.9)
    line(d, (30, 3.2), (30, 8.8), (150, 100, 40, 255), 0.9)
    return fin(im, 48, 12)
for n, f, note in [('fireball', p_fireball, 'Fire tower'), ('lightning_bolt', p_lightning, 'Lightning tower, 48x16'), ('poison_glob', p_poison, 'Poison tower'),
                   ('cannonball', p_cannonball, 'Cannon tower'), ('magic_orb', p_magic, 'Arcane tower'), ('nature_seed', p_nature, 'Nature tower (thorn seed), 32x16'),
                   ('sniper_round', p_sniper, 'Sniper tower, 48x12 (pair with vfx_arrow_impact or vfx_magical_burst scaled down)')]:
    reg('projectile_' + n if False else n, 'projectile', [f()], 0, False, folder='Projectiles', note=note + '. Faces EAST; engine rotates by travel angle.')
# rename files to projectile_<name>.png
for n in list(REG):
    if REG[n]['group'] == 'projectile':
        old = f'{ROOT}/Projectiles/{n}.png'; new = f'{ROOT}/Projectiles/projectile_{n}.png'; os.replace(old, new); REG[n]['file'] = f'Projectiles/projectile_{n}.png'

# ============================================================ IMPACTS
def fire_blobs(im, c, t, n, spread, rad0, rad1, seed, stops=FIRE, fadeat=0.6):
    r = random.Random(seed)
    for k in range(n):
        a = k / n * 6.283 + r.random() * 0.5; q = (3 + t * spread) * r.uniform(0.65, 1.0); rad = lerp(rad0, rad1, sm(0, 0.5, t)) * r.uniform(0.8, 1.15)
        al = int(255 * (1 - sm(fadeat, 1.0, t))); col = ramp(stops, t * 0.9 + r.random() * 0.1)
        blob(im, c + math.cos(a) * q, c + math.sin(a) * q, rad + 1.3, (110, 36, 40, int(al * 0.8)))
        blob(im, c + math.cos(a) * q, c + math.sin(a) * q, rad, col + (al,))
def embers(d, c, t, n, seed, spread, col=(255, 226, 120, 255), s=1.6):
    r = random.Random(seed)
    for _ in range(n):
        a = r.random() * 6.283; q = 6 + t * spread * r.uniform(0.5, 1); circ(d, c + math.cos(a) * q, c + math.sin(a) * q, s * (1 - t * 0.6), col, None)
def i_fire(t, i):
    W = 80; c = W / 2; im = cv(W)
    fire_blobs(im, c, t, 9, 20, 8, 15, 5)
    blob(im, c, c, lerp(14, 8, t), ramp(FIRE, t * 0.8) + (int(255 * (1 - sm(0.55, 1, t))),))
    d = ImageDraw.Draw(im); embers(d, c, t, 12, 7, 32)
    if t < 0.3: circ(d, c, c, 16 * (1 - t / 0.3) + 4, (255, 255, 235, 255), None)
    return im
def i_cannon(t, i):
    W = 96; c = W / 2; im = cv(W)
    fire_blobs(im, c, t * 0.9, 11, 26, 10, 18, 9)
    r = random.Random(4)
    for k in range(8):
        a = k / 8 * 6.283 + 0.3; q = 10 + sm(0.25, 1, t) * 32; blob(im, c + math.cos(a) * q, c + math.sin(a) * q, 5 + 8 * sm(0.3, 1, t), (96, 88, 96, int(190 * (1 - sm(0.55, 1, t)))))
    d = ImageDraw.Draw(im)
    arc(d, c, c, 6 + t * 40, 0, 360, (255, 244, 200, int(230 * (1 - t))), 3 * (1 - t) + 1)
    for k in range(8):
        a = r.random() * 6.283; q = 8 + t * r.uniform(20, 38); circ(d, c + math.cos(a) * q, c + math.sin(a) * q, 2.4 * (1 - t * .4), (92, 70, 56, 255), OUT, 0.8)
    if t < 0.3: circ(d, c, c, 20 * (1 - t / 0.3) + 4, (255, 255, 235, 255), None)
    return im
def i_lightning(t, i):
    W = 64; c = W / 2; im = comp(cv(W), glow(W, W, c, c, 14 * (1 - t) + 4, (110, 170, 255), 170 * (1 - t))); d = ImageDraw.Draw(im); r = random.Random(20 + i)
    for k in range(6):
        a = k / 6 * 6.283 + 0.3; L = 8 + t * 22; pts = zig((c, c), (c + math.cos(a) * L, c + math.sin(a) * L), r, 4, 2.6)
        al = int(255 * (1 - sm(0.4, 1, t))); pl(d, pts, (60, 100, 220, al), 3.4 * (1 - t * .5)); pl(d, pts, (255, 255, 235, al), 1.2)
    arc(d, c, c, 5 + t * 24, 0, 360, (150, 200, 255, int(220 * (1 - t))), 2.4 * (1 - t) + 0.8)
    if t < 0.5: circ(d, c, c, 9 * (1 - t * 1.8) + 2, (255, 255, 240, 255), None)
    embers(d, c, t, 8, 11, 26, (255, 255, 200, 255), 1.4)
    return im
def i_poison(t, i):
    W = 64; c = W / 2; im = cv(W); al = int(210 * (1 - sm(0.55, 1, t)))
    pr = 5 + 17 * sm(0, 0.7, t); blob(im, c, c, pr + 1.2, PG_D[:3] + (al,), rx=pr * 0.9 + 1.2); blob(im, c, c, pr, PG[:3] + (al,), rx=pr * 0.9)
    blob(im, c - pr * .25, c - pr * .3, pr * .5, PG_L[:3] + (int(al * .7),)); d = ImageDraw.Draw(im); r = random.Random(6)
    for k in range(10):
        a = k / 10 * 6.283 + r.random() * .4; q = 4 + 22 * (t ** 0.6) * r.uniform(0.6, 1); sz = 3 * (1 - t * .5) * r.uniform(.7, 1.2)
        if t < 0.85: circ(d, c + math.cos(a) * q, c + math.sin(a) * q, sz, PG, PG_D, 0.8)
    for k in range(4):
        u = clamp(t * 1.2 - k * 0.1)
        if 0.3 < u < 0.9: circ(d, c + math.cos(k * 1.9) * 9, c + math.sin(k * 1.9) * 7, 1.5 + u * 2, PG_L[:3] + (0,), (190, 240, 120, int(220 * (1 - u))), 0.9)
    return im
def i_magic(t, i):
    W = 64; c = W / 2; im = comp(cv(W), glow(W, W, c, c, 16 * (1 - t * .5) + 4, (180, 120, 255), 170 * (1 - t))); d = ImageDraw.Draw(im)
    arc(d, c, c, 5 + t * 24, 0, 360, MG[:3] + (int(240 * (1 - t)),), 3.2 * (1 - t) + 0.8)
    arc(d, c, c, 3 + t * 15, 0, 360, MG_L[:3] + (int(240 * (1 - t)),), 1.6)
    for k in range(8):
        a = math.radians(k * 45 + 10 + t * 40); L0, L1 = 6 + t * 10, 10 + t * 20; line(d, (c + math.cos(a) * L0, c + math.sin(a) * L0), (c + math.cos(a) * L1, c + math.sin(a) * L1), MG_L[:3] + (int(255 * (1 - t)),), 1.6)
    for k in range(5):
        a = k / 5 * 6.283 + 0.6; q = 8 + t * 20; star4(d, c + math.cos(a) * q, c + math.sin(a) * q, 3.8 * (1 - t * .5), (255, 255, 255, 255), MG_D, 0.5)
    if t < 0.4: circ(d, c, c, 9 * (1 - t / 0.4) + 2, (255, 255, 255, 255), None)
    return im
def i_nature(t, i):
    W = 64; c = W / 2; im = cv(W); u = math.sin(math.pi * clamp(t * 1.05)) ; al = int(255 * (1 - sm(0.7, 1, t))); d = ImageDraw.Draw(im); r = random.Random(12)
    blob(im, c, c, 9 + 6 * u, (84, 60, 40, int(150 * (1 - sm(.6, 1, t)))), rx=(9 + 6 * u) * .85)
    for k in range(7):
        a = k / 7 * 6.283 + 0.2; L = (10 + r.random() * 6) * (0.2 + 0.8 * u) + 4; cur = r.choice([-1, 1]) * 0.5; pts = []
        for s in range(9):
            q = s / 8 * L; aa = a + cur * (s / 8); pts.append((c + math.cos(aa) * q, c + math.sin(aa) * q))
        if al > 0:
            pl(d, pts, (66, 42, 30, al), 4.4); pl(d, pts, (124, 84, 54, al), 2.8); pl(d, pts, (160, 114, 76, al), 0.9)
            if u > 0.5: leaf(d, pts[-1][0], pts[-1][1], math.degrees(a + cur), 7 * u, 4 * u, (84, 168, 70, al), (34, 88, 42, al))
    for k in range(5):
        a = r.random() * 6.283; q = 6 + t * 22; leaf(d, c + math.cos(a) * q, c + math.sin(a) * q, math.degrees(a) + t * 200, 4.5, 2.6, (152, 218, 98, int(255 * (1 - sm(.5, 1, t)))), (34, 88, 42, int(255 * (1 - sm(.5, 1, t)))))
    return im
reg('fire_explosion', 'impact', fx(8, 80, 80, i_fire), 16, False, note='Fire tower hit, area burst. Spawn at target position.')
reg('lightning_impact', 'impact', fx(6, 64, 64, i_lightning), 18, False, note='Lightning tower hit / chain link end.')
reg('poison_splash', 'impact', fx(7, 64, 64, i_poison), 14, False, note='Poison hit; puddle can be kept by engine for DoT zone.')
reg('magical_burst', 'impact', fx(8, 64, 64, i_magic), 16, False, note='Arcane tower hit.')
reg('nature_root_impact', 'impact', fx(8, 64, 64, i_nature), 14, False, note='Nature tower hit; roots erupt and retract (root/slow).')
reg('cannon_explosion', 'impact', fx(9, 96, 96, i_cannon), 16, False, note='Cannon tower hit, splash. Engine may shake camera on frame 1.')

# ============================================================ STATUS OVERLAYS (64px, loop, centred on monster; scale in engine for big monsters)
def s_freeze(t, i):
    c = 32; im = cv(64); blob(im, c, c, 24, (170, 226, 252, 70)); d = ImageDraw.Draw(im)
    arc(d, c, c, 23, 0, 360, (36, 96, 180, 230), 1.6); arc(d, c, c, 21.2, 0, 360, (226, 248, 255, 200), 1.0)
    for k in range(8):
        a = math.radians(k * 45 + 22.5); u = (math.cos(a), math.sin(a)); v = (-u[1], u[0]); b = 20; h = 7 + (k % 2) * 3
        poly(d, [(c + u[0] * (b + h), c + u[1] * (b + h)), (c + u[0] * b + v[0] * 3.4, c + u[1] * b + v[1] * 3.4), (c + u[0] * (b - 2), c + u[1] * (b - 2)), (c + u[0] * b - v[0] * 3.4, c + u[1] * b - v[1] * 3.4)], ICE, (36, 96, 180, 255), 0.9)
        poly(d, [(c + u[0] * (b + h), c + u[1] * (b + h)), (c + u[0] * b + v[0] * 3.4, c + u[1] * b + v[1] * 3.4), (c + u[0] * (b - 2), c + u[1] * (b - 2))], ICE_L, None)
    for k in range(4):
        al = int(255 * max(0, math.sin((t + k / 4) * 6.283)) ** 2); a = k * 1.7 + 0.5
        spark(d, c + math.cos(a) * 12, c + math.sin(a) * 12, 3.6, (255, 255, 255, al))
    return im
def s_burn(t, i):
    c = 32; im = cv(64); blob(im, c, c, 22, (255, 120, 40, 40)); d = ImageDraw.Draw(im)
    for k in range(8):
        a = math.radians(k * 45 + 8); ph = (t + k * 0.37) % 1.0; fl = 0.75 + 0.25 * math.sin(ph * 6.283); L = 11 * fl + 4
        x, y = c + math.cos(a) * 18, c + math.sin(a) * 18; u = (math.cos(a), math.sin(a)); v = (-u[1], u[0])
        tip = (x + u[0] * L + v[0] * math.sin(ph * 6.283) * 1.5, y + u[1] * L + v[1] * math.sin(ph * 6.283) * 1.5)
        poly(d, [tip, (x + v[0] * 4.6, y + v[1] * 4.6), (x - u[0] * 3, y - u[1] * 3), (x - v[0] * 4.6, y - v[1] * 4.6)], (244, 104, 40, 255), (150, 52, 44, 255), 0.8)
        poly(d, [(x + u[0] * L * .62, y + u[1] * L * .62), (x + v[0] * 2.4, y + v[1] * 2.4), (x - u[0] * 1.5, y - u[1] * 1.5), (x - v[0] * 2.4, y - v[1] * 2.4)], (255, 214, 80, 255), None)
    for k in range(6):
        u2 = (t + k / 6) % 1.0; a = k * 1.05 + 0.4; q = 16 + u2 * 12; circ(d, c + math.cos(a) * q, c + math.sin(a) * q, 1.4 * (1 - u2 * .5), (255, 220, 120, int(255 * (1 - u2))), None)
    return im
def s_poison(t, i):
    c = 32; im = cv(64); blob(im, c, c, 23, (120, 210, 70, 85)); d = ImageDraw.Draw(im)
    arc(d, c, c, 22, 0, 360, (60, 150, 50, 230), 1.8)
    for k in range(7):
        u = (t + k / 7) % 1.0; a = k * 0.9 + 0.3; q = 8 + u * 15; rr = 1.6 + 2.6 * u
        circ(d, c + math.cos(a) * q, c + math.sin(a) * q, rr, (150, 226, 100, int(200 * (1 - u * u))), (50, 128, 50, int(255 * (1 - u * u))), 0.8)
        if u < 0.85: circ(d, c + math.cos(a) * q - rr * .3, c + math.sin(a) * q - rr * .3, rr * .25, (255, 255, 255, int(220 * (1 - u))), None)
    return im
def s_slow(t, i):
    c = 32; im = cv(64); blob(im, c, c, 24, (110, 130, 255, 40)); d = ImageDraw.Draw(im)
    rot = t * 120
    for k in range(3): arc(d, c, c, 22, rot + k * 120, rot + k * 120 + 70, (40, 60, 160, 255), 4.2)
    for k in range(3): arc(d, c, c, 22, rot + k * 120, rot + k * 120 + 70, (130, 160, 255, 255), 2.6)
    for k in range(3): arc(d, c, c, 15, -rot * 1.5 + k * 120, -rot * 1.5 + k * 120 + 50, (190, 210, 255, 220), 1.6)
    for k in range(3):
        a = math.radians(rot + k * 120 + 90); x, y = c + math.cos(a) * 22, c + math.sin(a) * 22
        circ(d, x, y, 2.2, (190, 210, 255, 255), (40, 60, 160, 255), 0.7)
    return im
def s_stun(t, i):
    c = 32; im = cv(64); d = ImageDraw.Draw(im); items = []
    for k in range(3):
        a = math.radians(t * 120 + k * 120); items.append((math.sin(a), c + math.cos(a) * 17, c + math.sin(a) * 9 - 6))
    for z, x, y in sorted(items): star4(d, x, y, 5.6 + z * 1.0, (255, 224, 90, 255), (190, 120, 30, 255), 0.9, 0.42)
    arc(d, c, c - 6, 17, 0, 360, (255, 240, 170, 60), 1.0)
    return im
reg('status_freeze', 'status', fx(8, 64, 64, s_freeze, True), 10, True, note='Overlay above monster; scale to monster frame (64/80/96). Add engine tint/slowdown.')
reg('status_burning', 'status', fx(8, 64, 64, s_burn, True), 12, True, note='Burning DoT overlay.')
reg('status_poison', 'status', fx(8, 64, 64, s_poison, True), 10, True, note='Poison DoT overlay.')
reg('status_slow', 'status', fx(8, 64, 64, s_slow, True), 10, True, note='Slow overlay (also use for root slow).')
reg('status_stun', 'status', fx(8, 64, 64, s_stun, True), 10, True, note='Stun stars (optional status).')

# ============================================================ TOWER EFFECTS (96px)
def t_spawn(t, i):
    c = 48; im = cv(96); d = ImageDraw.Draw(im); r = random.Random(2)
    for k in range(10):
        a = k / 10 * 6.283 + r.random() * .3; q = 10 + sm(0, 1, t) * 32 * r.uniform(.7, 1); blob(im, c + math.cos(a) * q, c + math.sin(a) * q, 4 + 5 * t, (240, 236, 226, int(200 * (1 - sm(.35, 1, t)))))
    d = ImageDraw.Draw(im)
    for k in range(8):
        a = k / 8 * 6.283 + 0.2; q = 8 + t * 34; spark(d, c + math.cos(a) * q, c + math.sin(a) * q - t * 6, 3.4 * (1 - t * .6), (255, 232, 140, int(255 * (1 - sm(.5, 1, t)))))
    return im
def t_destroy(t, i):
    c = 48; im = cv(96); r = random.Random(8)
    for k in range(9):
        a = r.random() * 6.283; q = 6 + sm(0.1, 1, t) * r.uniform(14, 36); blob(im, c + math.cos(a) * q, c + math.sin(a) * q - t * 8, 5 + 9 * t, (110, 104, 100, int(190 * (1 - sm(.4, 1, t)))))
    d = ImageDraw.Draw(im)
    for k in range(14):
        a = r.random() * 6.283; q = 8 + (t ** 0.6) * r.uniform(16, 42); sz = r.uniform(2, 4.2); col = r.choice([(150, 154, 172, 255), (178, 122, 70, 255), (118, 76, 44, 255)])
        if t < 0.92: circ(d, c + math.cos(a) * q, c + math.sin(a) * q + t * t * 10, sz, col, OUT, 0.8)
    return im
def t_upgrade(t, i):
    c = 48; im = cv(96); n = 12; ph = i
    if ph < 4:
        u = ph / 3; im = comp(im, glow(96, 96, c, c, 10 + u * 22, (255, 220, 110), 80 + 120 * u)); d = ImageDraw.Draw(im)
        for k in range(8):
            a = k / 8 * 6.283 + u; q = 40 * (1 - u) + 6; spark(d, c + math.cos(a) * q, c + math.sin(a) * q, 3.6, (255, 240, 170, 255))
    else:
        u = (ph - 4) / 7; im = comp(im, glow(96, 96, c, c, 36, (255, 230, 150), 200 * (1 - sm(0, 0.6, u)))); d = ImageDraw.Draw(im)
        if ph == 4: circ(d, c, c, 30, (255, 255, 240, 235), None)
        arc(d, c, c, 12 + u * 34, 0, 360, GOLD[:3] + (int(255 * (1 - u)),), 4 * (1 - u) + 1); arc(d, c, c, 6 + u * 24, 0, 360, (255, 255, 235, int(230 * (1 - u))), 2)
        for k in range(10):
            a = k / 10 * 6.283 + 0.3; q = 14 + u * 28; star4(d, c + math.cos(a) * q, c + math.sin(a) * q - u * 8, 4.2 * (1 - u * .5), (255, 232, 120, int(255 * (1 - sm(.5, 1, u)))), None)
    return im
def t_ready(t, i):
    im = comp(cv(32), glow(32, 32, 16, 16, 12, (130, 255, 140), 90 + 50 * math.sin(t * 6.283))); d = ImageDraw.Draw(im); b = 1.6 * math.sin(t * 6.283)
    poly(d, [(16, 4 + b), (26, 15 + b), (19.5, 15 + b), (19.5, 26 + b), (12.5, 26 + b), (12.5, 15 + b), (6, 15 + b)], (110, 230, 110, 255), (30, 110, 50, 255), 1.3)
    poly(d, [(16, 7 + b), (22, 14 + b), (10, 14 + b)], (190, 255, 190, 255), None)
    return fin(im, 32)
def t_pulse(col, edge, bad):
    def fn(t, i):
        c = 48; im = cv(96); d = ImageDraw.Draw(im); half = 30 + t * 12; al = int(255 * (1 - t))
        d.rounded_rectangle(((c - half) * S, (c - half) * S, (c + half) * S, (c + half) * S), radius=10 * S, outline=col + (al,), width=int((4 - 2.4 * t) * S))
        d.rounded_rectangle(((c - 28) * S, (c - 28) * S, (c + 28) * S, (c + 28) * S), radius=8 * S, outline=edge + (int(120 * (1 - t)),), width=2 * S)
        if bad:
            o = 8 * (1 - t * 0.5)
            for s in (-1, 1): line(d, (c - o, c - o * s), (c + o, c + o * s), (255, 235, 235, int(230 * (1 - t * .6))), 4)
        return im
    return fn
def t_sell(t, i):
    c = 48; im = cv(96); d = ImageDraw.Draw(im)
    for k in range(5):
        blob(im, c + math.cos(k * 1.3) * 22 * t, c + math.sin(k * 1.3) * 18 * t, 6 + 6 * t, (240, 236, 226, int(190 * (1 - sm(.1, .7, t)))))
    d = ImageDraw.Draw(im); arc(d, c, c, 8 + t * 32, 0, 360, GOLD[:3] + (int(230 * (1 - t)),), 2.6 * (1 - t) + .6)
    for k in range(7):
        a = k / 7 * 6.283 + 0.4; v = 22 + 8 * (k % 3); x = c + math.cos(a) * v * t; y = c + math.sin(a) * v * t - math.sin(t * math.pi) * 18
        if t < 0.94: coin(d, x, y, 4.2, math.cos(t * 12 + k))
    return im
reg('tower_spawn_particles', 'tower', fx(8, 96, 96, t_spawn), 14, False, tint=True, note='Layer over tower build animation (frame 0 with build frame 0).')
reg('tower_destruction_particles', 'tower', fx(10, 96, 96, t_destroy), 12, False, note='Layer over destroyed animation.')
reg('tower_upgrade', 'tower', fx(12, 96, 96, t_upgrade), 14, False, event=4, note='Event frame 4 = swap tower level sprite (full-white flash frame). Play centred on tower.')
reg('upgrade_ready', 'tower', fx(8, 32, 32, t_ready, True), 8, True, pivot=[16, 16], note='Indicator, 32x32, place at tower centre + (0,-44) when gold >= upgrade cost.')
reg('placement_valid_pulse', 'tower', fx(8, 96, 96, t_pulse((70, 230, 90), (214, 255, 214), False), True), 10, True, note='Loop on the hovered/placed cell (frame 96, cell 64 centred).')
reg('placement_invalid_pulse', 'tower', fx(8, 96, 96, t_pulse((232, 72, 72), (255, 200, 200), True), True), 10, True, note='Loop on invalid cell.')
reg('sell_effect', 'tower', fx(8, 96, 96, t_sell), 14, False, note='Play when tower is sold; spawn gold coin fly-to-HUD afterwards.')

# ============================================================ ENEMY EFFECTS (white/neutral = tint in engine with modulate)
def e_spawn(t, i):
    c = 32; im = cv(64); r = random.Random(4)
    for k in range(10):
        a = k / 10 * 6.283 + r.random() * .3; q = (26 * (1 - t) if t < 0.55 else 4 + (t - .55) * 70) * r.uniform(.8, 1); al = int(230 * (1 - sm(.6, 1, t)))
        blob(im, c + math.cos(a) * q, c + math.sin(a) * q, 3 + 3 * t, (246, 244, 250, al))
    d = ImageDraw.Draw(im)
    for k in range(6): a = k * 1.05 + t * 2; spark(d, c + math.cos(a) * (6 + t * 22), c + math.sin(a) * (6 + t * 22), 3 * (1 - t * .5), (255, 255, 255, int(255 * (1 - sm(.5, 1, t)))))
    arc(d, c, c, 4 + t * 24, 0, 360, (255, 255, 255, int(200 * (1 - t))), 2 * (1 - t) + .6)
    return im
def e_death(t, i):
    c = 32; im = cv(64); r = random.Random(14)
    for k in range(9):
        a = r.random() * 6.283; q = 4 + (t ** .7) * r.uniform(10, 26); blob(im, c + math.cos(a) * q, c + math.sin(a) * q, 4 + 6 * t, (244, 242, 248, int(210 * (1 - sm(.3, 1, t)))))
    d = ImageDraw.Draw(im)
    for k in range(4): a = k * 1.57 + 0.5 + t * 3; star4(d, c + math.cos(a) * (8 + t * 18), c + math.sin(a) * (8 + t * 18) - t * 4, 4.4 * (1 - t * .5), (255, 255, 255, int(255 * (1 - sm(.5, 1, t)))), None)
    return im
def e_crit(t, i):
    c = 32; im = cv(64); sc = 0.5 + 0.6 * back(clamp(t * 2.2)); al = int(255 * (1 - sm(0.6, 1, t))); d = ImageDraw.Draw(im); pts = []
    for k in range(16): a = math.radians(k * 22.5 - 90); rr = (26 if k % 2 == 0 else 11) * sc; pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
    poly(d, pts, (255, 214, 70, al), (190, 80, 30, al), 1.6)
    pts2 = [(c + math.cos(math.radians(k * 22.5 - 90)) * (16 if k % 2 == 0 else 8) * sc, c + math.sin(math.radians(k * 22.5 - 90)) * (16 if k % 2 == 0 else 8) * sc) for k in range(16)]
    poly(d, pts2, (255, 250, 210, al), None); return im
def e_boss(t, i):
    """Boss appearance v3: dark vortex spirals open, implode into a bright flash, then erupt as a violet starburst + smoke + motes."""
    c = 96; W = 192; im = cv(W); r = random.Random(5)
    vort = (1 - sm(0.34, 0.50, t)) * (0.3 + 0.7 * sm(0.0, 0.12, t))   # vortex visibility
    P_D, P_M, P_L = (60, 24, 96), (150, 72, 214), (232, 176, 255)
    if vort > 0:
        R = 24 + 66 * sm(0.0, 0.34, t); spin = t * 420; al = int(255 * vort)
        im = comp(im, glow(W, W, c, c, 40, (170, 80, 240), 130 * vort)); d = ImageDraw.Draw(im)
        for k in range(4):
            prev = None
            for sidx in range(0, 21):
                s_ = sidx / 20; ang = math.radians(k * 90 + spin - s_ * 230); rr = 6 + (R - 6) * s_; p = (c + math.cos(ang) * rr, c + math.sin(ang) * rr)
                if prev: wdt = 13 * (1 - s_ * 0.7) + 1.5; line(d, prev, p, P_D + (al,), wdt + 2.6); 
                prev = p
            prev = None
            for sidx in range(0, 21):
                s_ = sidx / 20; ang = math.radians(k * 90 + spin - s_ * 230); rr = 6 + (R - 6) * s_; p = (c + math.cos(ang) * rr, c + math.sin(ang) * rr)
                if prev: wdt = 13 * (1 - s_ * 0.7) + 1.5; line(d, prev, p, P_M + (al,), wdt); line(d, prev, p, P_L + (int(al * .9),), wdt * 0.32)
                prev = p
        cr = 4 + 24 * sm(0.0, 0.34, t)
        circ(d, c, c, cr + 2, (28, 10, 44, al), (52, 20, 80, al), 1.4); circ(d, c, c, cr * 0.55, (10, 2, 18, al), None)
        for k in range(18):
            u = (t * 1.6 + k / 18) % 1.0; ang = math.radians(k * 47 + u * 200); q = (R + 18) * (1 - u) + 4
            circ(d, c + math.cos(ang) * q, c + math.sin(ang) * q, 2.0 * (0.4 + u), (255, 214, 255, int(al * (0.3 + 0.7 * u))), None)
    # bright implosion flash
    if 0.30 <= t < 0.46:
        u = (t - 0.30) / 0.16; im = comp(im, glow(W, W, c, c, 60, (255, 200, 255), 230)); d = ImageDraw.Draw(im); circ(d, c, c, 30 * (1 - u * 0.5) + 6, (255, 246, 255, 255), None)
    # violet eruption starburst
    if t >= 0.36:
        u = clamp((t - 0.36) / 0.64); big = sm(0.0, 0.35, u); al = int(255 * (1 - sm(0.5, 1.0, u))); d = ImageDraw.Draw(im)
        # smoke clouds
        for k in range(11):
            a = k / 11 * 6.283 + r.random() * 0.3; q = 16 + sm(0.0, 0.8, u) * r.uniform(30, 64); rad = 8 + 10 * sm(0.0, 0.7, u)
            blob(im, c + math.cos(a) * q, c + math.sin(a) * q, rad + 1.5, (34, 14, 52, int(150 * (1 - sm(0.45, 1.0, u)))))
            blob(im, c + math.cos(a) * q, c + math.sin(a) * q, rad, (92, 44, 130, int(190 * (1 - sm(0.4, 1.0, u)))))
        if al > 0:
            im = comp(im, glow(W, W, c, c, 70, (200, 70, 220), 120 * (1 - u))); d = ImageDraw.Draw(im)
            for layer, (sc, col, edge) in enumerate([(1.0, ramp([(255, 150, 220), (170, 70, 220), (90, 40, 150)], u), (52, 20, 70)), (0.62, ramp([(255, 255, 255), (255, 200, 250), (210, 140, 240)], u), None)]):
                pts = []
                for k in range(24):
                    a = math.radians(k * 15 - 90 + u * 14); ln = (78 if k % 2 == 0 else 36) * (1 + 0.18 * ((k // 2) % 3 - 1)) if k % 2 == 0 else 38
                    rr = (10 + (ln - 10) * big) * sc; pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
                poly(d, pts, col + (al,), (edge + (al,)) if edge else None, 2.2)
            circ(d, c, c, 12 * (1 - u * 0.6) + 2, (255, 255, 255, al), None)
        d = ImageDraw.Draw(im)
        for k in range(20):
            a = r.random() * 6.283; q = 14 + (u ** 0.7) * r.uniform(30, 86); y = c + math.sin(a) * q - u * 18
            star4(d, c + math.cos(a) * q, y, 3.6 * (1 - u * 0.5), (255, 214, 255, int(255 * (1 - sm(0.5, 1, u)))), None)
    return im
reg('enemy_spawn_particles', 'enemy', fx(8, 64, 64, e_spawn), 14, False, tint=True, note='Neutral white; modulate per environment (green grass, sand, ash).')
reg('enemy_death_particles', 'enemy', fx(8, 64, 64, e_death), 14, False, tint=True, note='Neutral white puff + stars; modulate to monster colour.')
reg('critical_hit', 'enemy', fx(6, 64, 64, e_crit), 16, False, note='Starburst above target on crit; pair with crit damage number.')
reg('boss_appearance', 'enemy', fx(12, 192, 192, e_boss), 12, False, note='Play at spawn point when a boss enters; camera shake suggested. 192px.')

# ============================================================ FEEDBACK
def f_coin(t, i):
    im = cv(24); d = ImageDraw.Draw(im); coin(d, 12, 12, 9, math.cos(t * 6.283)); return im
def f_sparkle(t, i):
    c = 24; im = cv(48); d = ImageDraw.Draw(im)
    for k in range(6):
        a = k / 6 * 6.283 + 0.3; q = 3 + t * 18; spark(d, c + math.cos(a) * q, c + math.sin(a) * q, 4.4 * (1 - t * .55), (255, 226, 100, int(255 * (1 - sm(.5, 1, t)))))
    arc(d, c, c, 4 + t * 16, 0, 360, (255, 244, 190, int(220 * (1 - t))), 2 * (1 - t) + .5)
    if t < 0.4: circ(d, c, c, 7 * (1 - t / .4) + 1, (255, 255, 235, 255), None)
    return im
CONF = [(236, 76, 96), (255, 220, 72), (110, 160, 255), (110, 220, 110), (255, 150, 60), (190, 120, 240)]
def f_complete(t, i):
    c = 96; im = comp(cv(192), glow(192, 192, c, c, 40 + 30 * t, (255, 226, 130), 150 * (1 - t))); d = ImageDraw.Draw(im); r = random.Random(11)
    arc(d, c, c, 10 + t * 80, 0, 360, GOLD[:3] + (int(240 * (1 - t)),), 5 * (1 - t) + 1)
    sc = 0.4 + 0.8 * back(clamp(t * 2)); star = []
    for k in range(10): a = math.radians(k * 36 - 90); rr = (30 if k % 2 == 0 else 13) * sc; star.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
    poly(d, star, (255, 214, 70, int(255 * (1 - sm(.7, 1, t)))), (190, 110, 30, int(255 * (1 - sm(.7, 1, t)))), 1.6)
    for k in range(34):
        a = r.random() * 6.283; v = r.uniform(30, 86); x = c + math.cos(a) * v * (t ** .6); y = c + math.sin(a) * v * (t ** .6) + t * t * 28
        col = r.choice(CONF) + (int(255 * (1 - sm(.6, 1, t))),); rot = r.uniform(0, 6.283) + t * 6
        poly(d, [(x + math.cos(rot + q * 1.57) * 3.2, y + math.sin(rot + q * 1.57) * 1.7) for q in range(4)], col, None)
    return im
def f_wave(t, i):
    c = 64; im = cv(128); d = ImageDraw.Draw(im)
    for k in range(3):
        u = clamp(t * 1.3 - k * 0.2)
        if u > 0: arc(d, c, c, 8 + u * 52, 0, 360, (255, 232, 160, int(230 * (1 - u))), 5 * (1 - u) + 1)
    for k in range(10): a = k / 10 * 6.283; q = 14 + t * 44; spark(d, c + math.cos(a) * q, c + math.sin(a) * q, 3.4 * (1 - t * .5), (255, 244, 200, int(255 * (1 - sm(.4, 1, t)))))
    return im
reg('coin_spin', 'feedback', fx(8, 24, 24, f_coin, True), 12, True, note='Gold coin loop 24px; fly-to-HUD done by Tween in engine.')
reg('gold_collect_sparkle', 'feedback', fx(6, 48, 48, f_sparkle), 16, False, note='Play when coin reaches the HUD gold icon.')
reg('level_complete', 'feedback', fx(12, 192, 192, f_complete), 12, False, note='Victory burst, centre of screen.')
reg('wave_transition', 'feedback', fx(8, 128, 128, f_wave), 12, False, note='Horn ripple at spawn point when next wave starts.')

# damage numbers: glyph strips "0123456789+" (white/outlined). Engine can also use Label; these give a matching art style.
GLY = '0123456789+'
def digits(name, fill, edge, w, h, size, note):
    fr = []
    f = ImageFont.load_default(size=size * S)
    for chv in GLY:
        im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((w * S / 2, h * S / 2), chv, font=f, fill=fill, anchor='mm', stroke_width=int(2.2 * S), stroke_fill=edge)
        fr.append(fin(im, w, h))
    reg(name, 'feedback', fr, 0, False, note=note + ' Glyph order: ' + GLY + '. One frame per glyph; use as atlas, not an animation.')
digits('damage_digits_normal', (255, 255, 255, 255), (52, 40, 50, 255), 22, 30, 22, 'Normal damage, white.')
digits('damage_digits_crit', (255, 214, 70, 255), (150, 50, 30, 255), 30, 40, 30, 'Critical damage, bigger, yellow.')
digits('damage_digits_heal', (140, 255, 140, 255), (30, 96, 50, 255), 22, 30, 22, 'Heal, green.')

# ============================================================ ATLAS
json.dump({'note': 'Phase 5 VFX. Strips are horizontal, frame size frame_w x frame_h, pivot = frame centre unless stated. loop=false -> one-shot (free on finish).',
           'effects': REG}, open(f'{ROOT}/Documentation/vfx_atlas.json', 'w'), indent=1)

# ============================================================ DEMOS (review only)
atl = Image.open(f'{ROOT}/Environment/Grassland/grassland_tileset_32.png'); gt = [atl.crop((i * 32, 0, i * 32 + 32, 32)) for i in range(8)]
def grass_bg(w, h, seed=2):
    r = random.Random(seed); bg = Image.new('RGBA', (w, h))
    for y in range(0, h, 32):
        for x in range(0, w, 32): bg.paste(gt[r.randrange(8)], (x, y))
    return bg
def frames_of(name):
    e = REG[name]; im = Image.open(f'{ROOT}/{e["file"]}').convert('RGBA'); w = e['frame_w']
    return [im.crop((i * w, 0, i * w + w, e['frame_h'])) for i in range(e['frames'])]
def demo(group, names, path, cols=4, scale=1.5, cycle=1.6, fps=14):
    cell = max(max(REG[n]['frame_w'], REG[n]['frame_h']) for n in names) + 14; rows = math.ceil(len(names) / cols); W = cols * cell; H = rows * (cell + 14) + 22
    bg = grass_bg(W, H, 3); fr_cache = {n: frames_of(n) for n in names}; out = []
    for tick in range(int(cycle * fps * 1.0)):
        tm = tick / fps; im = bg.copy(); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 20), fill=(30, 34, 42, 255)); d.text((6, 3), f'PHASE 5 VFX  -  {group}', fill=(255, 226, 140, 255), font=FONT)
        for k, n in enumerate(names):
            e = REG[n]; f = fr_cache[n]; x0, y0 = (k % cols) * cell, 22 + (k // cols) * (cell + 14)
            if e['fps'] == 0: idx = int(tm * 3) % len(f) if len(f) > 1 else 0
            elif e['loop']: idx = int(tm * e['fps']) % len(f)
            else: idx = min(int((tm % (e['duration_s'] + 0.35)) * e['fps']), len(f) - 1)
            fw, fh = e['frame_w'], e['frame_h']
            if e['fps'] == 0 and len(f) > 1: idx = k % len(f)
            if group.startswith('projectiles') and e['fps'] == 0: pass
            im.alpha_composite(f[idx], (x0 + (cell - fw) // 2, y0 + (cell - fh) // 2))
            d.text((x0 + 3, y0 + cell - 2), n, fill=(255, 255, 255, 255), font=FONT, stroke_width=2, stroke_fill=(30, 30, 30, 255))
        out.append(im.resize((int(W * scale), int(H * scale)), Image.BICUBIC).convert('RGB'))
    mos = Image.new('RGB', (out[0].width, out[0].height * min(len(out), 10)))
    for i, f in enumerate(out[:10]): mos.paste(f, (0, i * out[0].height))
    pal = mos.quantize(colors=250, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in out]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, disposal=1, optimize=True)
G = lambda g: [n for n, e in REG.items() if e['group'] == g]
PV = f'{ROOT}/VFX/Preview'
# projectile -> impact pairs
PAIRS = [('fireball', 'fire_explosion'), ('lightning_bolt', 'lightning_impact'), ('poison_glob', 'poison_splash'), ('cannonball', 'cannon_explosion'),
         ('magic_orb', 'magical_burst'), ('nature_seed', 'nature_root_impact'), ('sniper_round', None)]
def pair_demo(path, fps=16, scale=1.5):
    W, RH = 360, 80; H = 22 + RH * len(PAIRS); bg = grass_bg(W, H, 9); out = []; T = 26
    for tick in range(T * 2):
        tm = tick % T; im = bg.copy(); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, 20), fill=(30, 34, 42, 255)); d.text((6, 3), 'PHASE 5 VFX  -  projectile -> impact', fill=(255, 226, 140, 255), font=FONT)
        for r, (p, imp) in enumerate(PAIRS):
            y = 22 + r * RH + RH // 2; pr = Image.open(f'{ROOT}/{REG[p]["file"]}').convert('RGBA'); x = 20 + (250 - 20) * clamp(tm / 14)
            d.ellipse((12, y - 6, 28, y + 6), outline=(255, 255, 255, 90)); d.text((4, y - 38), p, fill=(255, 255, 255, 255), font=FONT, stroke_width=2, stroke_fill=(30, 30, 30, 255))
            if tm < 15: im.alpha_composite(pr, (int(x - pr.width / 2), int(y - pr.height / 2)))
            if imp and tm >= 14:
                f = frames_of(imp); j = min(int((tm - 14) * REG[imp]['fps'] / fps), len(f) - 1); im.alpha_composite(f[j], (int(260 - f[j].width / 2), int(y - f[j].height / 2)))
            if not imp and tm >= 14: spark(ImageDraw.Draw(im), 260, y, 5, (255, 255, 255, 255)) if False else None
            tx = 300
            for rr, col in [(13, (60, 40, 30, 255)), (12, (250, 246, 236, 255)), (9, (220, 60, 66, 255)), (6, (250, 246, 236, 255)), (3, (220, 60, 66, 255))]:
                pass
        out.append(im.resize((int(W * scale), int(H * scale)), Image.BICUBIC).convert('RGB'))
    pal = Image.new('RGB', (out[0].width, out[0].height * 6))
    for i in range(6): pal.paste(out[i * 4], (0, i * out[0].height))
    pal = pal.quantize(colors=250, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE); q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in out]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, disposal=1, optimize=True)
pair_demo(f'{PV}/DEMO_projectiles_and_impacts.gif')
demo('status effects', G('status'), f'{PV}/DEMO_status_effects.gif', 5)
demo('tower effects', G('tower'), f'{PV}/DEMO_tower_effects.gif', 4)
demo('enemy effects', G('enemy'), f'{PV}/DEMO_enemy_effects.gif', 4, 1.2)
demo('feedback', [n for n in G('feedback') if not n.startswith('damage')] + ['damage_digits_normal', 'damage_digits_crit', 'damage_digits_heal'], f'{PV}/DEMO_feedback.gif', 4, 1.2)

# static overview (middle frame of each effect)
names = [n for n in REG if REG[n]['group'] != 'projectile']; cell = 124; cols = 8; rows = math.ceil(len(names) / cols)
ov = grass_bg(cols * cell, rows * (cell + 14), 4).copy(); d = ImageDraw.Draw(ov)
for k, n in enumerate(names):
    e = REG[n]; f = frames_of(n); fr = f[min(len(f) - 1, max(0, int(len(f) * 0.3)))] if e['fps'] else f[0]
    if max(fr.size) > cell - 8: fr = fr.resize((cell - 8, cell - 8), Image.LANCZOS)
    x0, y0 = (k % cols) * cell, (k // cols) * (cell + 14); ov.alpha_composite(fr, (x0 + (cell - fr.width) // 2, y0 + (cell - fr.height) // 2))
    d.text((x0 + 3, y0 + cell - 4), n, fill=(255, 255, 255, 255), font=FONT, stroke_width=2, stroke_fill=(30, 30, 30, 255))
ov.convert('RGB').save(f'{PV}/vfx_overview.png')
# projectile sheet
pr = G('projectile'); ps = grass_bg(len(pr) * 64, 80, 6)
for k, n in enumerate(pr):
    im = Image.open(f'{ROOT}/{REG[n]["file"]}').convert('RGBA'); ps.alpha_composite(im, (k * 64 + (64 - im.width) // 2, 40 - im.height // 2)); ImageDraw.Draw(ps).text((k * 64 + 2, 62), n[:10], fill=(255, 255, 255, 255), font=FONT, stroke_width=2, stroke_fill=(30, 30, 30, 255))
ps.resize((ps.width * 2, ps.height * 2), Image.BICUBIC).convert('RGB').save(f'{PV}/projectiles_sheet.png')
print('vfx done:', len(REG), 'entries')
