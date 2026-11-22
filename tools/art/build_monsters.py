import os, math, random, json, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4
ROOT = '/mnt/user-data/outputs/GameAssets'
OUT = (52, 40, 50, 255)
NAMES = ['slime', 'goblin', 'boar', 'mushroom', 'treant']
for n in NAMES: os.makedirs(f'{ROOT}/Monsters/Grassland/{n.capitalize()}', exist_ok=True)
os.makedirs(f'{ROOT}/Monsters/Preview', exist_ok=True)
try: FONT = ImageFont.load_default(size=15); FONT_S = ImageFont.load_default(size=12)
except Exception: FONT = FONT_S = ImageFont.load_default()

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def sm(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def comp(*ims):
    o = Image.new('RGBA', ims[0].size, (0, 0, 0, 0))
    for i in ims: o.alpha_composite(i)
    return o
def fade(im, a):
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a))); return im
def flashfx(im, k):
    if k <= 0: return im
    k = k * 0.8
    r, g, b, a = im.split(); f = lambda c: c.point(lambda v: int(v + (255 - v) * k))
    return Image.merge('RGBA', (f(r), f(g), f(b), a))
def xform(im, s=1.0, dx=0, dy=0, ang=0, alpha=1.0):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    if s < 0.02 or alpha <= 0: return out
    if ang: im = im.rotate(ang, resample=Image.BICUBIC)
    w = max(2, int(im.width * s)); r = im.resize((w, w), Image.LANCZOS)
    if alpha < 1: r = fade(r, alpha)
    out.alpha_composite(r, (int(im.width / 2 + dx - w / 2), int(im.height / 2 + dy - w / 2)))
    return out
def put(bg, spr, x, y):
    x, y = int(round(x)), int(round(y))
    if x >= bg.width or y >= bg.height or x + spr.width <= 0 or y + spr.height <= 0: return
    sx0, sy0 = max(-x, 0), max(-y, 0); sx1 = min(spr.width, bg.width - x); sy1 = min(spr.height, bg.height - y)
    bg.alpha_composite(spr, (max(x, 0), max(y, 0)), (sx0, sy0, sx1, sy1))

class Cx:
    def __init__(s, F, ang, sc=1.0):
        s.sc = sc; s.F = F; s.c = F / 2; a = math.radians(ang); s.ca, s.sa = math.cos(a), math.sin(a)
        s.im = Image.new('RGBA', (F * S, F * S), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
    def T(s, x, y): return (s.c + (x * s.ca - y * s.sa) * s.sc, s.c + (x * s.sa + y * s.ca) * s.sc)
    def _poly(s, q, fill, out, ow):
        pts = [(x * S, y * S) for x, y in q]
        if fill is not None and len(fill) == 4 and fill[3] < 255:
            tmp = Image.new('RGBA', s.im.size, (0, 0, 0, 0)); ImageDraw.Draw(tmp).polygon(pts, fill=fill); s.im.alpha_composite(tmp)
        else: s.d.polygon(pts, fill=fill)
        if out: s.d.line(pts + [pts[0]], fill=out, width=max(1, int(ow * S)), joint='curve')
    def poly(s, pts, fill, out=OUT, ow=1.3): s._poly([s.T(*p) for p in pts], fill, out, ow)
    def ell(s, cx, cy, rx, ry, fill, out=OUT, ow=1.3, rot=0, n=40):
        r = math.radians(rot); pts = []
        for i in range(n):
            t = i / n * 6.2832; x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
        s.poly(pts, fill, out, ow)
    def circ(s, cx, cy, r, fill, out=OUT, ow=1.3): s.ell(cx, cy, r, r, fill, out, ow, 0, 28)
    def hl(s, cx, cy, r, col=(255, 255, 255, 150)):
        x, y = s.T(cx, cy); r = r * s.sc; x -= r * 0.35; y -= r * 0.42
        s._poly([(x + r * 0.5 * math.cos(t / 16 * 6.2832), y + r * 0.36 * math.sin(t / 16 * 6.2832)) for t in range(16)], col, None, 0)
    def line(s, p, q, col, w):
        a, b = s.T(*p), s.T(*q); s.d.line((a[0] * S, a[1] * S, b[0] * S, b[1] * S), fill=col, width=max(1, int(w * s.sc * S)))
    def limb(s, p, q, col, w, ow=1.2):
        s.line(p, q, OUT, w + ow * 2); s.line(p, q, col, w)
    def eye(s, x, y, r, pr=None):
        s.circ(x, y, r, (255, 255, 255, 255), OUT, 0.9); s.circ(x + r * 0.3, y, pr or r * 0.52, (36, 28, 40, 255), None)
        a = s.T(x + r * 0.3, y); s._poly([(a[0] - r * 0.3 + r * 0.22 * math.cos(t / 8 * 6.2832), a[1] - r * 0.3 + r * 0.22 * math.sin(t / 8 * 6.2832)) for t in range(8)], (255, 255, 255, 255), None, 0)
    def out(s): return s.im.resize((s.F, s.F), Image.LANCZOS)

def star4(d, x, y, r, col):
    pts = []
    for k in range(8):
        a = math.radians(k * 45 - 90); rr = r if k % 2 == 0 else r * 0.38; pts.append(((x + math.cos(a) * rr) * S, (y + math.sin(a) * rr) * S))
    d.polygon(pts, fill=col)

# ================================================================== SLIME
G, G_D, G_L = (96, 204, 100, 255), (40, 118, 64, 255), (136, 228, 122, 255)
def slime(ang, mode, k):
    cx = Cx(64, ang); st = 0; ox = 0; fl = 0
    if mode == 'idle': st = 0.07 * math.sin(k * 6.2832)
    elif mode == 'walk': st = -0.22 * math.cos(k * 6.2832); ox = 2.5 * math.sin(k * 6.2832)
    elif mode == 'atk':
        if k < .35: u = k / .35; st = -0.28 * u; ox = -3 * u
        elif k < .6: u = (k - .35) / .25; st = -0.28 + 0.65 * u; ox = -3 + 16 * u
        else: u = (k - .6) / .4; st = 0.37 * (1 - u); ox = 13 * (1 - u)
    elif mode == 'hit': ox = -4 * math.sin(math.pi * k); st = -0.2 * math.sin(math.pi * k); fl = 1 - k
    sx, sy, ph = 1 + st, 1 - 0.6 * st, k * 6.2832
    pts = []
    for i in range(40):
        t = i / 40 * 6.2832; r = 14 * (1 + 0.05 * math.sin(3 * t + ph)); pts.append((ox + r * math.cos(t) * sx, r * math.sin(t) * sy))
    cx.poly(pts, G, G_D, 1.5)
    q = [cx.T(ox + (p[0] - ox) * 0.74, p[1] * 0.74) for p in pts]; cx._poly([(x - 1.5, y - 1.8) for x, y in q], G_L, None, 0)
    cx.circ(ox - 4, 3, 3.2, (74, 176, 92, 255), None); cx.circ(ox - 6.5, -4, 1.6, (74, 176, 92, 255), None)
    cx.hl(ox, 0, 11, (255, 255, 255, 120))
    for sgn in (-1, 1): cx.circ(ox + 5, sgn * 8.2 * sy, 1.8, (255, 150, 164, 160), None)
    for sgn in (-1, 1): cx.eye(ox + 7.5 * sx, sgn * 4.6 * sy, 3.5)
    cx.ell(ox + 11.8 * sx, 0, 1.6, 1.0, G_D, None)
    return flashfx(cx.out(), fl)

# ================================================================== GOBLIN
SK, SK_D, TUN, CAP = (128, 190, 78, 255), (60, 116, 52, 255), (160, 110, 66, 255), (196, 76, 66, 255)
def goblin(ang, mode, k):
    cx = Cx(80, ang, 1.25); sw = math.sin(k * 6.2832); ox = 0; th = 0; fl = 0; hb = 0; ft = 0; hand = 0
    if mode == 'walk': ft = 5 * sw; hand = 4 * sw; hb = 0.8 * abs(sw)
    if mode == 'idle': hb = 0.7 * math.sin(k * 6.2832)
    if mode == 'atk':
        if k < .3: u = k / .3; ox = -3 * u; th = -0.4 * u
        elif k < .55: u = (k - .3) / .25; ox = -3 + 11 * u; th = -0.4 + 1.4 * u
        else: u = (k - .55) / .45; ox = 8 * (1 - u); th = 1 - u
    if mode == 'hit': ox = -4 * math.sin(math.pi * k); fl = 1 - k
    for sgn in (-1, 1): cx.ell(ox - 1 + ft * sgn, sgn * 5, 4.2, 2.9, (104, 68, 46, 255), OUT, 1.0)
    cx.limb((ox, 8.5), (ox + 5 - hand, 10.8), SK, 3.0)
    cx.ell(ox - 1, 0, 6.6, 9.8, TUN, OUT, 1.3); cx.line((ox + 1.5, -8.6), (ox + 1.5, 8.6), (96, 62, 40, 255), 1.5)
    cx.hl(ox - 1, 0, 8, (255, 230, 190, 90))
    cx.circ(ox + 5 - hand, 10.8, 2.2, SK, OUT, 0.9)
    hx, hy = ox + 6 + hand * 0.3 + th * 9, -9.2
    cx.limb((ox, -8.6), (hx, hy), SK, 3.0)
    cx.poly([(hx + 11, hy), (hx + 1, hy - 1.8), (hx + 1, hy + 1.8)], (214, 220, 232, 255), OUT, 0.9)
    cx.line((hx + 1.5, hy - 3), (hx + 1.5, hy + 3), (130, 90, 50, 255), 1.5)
    cx.circ(hx, hy, 2.2, SK, OUT, 0.9)
    for sgn in (-1, 1):
        cx.poly([(ox + 1.0, sgn * 13.6), (ox + 5.5, sgn * 6.4), (ox - 1.2, sgn * 6.6)], SK, OUT, 1.1)
        cx.poly([(ox + 1.5, sgn * 11.6), (ox + 4.2, sgn * 7.6), (ox - 0.2, sgn * 7.8)], (232, 156, 150, 255), None)
    cx.circ(ox + 3 + hb, 0, 7.4, SK, SK_D, 1.3); cx.hl(ox + 3 + hb, 0, 6.5, (230, 255, 190, 110))
    cx.circ(ox + 0.6 + hb, 0, 4.3, CAP, (112, 36, 42, 255), 1.1); cx.circ(ox - 4.6 + hb, 0, 1.7, (244, 214, 124, 255), OUT, 0.7)
    for sgn in (-1, 1): cx.eye(ox + 7.4 + hb, sgn * 3.1, 2.0, 1.0)
    cx.circ(ox + 10.6 + hb, 0, 1.7, (98, 158, 62, 255), SK_D, 0.6)
    return flashfx(cx.out(), fl)

# ================================================================== BOAR
BR, BR_L, BR_D, PINK = (156, 102, 68, 255), (176, 120, 82, 255), (88, 54, 40, 255), (242, 168, 168, 255)
def boar(ang, mode, k):
    cx = Cx(80, ang); sw = math.sin(k * 6.2832); ox = 0; ft = 0; hd = 0; fl = 0; lines = 0; roll = 0
    if mode == 'walk': ft = 5 * sw; roll = 1.2 * sw
    if mode == 'idle': hd = 0.7 * math.sin(k * 6.2832); roll = 0.5 * math.sin(k * 6.2832)
    if mode == 'atk':
        if k < .3: u = k / .3; ox = -4 * u; hd = -1 * u
        elif k < .6: u = (k - .3) / .3; ox = -4 + 16 * u; hd = -1 + 4 * u; lines = u
        else: u = (k - .6) / .4; ox = 12 * (1 - u); hd = 3 * (1 - u); lines = 1 - u
    if mode == 'hit': ox = -5 * math.sin(math.pi * k); fl = 1 - k
    for sgn in (-1, 1):
        a, b = (ft, -ft) if sgn > 0 else (-ft, ft)
        cx.ell(ox + 9 + a, sgn * 11.4, 4.6, 3.4, (112, 74, 52, 255), OUT, 1.0); cx.ell(ox + 10.5 + a, sgn * 11.6, 2.4, 2.0, (60, 40, 34, 255), None)
        cx.ell(ox - 10 + b, sgn * 11.4, 4.6, 3.4, (112, 74, 52, 255), OUT, 1.0); cx.ell(ox - 8.5 + b, sgn * 11.6, 2.4, 2.0, (60, 40, 34, 255), None)
    if lines > 0:
        for i in range(3): y = -7 + 7 * i; cx.line((ox - 26, y), (ox - 26 - lines * 11, y), (255, 255, 255, int(220 * lines)), 1.3)
    cx.ell(ox - 2, roll, 20.5, 12.8, BR, BR_D, 1.6)
    cx.ell(ox - 5, roll, 13, 3.2, (116, 72, 50, 255), None)
    for i in range(7):
        x = ox - 15 + i * 3.3; s_ = 1 if i % 2 == 0 else -1
        cx.poly([(x, roll), (x + 1.8, roll + s_ * 4.2), (x + 3.6, roll)], BR_D, None)
    cx.hl(ox - 2, roll, 14, (255, 220, 180, 100))
    cx.circ(ox - 23.5, roll, 2.6, PINK, OUT, 0.9); cx.circ(ox - 23.5, roll, 1.0, BR, None)
    for sgn in (-1, 1):
        cx.poly([(ox + 12, sgn * 6.2 + roll), (ox + 8.5, sgn * 13.2 + roll), (ox + 16.5, sgn * 8.8 + roll)], BR_D, OUT, 1.1)
        cx.poly([(ox + 12.5, sgn * 8 + roll), (ox + 10.6, sgn * 11.6 + roll), (ox + 14.5, sgn * 9.2 + roll)], (230, 150, 150, 255), None)
    cx.ell(ox + 16.5 + hd, roll, 9.8, 8.8, BR_L, BR_D, 1.4); cx.hl(ox + 16.5 + hd, roll, 8, (255, 230, 190, 100))
    cx.ell(ox + 24.6 + hd, roll, 5.3, 4.7, PINK, (150, 80, 92, 255), 1.1)
    for sgn in (-1, 1): cx.circ(ox + 26.6 + hd, sgn * 1.8 + roll, 0.95, (120, 50, 64, 255), None)
    for sgn in (-1, 1):
        cx.poly([(ox + 25 + hd, sgn * 4.0 + roll), (ox + 31.5 + hd, sgn * 7.4 + roll), (ox + 27.5 + hd, sgn * 2.4 + roll)], (250, 246, 232, 255), OUT, 0.9)
    for sgn in (-1, 1):
        cx.circ(ox + 18.2 + hd, sgn * 4.7 + roll, 1.9, (255, 255, 255, 255), OUT, 0.7); cx.circ(ox + 18.7 + hd, sgn * 4.7 + roll, 1.1, (30, 24, 34, 255), None)
        cx.line((ox + 16.2 + hd, sgn * 7.2 + roll), (ox + 20.4 + hd, sgn * 4.2 + roll), BR_D, 1.0)
    return flashfx(cx.out(), fl)

# ================================================================== MUSHROOM
CAPR, CAPR_D, CAPR_L = (226, 78, 86, 255), (110, 34, 54, 255), (206, 60, 74, 255)
CRM, CRM_D = (252, 236, 204, 255), (170, 134, 102, 255)
def mushroom(ang, mode, k):
    cx = Cx(64, ang); sw = math.sin(k * 6.2832); rot = 0; sq = 1.0; fl = 0; ox = 0; ft = 0; puff = 0
    if mode == 'idle': rot = 4 * sw; sq = 1 + 0.025 * sw
    if mode == 'walk': ft = 4 * sw; rot = 8 * sw; sq = 1 + 0.03 * abs(sw)
    if mode == 'atk':
        if k < .35: u = k / .35; sq = 1 - 0.14 * u; ox = -2 * u
        elif k < .6: u = (k - .35) / .25; sq = 0.86 + 0.28 * u; ox = -2 + 4 * u; puff = u * 0.5
        else: u = (k - .6) / .4; sq = 1.14 - 0.14 * u; ox = 2 * (1 - u); puff = 0.5 + 0.5 * u
    if mode == 'hit': ox = -3 * math.sin(math.pi * k); sq = 1 - 0.15 * math.sin(math.pi * k); fl = 1 - k
    ccx = ox - 4; R = 16.5 * (1 + (1 - sq))
    for sgn in (-1, 1): cx.ell(ox + 15 + ft * sgn, sgn * 8, 3.4, 2.6, CRM, CRM_D, 1.0)
    for sgn in (-1, 1): cx.ell(ox - 1, sgn * 18.2, 3.4, 2.4, CRM, CRM_D, 1.0, rot=0)
    cx.ell(ox + 13.5, 0, 7.6, 8.6, CRM, CRM_D, 1.2)
    for sgn in (-1, 1):
        cx.eye(ox + 16.6, sgn * 3.4, 1.9, 1.0); cx.circ(ox + 15.4, sgn * 6.4, 1.3, (255, 150, 164, 170), None)
    cx.ell(ox + 19.4, 0, 1.0, 1.4, (150, 70, 70, 255), None)
    r_ = math.radians(rot)
    def rp(x, y): return (ccx + x * math.cos(r_) - y * math.sin(r_), x * math.sin(r_) + y * math.cos(r_))
    cx.circ(ccx, 0, R, CAPR_L, CAPR_D, 1.6)
    cx.circ(ccx, 0, R * 0.86, CAPR, None)
    for (x, y, rr) in [(-4, -8, 3.6), (7, -6, 2.6), (-9, 4, 3.0), (3, 6, 3.8), (11, 2, 1.9), (-1, -1, 2.0), (-5, 11, 2.0), (8, 11, 2.2)]:
        px, py = rp(x * R / 16.5, y * R / 16.5); cx.circ(px, py, rr, (255, 250, 242, 255), (190, 150, 150, 255), 0.7)
    cx.hl(ccx, 0, R * 0.9, (255, 220, 220, 120))
    if puff > 0:
        r = random.Random(3)
        for i in range(9):
            a = i / 9 * 6.2832 + r.random(); q = 20 + puff * 15; rr = 2.5 + puff * 3.5
            x, y = cx.c + math.cos(a) * q, cx.c + math.sin(a) * q
            cx._poly([(x + rr * math.cos(t / 14 * 6.2832), y + rr * math.sin(t / 14 * 6.2832)) for t in range(14)], (210, 232, 110, int(230 * (1 - puff * 0.55))), None, 0)
    return flashfx(cx.out(), fl)

# ================================================================== TREANT
BK, BK_D = (124, 84, 54, 255), (66, 42, 30, 255)
LD, LM, LL = (46, 122, 58, 255), (84, 168, 70, 255), (152, 218, 98, 255)
FOL_O = (34, 88, 42, 255)
def treant(ang, mode, k):
    cx = Cx(96, ang); sw = math.sin(k * 6.2832); ft = 0; arm = 0; sway = 0; ox = 0; fl = 0; shock = 0; leaves = 0
    if mode == 'idle': sway = 2 * sw; arm = 1.2 * sw
    if mode == 'walk': ft = 5 * sw; arm = 4 * sw; sway = 3 * sw
    if mode == 'atk':
        if k < .4: u = k / .4; arm = -6 * u; ox = -3 * u
        elif k < .6: u = (k - .4) / .2; arm = -6 + 22 * u; ox = -3 + 8 * u
        else: u = (k - .6) / .4; arm = 16 * (1 - u); ox = 5 * (1 - u); shock = u
    if mode == 'hit': ox = -4 * math.sin(math.pi * k); fl = 1 - k; leaves = k
    for sgn in (-1, 1):
        a, b = (ft, -ft) if sgn > 0 else (-ft, ft)
        cx.ell(ox + 10 + a, sgn * 11, 7.2, 5.2, BK_D, OUT, 1.2); cx.ell(ox - 9 + b, sgn * 13, 7.2, 5.2, BK_D, OUT, 1.2)
    if shock > 0:
        c0 = cx.T(ox + 34, 0)
        for rr, al in [(6 + shock * 22, 220), (3 + shock * 14, 160)]:
            cx.d.ellipse(((c0[0] - rr) * S, (c0[1] - rr) * S, (c0[0] + rr) * S, (c0[1] + rr) * S), outline=(236, 224, 196, int(al * (1 - shock * 0.7))), width=int(2.2 * S))
    cx.ell(ox, 0, 14.6, 15.6, BK, BK_D, 1.7)
    for yy in (-8, -3, 3, 8): cx.line((ox - 8, yy), (ox + 3, yy + 0.6), (96, 62, 42, 255), 1.0)
    cx.ell(ox + 12.4, 0, 4.8, 7.0, (44, 28, 26, 255), None)
    for sgn in (-1, 1): cx.circ(ox + 13.4, sgn * 3.1, 1.9, (255, 226, 100, 255), None); cx.circ(ox + 14, sgn * 3.1, 0.8, (120, 70, 20, 255), None)
    cx.ell(ox + 16.4, 0, 1.2, 2.4, (255, 150, 70, 255), None)
    for sgn in (-1, 1):
        ex, ey = ox + 20 + arm, sgn * (21 - arm * 0.45)
        cx.limb((ox + 2, sgn * 12), (ox + 9 + arm * 0.5, sgn * 17), BK, 5.8, 1.3); cx.limb((ox + 9 + arm * 0.5, sgn * 17), (ex, ey), BK, 5.0, 1.3)
        for dy_ in (-1, 0, 1): cx.limb((ex, ey), (ex + 6, ey + dy_ * 4.2), BK, 1.8, 0.7)
        cx.circ(ex + 1, ey, 4.6, LM, FOL_O, 1.0); cx.circ(ex, ey - 1, 2.2, LL, None)
    cc = ox - 13 + sway * 0.4; cy_ = sway * 0.6
    cx.circ(cc, cy_, 20.5, LD, FOL_O, 1.6)
    rr_ = random.Random(2)
    for i in range(8):
        a = i / 8 * 6.2832 + 0.2; x, y = cc + math.cos(a) * 13.5, cy_ + math.sin(a) * 13.5
        cx.circ(x, y, 9.6, LM, None); cx.circ(x - 1.4, y - 1.6, 4.6, LL, None)
    cx.circ(cc, cy_, 11.5, LM, None); cx.circ(cc - 2, cy_ - 2.2, 6.0, LL, None)
    for i in range(5):
        a = rr_.random() * 6.2832; q = rr_.random() * 15; cx.circ(cc + math.cos(a) * q, cy_ + math.sin(a) * q, 1.5, (255, 170, 190, 255), (180, 70, 110, 255), 0.5)
    im = cx.out()
    if leaves > 0:
        lay = Image.new('RGBA', (96 * S, 96 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(9)
        for _ in range(9):
            a = r.random() * 6.2832; q = 16 + leaves * 26 * r.random(); x, y = 48 + math.cos(a) * q, 48 + math.sin(a) * q; rr = 2.4
            d.ellipse(((x - rr) * S, (y - rr * 0.6) * S, (x + rr) * S, (y + rr * 0.6) * S), fill=LM, outline=FOL_O, width=S)
        im = comp(im, fade(lay.resize((96, 96), Image.LANCZOS), 1 - leaves * 0.6))
    return flashfx(im, fl)

# ================================================================== registry
MON = {
    'slime': dict(fn=slime, F=64, sh=(15, 11), stride=20, hit=4, role='Normal', env='Grassland', speed='Medium (bounce hop)',
                  look='Round jelly blob with wobbling edge, big eyes, pink blush and a darker nucleus.',
                  move='Hops: squashes on landing, stretches mid-air.', attack='Winds up, then lunges forward and slams into the target.',
                  death=dict(sc=0.5, spin=0, cols=[(96, 204, 100, 255), (160, 236, 140, 255)], n=16, shape='dot', rmax=26, puddle=True, stars=False),
                  spawn=dict(cols=[(96, 204, 100, 255), (160, 236, 140, 255)], n=14, shape='dot')),
    'goblin': dict(fn=goblin, F=80, sh=(14, 11), stride=18, hit=4, role='Fast', env='Grassland', speed='Fast (scurry)',
                   look='Small green goblin: big pointy ears, red cap with pom, leather tunic, dagger.',
                   move='Scurries with alternating feet and swinging arms.', attack='Quick dagger stab with a body lunge.',
                   death=dict(sc=0.25, spin=300, cols=[(196, 190, 210, 255), (230, 226, 240, 255)], n=14, shape='puff', rmax=28, puddle=False, stars=True),
                   spawn=dict(cols=[(196, 190, 210, 255), (230, 226, 240, 255)], n=12, shape='puff')),
    'boar': dict(fn=boar, F=80, sh=(21, 12), stride=30, hit=4, role='Fast (charger)', env='Grassland', speed='Very fast (gallop)',
                 look='Stocky brown boar with dark spiky mane, pink snout, white tusks and curly tail.',
                 move='Gallops with diagonal hoof pairs and body roll.', attack='Lowers head and charges forward with tusks, speed lines behind.',
                 death=dict(sc=0.8, spin=100, cols=[(214, 190, 150, 255), (240, 226, 196, 255)], n=14, shape='puff', rmax=30, puddle=False, stars=True),
                 spawn=dict(cols=[(214, 190, 150, 255), (240, 226, 196, 255)], n=12, shape='puff')),
    'mushroom': dict(fn=mushroom, F=64, sh=(17, 15), stride=18, hit=4, role='Special ability (spore burst)', env='Grassland', speed='Slow (waddle)',
                     look='Red spotted cap seen from above, cream face peeking from under the rim, stubby feet.',
                     move='Waddles: cap sways side to side, feet alternate.', attack='Squashes, then releases a ring of spores that damages nearby targets.',
                     death=dict(sc=0.45, spin=0, cols=[(210, 232, 110, 255), (250, 246, 170, 255), (226, 78, 86, 255)], n=18, shape='dot', rmax=30, puddle=False, stars=True),
                     spawn=dict(cols=[(210, 232, 110, 255), (250, 246, 170, 255)], n=12, shape='dot')),
    'treant': dict(fn=treant, F=96, sh=(26, 24), stride=24, hit=4, role='Tank / Elite', env='Grassland', speed='Slow (heavy stomp)',
                   look='Walking tree: big leafy crown from above, bark trunk with glowing eyes, branch arms with leaf hands.',
                   move='Heavy steps with alternating root feet, arms and crown sway.', attack='Pulls branch arms back, then slams them forward and sends out a ground shockwave.',
                   death=dict(sc=0.85, spin=0, cols=[(84, 168, 70, 255), (152, 218, 98, 255), (124, 84, 54, 255)], n=26, shape='leaf', rmax=40, puddle=False, stars=False),
                   spawn=dict(cols=[(84, 168, 70, 255), (152, 218, 98, 255), (124, 84, 54, 255)], n=18, shape='leaf')),
}
DIRS = {'E': 0, 'S': 90, 'W': 180, 'N': 270}
ANIMS = {'idle': (6, 'idle', 8, True), 'walk': (8, 'walk', 12, True), 'attack': (8, 'atk', 14, False), 'hit': (4, 'hit', 12, False)}

def burst(F, t, cols, n, seed, rmax, shape, rmin=6, size=3):
    r = random.Random(seed); im = Image.new('RGBA', (F * S, F * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = F / 2
    for _ in range(n):
        a = r.random() * 6.2832; q = rmin + (rmax - rmin) * (t ** 0.7) * r.uniform(.6, 1); sz = size * r.uniform(.6, 1.4) * (1 - t * .45)
        col = r.choice(cols); x, y = c + math.cos(a) * q, c + math.sin(a) * q
        if shape == 'leaf':
            rot = r.uniform(0, 6.28); pts = [((x + math.cos(rot) * sz * 1.5 * math.cos(u) - math.sin(rot) * sz * 0.8 * math.sin(u)) * S,
                                              (y + math.sin(rot) * sz * 1.5 * math.cos(u) + math.cos(rot) * sz * 0.8 * math.sin(u)) * S) for u in [i / 10 * 6.2832 for i in range(10)]]
            d.polygon(pts, fill=col)
        elif shape == 'puff': d.ellipse(((x - sz * 1.3) * S, (y - sz * 1.3) * S, (x + sz * 1.3) * S, (y + sz * 1.3) * S), fill=col)
        else: d.ellipse(((x - sz) * S, (y - sz) * S, (x + sz) * S, (y + sz) * S), fill=col, outline=OUT, width=int(0.7 * S))
    if shape == 'puff': im = im.filter(ImageFilter.GaussianBlur(S * 0.8))
    return fade(im.resize((F, F), Image.LANCZOS), 1 - sm(0.5, 1.0, t))

def ring(F, t, col, rmax):
    im = Image.new('RGBA', (F * S, F * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = F / 2; r = 4 + t * rmax
    d.ellipse(((c - r) * S, (c - r) * S, (c + r) * S, (c + r) * S), outline=col[:3] + (int(230 * (1 - t)),), width=int(max(1, 3 * (1 - t) + 1) * S))
    return im.resize((F, F), Image.LANCZOS)

def stars_layer(F, t, n=3):
    im = Image.new('RGBA', (F * S, F * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        a = t * 9 + i / n * 6.2832; star4(d, F / 2 + math.cos(a) * F * 0.2, F / 2 + math.sin(a) * F * 0.2 * 0.7 - F * 0.05, 3.2, (255, 224, 90, 255))
    return im.resize((F, F), Image.LANCZOS)

def spawn_frames(name, n=10):
    m = MON[name]; F = m['F']; base = m['fn'](0, 'idle', 0); out = []; cfg = m['spawn']
    for i in range(n):
        t = i / (n - 1); s = lerp(0.12, 1, back(clamp(t / 0.72))); fr = xform(base, s, 0, 0, 0, clamp(t * 3.5))
        fr = comp(ring(F, t, cfg['cols'][0], F * 0.45), fr)
        if 0.08 < t < 0.98: fr = comp(fr, burst(F, clamp(t * 0.95 + 0.05), cfg['cols'], cfg['n'], 21, F * 0.42, cfg['shape'], 8, 3 if F < 90 else 3.6))
        out.append(fr)
    return out

def death_frames(name, ang, n=10):
    m = MON[name]; F = m['F']; fn = m['fn']; cfg = m['death']; a = math.radians(ang); out = []
    for i in range(n):
        t = i / (n - 1)
        if t < 0.3: src = fn(ang, 'hit', clamp(t / 0.3)); u = 0.0
        else: src = fn(ang, 'hit', 1.0); u = (t - 0.3) / 0.7
        im = xform(src, lerp(1, cfg['sc'], u), -math.cos(a) * 6 * u, -math.sin(a) * 6 * u, cfg['spin'] * u, 1 - sm(0.35, 1.0, u))
        if cfg['puddle'] and t > 0.28:
            pl = Cx(F, 0); al = int(210 * (1 - sm(0.2, 1, u)))
            pl.ell(0, 0, 14 + 9 * u, 12 + 7 * u, (96, 204, 100, al), (40, 118, 64, al), 1.4)
            for k_ in range(5):
                aa = k_ / 5 * 6.28 + 0.4; pl.circ(math.cos(aa) * (16 + 8 * u), math.sin(aa) * (14 + 7 * u), 2.4, (96, 204, 100, al), None)
            im = comp(pl.out(), im)
        if cfg['stars'] and t < 0.75: im = comp(im, fade(stars_layer(F, t), 1 - sm(0.4, 0.75, t)))
        if t > 0.18: im = comp(im, burst(F, clamp((t - 0.18) / 0.82), cfg['cols'], cfg['n'], 33, cfg['rmax'], cfg['shape'], 6, 3 if F < 90 else 3.6))
        out.append(im)
    return out

def shadow_img(F, rx, ry):
    im = Image.new('RGBA', (F * S, F * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = F / 2
    d.ellipse(((c - rx + 1.5) * S, (c - ry + 3.5) * S, (c + rx + 1.5) * S, (c + ry + 3.5) * S), fill=(20, 40, 20, 80))
    return im.filter(ImageFilter.GaussianBlur(S * 1.1)).resize((F, F), Image.LANCZOS)


def save_gif(frames, durs, path):
    step = max(1, len(frames) // 10); samp = frames[::step][:12]
    w, h = samp[0].size; mos = Image.new('RGB', (w, h * len(samp)))
    for i, f in enumerate(samp): mos.paste(f, (0, i * h))
    pal = mos.quantize(colors=250, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=1, optimize=True)

# ================================================================== BUILD
FR = {}; SH = {}
ROWORDER = ([('idle', d) for d in DIRS] + [('walk', d) for d in DIRS] + [('attack', d) for d in DIRS] + [('hit', d) for d in DIRS] +
            [('death', d) for d in DIRS] + [('spawn', 'E')])
COLS = 10
for name, m in MON.items():
    F = m['F']; fo = f"{ROOT}/Monsters/Grassland/{name.capitalize()}"
    SH[name] = shadow_img(F, *m['sh']); SH[name].save(f'{fo}/monster_{name}_shadow.png')
    for an, (n, mode, fps, loop) in ANIMS.items():
        for dn, a in DIRS.items():
            fr = [m['fn'](a, mode, (i / n) if mode in ('idle', 'walk') else i / (n - 1)) for i in range(n)]
            FR[(name, an, dn)] = fr
    for dn, a in DIRS.items(): FR[(name, 'death', dn)] = death_frames(name, a)
    FR[(name, 'spawn', 'E')] = spawn_frames(name)
    sheet = Image.new('RGBA', (F * COLS, F * len(ROWORDER)), (0, 0, 0, 0))
    atlas = {'monster': name, 'frame_px': F, 'pivot': [F // 2, F // 2], 'columns': COLS, 'rows': {}, 'walk_stride_px_per_cycle': m['stride'],
             'attack_hit_frame': 4, 'directions': {'E': 'right', 'S': 'down', 'W': 'left', 'N': 'up'}, 'shadow': f'monster_{name}_shadow.png (separate)'}
    for r, (an, dn) in enumerate(ROWORDER):
        fr = FR[(name, an, dn)]
        for i, f in enumerate(fr): sheet.paste(f, (i * F, r * F))
        fps, loop = {'idle': (8, True), 'walk': (12, True), 'attack': (14, False), 'hit': (12, False), 'death': (12, False), 'spawn': (12, False)}[an]
        atlas['rows'][f'{an}_{dn}'] = dict(row=r, y=r * F, frames=len(fr), fps=fps, loop=loop, duration_s=round(len(fr) / fps, 3))
    sheet.save(f'{fo}/monster_{name}_spritesheet.png')
    LM_, TH = 120, 28; lab = Image.new('RGB', (LM_ + F * COLS, TH + F * len(ROWORDER)), (52, 60, 72)); dl = ImageDraw.Draw(lab)
    dl.text((LM_, 6), f'{name.upper()}  -  {m["role"]}  -  frame {F}x{F}, pivot center', fill=(255, 255, 255), font=FONT)
    for r, (an, dn) in enumerate(ROWORDER):
        dl.text((8, TH + r * F + F // 2 - 8), f'{an.upper()} {dn}', fill=(255, 224, 140), font=FONT)
        dl.line((LM_, TH + r * F, LM_ + F * COLS, TH + r * F), fill=(80, 90, 104))
    lab.paste(sheet, (LM_, TH), sheet); lab.save(f'{fo}/monster_{name}_spritesheet_LABELED.png')
    json.dump(atlas, open(f'{ROOT}/Documentation/monster_{name}_atlas.json', 'w'), indent=1)
    for (an, dn), r in [((a_, d_), 0) for a_, d_ in ROWORDER]:
        pass
    for an, dn in ROWORDER:
        fr = FR[(name, an, dn)]; Image.fromarray if False else None
        strip = Image.new('RGBA', (F * len(fr), F), (0, 0, 0, 0))
        for i, f in enumerate(fr): strip.paste(f, (i * F, 0))
        os.makedirs(f'{fo}/Strips', exist_ok=True); strip.save(f'{fo}/Strips/monster_{name}_{an}_{dn}.png')

# ================================================================== PREVIEWS
atl = Image.open(f'{ROOT}/Environment/Grassland/grassland_tileset_32.png')
gt = [atl.crop((i * 32, 0, i * 32 + 32, 32)) for i in range(8)]
def grass_bg(w, h, seed=2):
    r = random.Random(seed); bg = Image.new('RGBA', (w, h))
    for y in range(0, h, 32):
        for x in range(0, w, 32): bg.paste(gt[r.randrange(8)], (x, y))
    return bg
# overview
CELL = 112; ov = grass_bg(CELL * 4 + 8, CELL * 5 + 30, 5); dd = ImageDraw.Draw(ov)
for r_, name in enumerate(NAMES):
    F = MON[name]['F']
    for c_, dn in enumerate(DIRS):
        x, y = c_ * CELL + 4 + (CELL - F) // 2, r_ * CELL + 26 + (CELL - F) // 2
        put(ov, SH[name], x, y); put(ov, FR[(name, 'idle', dn)][0], x, y)
    dd.text((6, r_ * CELL + 8), f'{name.upper()}  ({MON[name]["role"]})', fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(30, 30, 30, 255))
ov.resize((ov.width * 2, ov.height * 2), Image.BICUBIC).convert('RGB').save(f'{ROOT}/Monsters/Preview/monsters_overview_4dir.png')

# per-monster demo
def stage_demo(name, path, scale=2):
    m = MON[name]; F = m['F']; W, H, BAN = 320, 180, 24
    bg = grass_bg(W, H, 7 + len(name)); frames, durs = [], []
    def emit(label, spr, x, y, dur):
        im = bg.copy(); put(im, SH[name], x - F / 2, y - F / 2); put(im, spr, x - F / 2, y - F / 2)
        out = Image.new('RGB', (W, H + BAN), (30, 34, 42)); out.paste(im.convert('RGB'), (0, BAN))
        ImageDraw.Draw(out).text((8, 4), f'{name.upper()}  -  {label}', fill=(255, 226, 140), font=FONT)
        out = out.resize((W * scale, (H + BAN) * scale), Image.BICUBIC); frames.append(out); durs.append(dur)
    P0 = (60, 60)
    for i, f in enumerate(FR[(name, 'spawn', 'E')]): emit('SPAWN', f, *P0, 83)
    for i in range(12): emit('IDLE', FR[(name, 'idle', 'E')][i % 6], *P0, 125)
    wps = [(60, 60, 'E'), (260, 60, 'S'), (260, 130, 'W'), (60, 130, 'N'), (60, 60, 'E')]
    sp = m['stride'] / 8 * 1.0; dist = 0.0
    for (x0, y0, dn), (x1, y1, _) in zip(wps, wps[1:]):
        L = math.hypot(x1 - x0, y1 - y0); u = 0.0
        while u < L:
            x = x0 + (x1 - x0) * u / L; y = y0 + (y1 - y0) * u / L
            emit(f'WALK  facing {dn}', FR[(name, 'walk', dn)][int(dist / sp) % 8], x, y, 80); u += sp * 1.0; dist += sp * 1.0
    for _ in range(2):
        for f in FR[(name, 'attack', 'E')]: emit('ATTACK', f, *P0, 70)
        for _ in range(2): emit('ATTACK', FR[(name, 'idle', 'E')][0], *P0, 120)
    for f in FR[(name, 'hit', 'E')]: emit('HIT REACTION', f, *P0, 83)
    for _ in range(3): emit('IDLE', FR[(name, 'idle', 'E')][0], *P0, 120)
    for f in FR[(name, 'death', 'E')]: emit('DEATH', f, *P0, 90)
    save_gif(frames, durs, path)
for name in NAMES: stage_demo(name, f'{ROOT}/Monsters/Preview/DEMO_{name}_all_animations.gif')

# map demo
PP = f'{ROOT}/Environment/Grassland/Preview/layers'
ld = lambda n: Image.open(f'{PP}/layer_{n}.png').convert('RGBA')
mp = comp(ld('1_ground'), ld('2_water'), ld('3_path'), ld('4_path_decals'), ld('5_small_decor'), ld('6_objects'), ld('7_grid'))
cellc = lambda x, y: ((x + .5) * 64, (y + .5) * 64)
def tower_on_map(folder, tn, L, cx, cy, tgt):
    fo = f'{ROOT}/Towers/{folder}'; x, y = cellc(cx, cy); a = math.degrees(math.atan2(tgt[1] - y, tgt[0] - x))
    sh = Image.open(f'{fo}/tower_{tn}_shadow.png'); b = Image.open(f'{fo}/tower_{tn}_level_{L:02d}_base.png'); h = Image.open(f'{fo}/tower_{tn}_level_{L:02d}_head_static.png')
    if tn != 'frost': h = h.rotate(-a, resample=Image.BICUBIC)
    mp.alpha_composite(sh, (int(x - 48), int(y - 48))); mp.alpha_composite(b, (int(x - 48), int(y - 48))); mp.alpha_composite(h, (int(x - 48), int(y - 48)))
tower_on_map('Archer', 'archer', 3, 5, 3, cellc(4, 5)); tower_on_map('Stone', 'stone', 4, 10, 6, cellc(9, 5)); tower_on_map('Frost', 'frost', 5, 13, 4, cellc(14, 5))
corners = [(-1, 2), (0, 2), (4, 2), (4, 8), (9, 8), (9, 3), (14, 3), (14, 9), (19, 9)]
PL = [cellc(*c) for c in corners]; SEG = []; tot = 0
for a, b in zip(PL, PL[1:]):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); SEG.append((a, b, tot, L)); tot += L
def pos_at(d):
    for a, b, s0, L in SEG:
        if d <= s0 + L:
            u = (d - s0) / L; dx, dy = b[0] - a[0], b[1] - a[1]
            dn = 'E' if dx > 0 else 'W' if dx < 0 else 'S' if dy > 0 else 'N'
            return a[0] + dx * u, a[1] + dy * u, dn
    return None
sched = [('slime', 9, 0), ('goblin', 12, 14), ('boar', 18, 30), ('mushroom', 8, 44), ('treant', 6, 56)]
NF, SC = 120, 0.65; frames = []
for f in range(NF):
    im = mp.copy(); items = []
    for name, spd, st in sched:
        if f < st: continue
        loc = f - st; F = MON[name]['F']
        if loc < 10: x, y = PL[1]; items.append((y, name, FR[(name, 'spawn', 'E')][loc], x, y))
        else:
            dist = (loc - 10) * spd + 64; p = pos_at(dist)
            if not p: continue
            x, y, dn = p; idx = int((loc - 10) * spd / (MON[name]['stride'] / 8)) % 8
            items.append((y, name, FR[(name, 'walk', dn)][idx], x, y))
    for y, name, spr, x, yy in sorted(items, key=lambda t: t[0]):
        F = MON[name]['F']; put(im, SH[name], x - F / 2, yy - F / 2); put(im, spr, x - F / 2, yy - F / 2)
    im = im.convert('RGB').resize((int(1280 * SC), int(768 * SC)), Image.BICUBIC)
    ImageDraw.Draw(im).text((10, 8), 'GRASSLAND MONSTERS  -  Slime / Goblin / Wild Boar / Mushroom / Treant', fill=(255, 255, 255), font=FONT, stroke_width=2, stroke_fill=(30, 30, 30))
    frames.append(im)
save_gif(frames, [45] * len(frames), f'{ROOT}/Monsters/Preview/DEMO_all_monsters_walking_on_map.gif')

# docs
md = ['# Grassland Monsters (Phase 4)\n', 'Top-down, frames drawn facing EAST then re-drawn for S/W/N (lighting stays top-left). Shadows are separate PNGs.\n',
      '| Monster | Role | Frame | Walk stride (px/cycle) | Look | Movement | Attack |', '|---|---|---|---|---|---|---|']
for n, m in MON.items(): md.append(f"| {n.capitalize()} | {m['role']} | {m['F']}x{m['F']} | {m['stride']} | {m['look']} | {m['move']} | {m['attack']} |")
md += ['\n## Animations (every monster)\n', '| Anim | Frames | FPS | Loop | Directions |', '|---|---|---|---|---|', '| idle | 6 | 8 | yes | E S W N |', '| walk | 8 | 12 | yes | E S W N |',
       '| attack | 8 | 14 | no | E S W N (damage event frame 4) |', '| hit | 4 | 12 | no | E S W N |', '| death | 10 | 12 | no | E S W N (last frame ~empty, despawn) |', '| spawn | 10 | 12 | no | E only (at spawn point) |',
       '\nSheet: 10 columns, 21 rows: idle x4, walk x4, attack x4, hit x4, death x4, spawn. Pivot = frame center. See Documentation/monster_<name>_atlas.json.']
open(f'{ROOT}/Documentation/MONSTERS_GRASSLAND.md', 'w').write('\n'.join(md))
import zipfile
with zipfile.ZipFile('/mnt/user-data/outputs/GameAssets_Phase4_Monsters.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for sub in ['Monsters', 'Documentation']:
        for dp, _, fs in os.walk(f'{ROOT}/{sub}'):
            for f in fs: z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), ROOT))
print('done')
