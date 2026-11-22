import os, math, random, json
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S, F = 4, 96
C = F / 2
ROOT = '/mnt/user-data/outputs/GameAssets'
OUT = (52, 40, 50, 255)
for n in ['Stone', 'Archer', 'Frost']: os.makedirs(f'{ROOT}/Towers/{n}', exist_ok=True)
os.makedirs(f'{ROOT}/Projectiles', exist_ok=True); os.makedirs(f'{ROOT}/VFX', exist_ok=True)
os.makedirs(f'{ROOT}/Towers/Preview', exist_ok=True)

# ------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def canvas(w=F, h=None): return Image.new('RGBA', (w * S, (h or w) * S), (0, 0, 0, 0))
def fin(im, w=F, h=None): return im.resize((w, h or w), Image.LANCZOS)
def circ(d, cx, cy, r, fill, out=OUT, ow=1.3):
    if out: d.ellipse(((cx - r - ow) * S, (cy - r - ow) * S, (cx + r + ow) * S, (cy + r + ow) * S), fill=out)
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=fill)
def poly(d, pts, fill, out=OUT, ow=1.3):
    q = [(x * S, y * S) for x, y in pts]
    d.polygon(q, fill=fill)
    if out: d.line(q + [q[0]], fill=out, width=int(ow * S), joint='curve')
def rrect(d, cx, cy, w, h, ang, fill, out=OUT, ow=1.2):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]
    poly(d, pts, fill, out, ow)
def line(d, p, q, col, w): d.line((p[0] * S, p[1] * S, q[0] * S, q[1] * S), fill=col, width=int(w * S))
def arc(d, cx, cy, r, a0, a1, col, w):
    d.arc(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), a0, a1, fill=col, width=int(w * S))
def glow(cx, cy, r, col, a):
    l = canvas(); d = ImageDraw.Draw(l)
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=col + (int(a),))
    return l.filter(ImageFilter.GaussianBlur(r * S * 0.45))
def fade(im, a):
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a))); return im
def xform(im, s=1.0, dx=0, dy=0, ang=0, alpha=1.0):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    if s < 0.02 or alpha <= 0: return out
    if ang: im = im.rotate(ang, resample=Image.BICUBIC)
    w = max(2, int(im.width * s)); r = im.resize((w, w), Image.LANCZOS)
    if alpha < 1: r = fade(r, alpha)
    out.alpha_composite(r, (int(im.width / 2 + dx - w / 2), int(im.height / 2 + dy - w / 2))) if True else None
    return out
def comp(*ims):
    o = Image.new('RGBA', ims[0].size, (0, 0, 0, 0))
    for i in ims: o.alpha_composite(i)
    return o
def strip(frames):
    w, h = frames[0].size; s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames): s.paste(f, (i * w, 0))
    return s

# palette
WALL, WALL_L, FLOOR = (150, 154, 172, 255), (196, 200, 214, 255), (206, 208, 220, 255)
WOOD, WOOD_D, WOOD_L = (178, 122, 70, 255), (118, 76, 44, 255), (220, 168, 106, 255)
GOLD, RED = (255, 210, 84, 255), (226, 66, 74, 255)
ICE, ICE_L, ICE_D = (140, 218, 252, 255), (226, 248, 255, 255), (64, 142, 222, 255)

# ------------------------------------------------------------ STONE
def stone_base(L, t=0.0):
    im = canvas(); d = ImageDraw.Draw(im); R = (26, 27, 27, 28, 29)[L - 1]; r = random.Random(11)
    circ(d, C, C, R, WALL, OUT, 1.5)
    for _ in range(26):
        a, q = r.random() * 6.283, R - 1 - r.random() * 5
        circ(d, C + math.cos(a) * q, C + math.sin(a) * q, 0.7, (126, 130, 150, 255), None)
    if L == 1:
        for k in range(4): arc(d, C, C, R - 3, 20 + 90 * k, 70 + 90 * k, WOOD, 3)
    else: arc(d, C, C, R - 3, 0, 360, WOOD, 3)
    if L >= 3: arc(d, C, C, R - 0.6, 0, 360, GOLD, 1.4 + (0.6 if L == 5 else 0))
    circ(d, C, C, R - 6, FLOOR, OUT, 1.0)
    for _ in range(7):
        a = r.random() * 6.283; q = 6 + r.random() * 9
        x, y = C + math.cos(a) * q, C + math.sin(a) * q
        line(d, (x, y), (x + r.randint(-3, 3), y + r.randint(-3, 3)), (170, 172, 188, 255), 0.9)
    if L >= 3:
        arc(d, C, C, 14, 0, 360, GOLD, 1.0)
        for k in range(6):
            a = k / 6 * 6.283; circ(d, C + math.cos(a) * 14, C + math.sin(a) * 14, 1.3, GOLD, None)
    tur = (0, 20, 20, 21, 22)[L - 1]
    if L >= 4:
        arc(d, C, C, 16.5, 0, 360, WALL_L, 2.6); arc(d, C, C, 16.5, 0, 360, OUT, 0.5)
        for k in range(8):
            a = k / 8 * 6.283; circ(d, C + math.cos(a) * 16.5, C + math.sin(a) * 16.5, 1.7, GOLD, OUT, 0.6)
    if L == 5:
        im = comp(im, glow(C, C, 14, (255, 150, 60), 120)); d = ImageDraw.Draw(im)
        arc(d, C, C, 11, 0, 360, (255, 160, 70, 255), 1.6)
        for k in range(8):
            a = k / 8 * 6.283 + 0.4; circ(d, C + math.cos(a) * 11, C + math.sin(a) * 11, 1.2, (255, 236, 160, 255), None)
    if L >= 2:
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = C + sx * tur, C + sy * tur
                tr = 7.2 if L >= 4 else 6.4
                circ(d, x, y, tr, WALL, OUT, 1.3); circ(d, x, y, tr - 2.8, WALL_L, OUT, 0.9)
                if L >= 3: circ(d, x, y, 1.3 + (0.8 if L >= 4 else 0), GOLD, None)
                if L == 5:
                    for k in range(6):
                        a = k / 6 * 6.283
                        poly(d, [(x, y), (x + math.cos(a) * tr, y + math.sin(a) * tr), (x + math.cos(a + 1.0) * tr, y + math.sin(a + 1.0) * tr)], RED if k % 2 == 0 else GOLD, None)
                    circ(d, x, y, 1.6, GOLD, OUT, 0.6)
    n = (8, 10, 12, 12, 14)[L - 1]
    for i in range(n):
        a = i / n * 6.283 + 3.1416 / n
        x, y = C + math.cos(a) * (R - 1.5), C + math.sin(a) * (R - 1.5)
        rrect(d, x, y, 6.5, 6.5, math.degrees(a), WALL_L, OUT, 1.1)
        if L >= 3: circ(d, x, y, 1.4, GOLD, None)
    # flag (animated)
    px, py = C - 11, C - 13; wv = math.sin(t * 6.283)
    ln = 13 + (3 if L >= 3 else 0) + (2 if L == 5 else 0); col = GOLD if L >= 3 else RED
    tip = (px - ln + wv * 1.5, py - 2 + wv * 3.2)
    poly(d, [(px, py - 3.2), (tip[0], tip[1] - 1.2), (tip[0] + 2.5, tip[1] + 2.2), (px, py + 3.2)], col, OUT, 1.0)
    circ(d, px, py, 1.9, WOOD_D, OUT, 0.9)
    if L >= 4:
        px2, py2 = C + 11, C - 13; tip2 = (px2 + ln - wv * 1.5, py2 - 2 - wv * 3.2)
        poly(d, [(px2, py2 - 3.2), (tip2[0], tip2[1] - 1.2), (tip2[0] - 2.5, tip2[1] + 2.2), (px2, py2 + 3.2)], RED, OUT, 1.0)
        circ(d, px2, py2, 1.9, WOOD_D, OUT, 0.9)
    return fin(im)

def stone_head(L, off=0.0, loaded=True, puff=0.0):
    im = canvas(); d = ImageDraw.Draw(im)
    wd = (5.0, 6.5, 7.5, 8.5, 9.5)[L - 1]; ln = (17, 19, 21, 22, 23)[L - 1]
    rrect(d, C - 5, C, 15, 17, 0, WOOD_D, OUT, 1.2)
    for yy in (-5.5, 5.5): circ(d, C - 9, C + yy, 1.2, (190, 194, 206, 255), None)
    if L >= 4: rrect(d, C - 11, C, 3, 15, 0, GOLD, OUT, 0.7)
    rrect(d, C + 3 + off + ln / 2 - 8, C, ln, wd, 0, WOOD, OUT, 1.2)
    line(d, (C + off - 4, C - wd / 2 + 1), (C + off + ln - 6, C - wd / 2 + 1), WOOD_L, 0.9)
    if L >= 2:
        for k in (0.35, 0.7): rrect(d, C + off + ln * k - 4, C, 1.8, wd + 1.6, 0, (170, 174, 190, 255), OUT, 0.7)
    if L >= 3:
        rrect(d, C + off + 4, C, 1.6, wd + 1.6, 0, GOLD, OUT, 0.7)
    if L >= 4: rrect(d, C + off + ln * 0.55, C, 1.6, wd + 1.6, 0, GOLD, OUT, 0.7)
    bx = C + 3 + off + ln - 8
    br = (6.2, 6.2, 7, 7.6, 8.2)[L - 1]; circ(d, bx, C, br, WOOD_D, OUT, 1.3); circ(d, bx, C, br - 2, (140, 92, 54, 255), None)
    if loaded:
        sc = [(160, 164, 182, 255)] * 3 + [(112, 116, 134, 255), (255, 142, 60, 255)]
        circ(d, bx, C, br - 2.4, sc[L - 1], OUT, 1.0)
        circ(d, bx - 1.1, C - 1.1, 1.4, (255, 236, 170, 255) if L == 5 else (214, 218, 230, 255), None)
    circ(d, C - 2, C, 4.6, (96, 98, 116, 255), OUT, 1.2); circ(d, C - 2, C, 1.7, (200, 204, 216, 255), None)
    im = fin(im)
    if puff > 0:
        l = canvas(); dd = ImageDraw.Draw(l)
        for k, (ox, oy) in enumerate([(0, 0), (4, -5), (4, 5), (9, 0)]):
            rr = 4 + puff * 5
            dd.ellipse(((bx + 6 + ox * puff - rr) * S, (C + oy * puff - rr) * S, (bx + 6 + ox * puff + rr) * S, (C + oy * puff + rr) * S),
                       fill=(240, 232, 214, int(210 * (1 - puff * 0.7))))
        im = comp(im, fin(l.filter(ImageFilter.GaussianBlur(S * 0.6))))
    return im

STONE_ATT = dict(off=[-1, -3, -4, 5, 2, -2, -1, 0], loaded=[1, 1, 1, 0, 0, 0, 1, 1], puff=[0, 0, 0, .35, .7, 1, 0, 0])
def stone_attack(L): return [stone_head(L, STONE_ATT['off'][i], bool(STONE_ATT['loaded'][i]), STONE_ATT['puff'][i]) for i in range(8)]

# ------------------------------------------------------------ ARCHER
def archer_base(L):
    im = canvas(); d = ImageDraw.Draw(im); half = (23, 25, 27, 28, 29)[L - 1]
    pw = 2 * half / 7
    d.rounded_rectangle(((C - half - 1.5) * S, (C - half - 1.5) * S, (C + half + 1.5) * S, (C + half + 1.5) * S), radius=4 * S, fill=OUT)
    for k in range(7):
        x0 = C - half + k * pw
        d.rectangle((x0 * S, (C - half) * S, (x0 + pw) * S, (C + half) * S), fill=(186, 130, 74, 255) if k % 2 == 0 else (172, 116, 66, 255))
        line(d, (x0, C - half), (x0, C + half), WOOD_D, 0.9)
    d.rounded_rectangle(((C - half) * S, (C - half) * S, (C + half) * S, (C + half) * S), radius=3 * S, outline=WOOD_D, width=int(3.2 * S))
    d.rounded_rectangle(((C - half + 1) * S, (C - half + 1) * S, (C + half - 1) * S, (C + half - 1) * S), radius=2 * S, outline=WOOD_L, width=int(0.8 * S))
    if L >= 2:
        h2 = half - 5
        d.rounded_rectangle(((C - h2) * S, (C - h2) * S, (C + h2) * S, (C + h2) * S), radius=2 * S, outline=(200, 148, 90, 255), width=int(1.4 * S))
        for p in [(0, -h2), (0, h2), (-h2, 0), (h2, 0)]: circ(d, C + p[0], C + p[1], 1.6, WOOD_D, OUT, 0.7)
        qx, qy = C - half + 9, C + half - 9
        rrect(d, qx, qy, 8, 8, 0, WOOD_D, OUT, 1.0)
        for k in range(3): line(d, (qx - 2.5 + k * 2.5, qy), (qx - 2.5 + k * 2.5 + 0.8, qy - 6), (230, 226, 210, 255), 0.9)
    if L >= 3:
        for p in [(0, -half), (0, half), (-half, 0), (half, 0)]:
            circ(d, C + p[0], C + p[1], 3.4, RED, OUT, 1.0); circ(d, C + p[0], C + p[1], 1.4, GOLD, None)
        bx, by = C - half + 5, C - half + 5
        poly(d, [(bx - 3, by - 3), (bx + 12, by - 3), (bx + 12, by + 7), (bx + 4.5, by + 12), (bx - 3, by + 7)], RED, OUT, 1.1)
        circ(d, bx + 4.5, by + 3, 2.3, GOLD, OUT, 0.7)
    if L >= 4:
        bx2, by2 = C + half - 5, C - half + 5
        poly(d, [(bx2 + 3, by2 - 3), (bx2 - 12, by2 - 3), (bx2 - 12, by2 + 7), (bx2 - 4.5, by2 + 12), (bx2 + 3, by2 + 7)], RED, OUT, 1.1)
        circ(d, bx2 - 4.5, by2 + 3, 2.3, GOLD, OUT, 0.7)
        for sx in (-1, 1):
            circ(d, C + sx * (half - 9), C + half - 3.5, 2.4, (120, 220, 250, 255), OUT, 0.8)
        d.rounded_rectangle(((C - half + 2) * S, (C - half + 2) * S, (C + half - 2) * S, (C + half - 2) * S), radius=2 * S, outline=GOLD, width=int(0.9 * S))
    if L == 5:
        arc(d, C, C, 17, 0, 360, GOLD, 1.4)
        for k in range(8):
            a = k / 8 * 6.283 + 0.3; circ(d, C + math.cos(a) * 17, C + math.sin(a) * 17, 1.2, GOLD, None)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx0, cy0 = C + sx * half, C + sy * half
                poly(d, [(cx0, cy0), (cx0 - sx * 15, cy0), (cx0, cy0 - sy * 15)], RED, GOLD, 1.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            circ(d, C + sx * half, C + sy * half, 5, WOOD_D, OUT, 1.3); circ(d, C + sx * half - 0.6, C + sy * half - 0.6, 3, WOOD_L, None)
            if L >= 3: circ(d, C + sx * half - 0.6, C + sy * half - 0.6, 1.4 + (0.8 if L >= 4 else 0), GOLD, None)
    return fin(im)

def archer_head(L, pull=0.0, arrow=True):
    im = canvas(); d = ImageDraw.Draw(im)
    TUN, TUN_D, SKIN = (96, 166, 88, 255), (60, 120, 66, 255), (246, 206, 164, 255)
    bowc = (C - 2, C); R = (15, 15, 16, 17, 18)[L - 1]
    tipu, tipd = (bowc[0] + R * math.cos(math.radians(-55)), bowc[1] + R * math.sin(math.radians(-55))), (bowc[0] + R * math.cos(math.radians(55)), bowc[1] + R * math.sin(math.radians(55)))
    v = (tipu[0] - pull, C); grip = (bowc[0] + R, C)
    if L == 5: im = comp(im, glow(v[0] + 11, C, 9, (120, 230, 255), 150)); d = ImageDraw.Draw(im)
    if L >= 4:
        poly(d, [(C - 3, C - 10), (C - 15, C - 4), (C - 17, C), (C - 15, C + 4), (C - 3, C + 10)], (70, 110, 190, 255) if L == 4 else (120, 70, 170, 255), OUT, 1.1)
    if L >= 2: rrect(d, C - 7, C - 3, 3.2, 13, 18, WOOD_D, OUT, 0.9)
    d.ellipse(((C - 1 - 6) * S, (C - 11) * S, (C - 1 + 6) * S, (C + 11) * S), fill=OUT)
    d.ellipse(((C - 1 - 5) * S, (C - 10) * S, (C - 1 + 5) * S, (C + 10) * S), fill=TUN)
    if L >= 3: arc(d, C - 1, C, 5.4, 100, 260, GOLD, 1.4)
    for tgt, sy in [(grip, 1), (v, -1)]:
        sh = (C + 0.5, C + sy * 8)
        line(d, sh, (tgt[0], tgt[1] + sy * 0.4), OUT, 4.6); line(d, sh, (tgt[0], tgt[1] + sy * 0.4), TUN_D, 3.2)
    if L == 5:
        for sy in (-1, 1): circ(d, C + 0.5, C + sy * 8, 2.8, GOLD, OUT, 0.8)
    arc(d, bowc[0], bowc[1], R, -55, 55, OUT, 4.6); arc(d, bowc[0], bowc[1], R, -55, 55, (166, 106, 58, 255) if L < 3 else (226, 176, 70, 255), 2.8)
    for p in (tipu, tipd): circ(d, p[0], p[1], 1.5, (120, 220, 250, 255) if L >= 3 else WOOD_D, OUT if L < 3 else None, 0.8)
    strc = (244, 242, 232, 255) if L < 5 else (170, 240, 255, 255)
    line(d, tipu, v, strc, 0.9); line(d, v, tipd, strc, 0.9)
    if arrow:
        tx = v[0] + 24
        line(d, v, (tx, C), OUT, 2.2); line(d, v, (tx, C), (160, 118, 74, 255) if L < 5 else (170, 240, 255, 255), 1.2)
        poly(d, [(tx + 4, C), (tx - 1, C - 2.6), (tx - 1, C + 2.6)], (214, 218, 228, 255), OUT, 0.8)
        for sy in (-1, 1): poly(d, [(v[0] + 1, C), (v[0] + 5, C + sy * 3), (v[0] + 7, C + sy * 3), (v[0] + 4, C)], RED, None)
    circ(d, grip[0], grip[1], 2.2, SKIN, OUT, 0.9); circ(d, v[0], v[1], 2.2, SKIN, OUT, 0.9)
    circ(d, C + 1, C, 6.4, TUN_D if L < 3 else ((60, 98, 150, 255) if L < 5 else (104, 66, 164, 255)), OUT, 1.3)
    circ(d, C + 4, C, 3.1, SKIN, None)
    if L >= 3: arc(d, C + 1, C, 6.9, 90, 270, GOLD, 1.1)
    if L >= 2: line(d, (C - 2, C - 5), (C - 8, C - 9), RED, 1.6)
    return fin(im)

ARCH_ATT = dict(pull=[0, 2.5, 5, 7, 7.6, -1.6, 0.6, 0], arrow=[1, 1, 1, 1, 1, 0, 0, 1])
def archer_attack(L): return [archer_head(L, ARCH_ATT['pull'][i], bool(ARCH_ATT['arrow'][i])) for i in range(8)]

# ------------------------------------------------------------ FROST
def crystal(d, cx, cy, ang, length, width, br, main, light):
    a = math.radians(ang); u = (math.cos(a), math.sin(a)); vv = (-u[1], u[0])
    tip = (cx + u[0] * (br + length), cy + u[1] * (br + length)); b = (cx + u[0] * br, cy + u[1] * br)
    m = (cx + u[0] * (br + length * 0.35), cy + u[1] * (br + length * 0.35))
    m1, m2 = (m[0] + vv[0] * width / 2, m[1] + vv[1] * width / 2), (m[0] - vv[0] * width / 2, m[1] - vv[1] * width / 2)
    poly(d, [tip, m1, b], light, None); poly(d, [tip, m2, b], main, None)
    poly(d, [tip, m1, b, m2], None, OUT, 1.2) if False else d.line([(p[0] * S, p[1] * S) for p in [tip, m1, b, m2, tip]], fill=(30, 70, 140, 255), width=int(1.2 * S), joint='curve')

def snowflake(d, cx, cy, r, col, w=0.9):
    for k in range(3):
        a = k * math.pi / 3
        line(d, (cx - math.cos(a) * r, cy - math.sin(a) * r), (cx + math.cos(a) * r, cy + math.sin(a) * r), col, w)

def frost_base(L):
    im = canvas(); im = comp(im, glow(C, C, 26, (120, 220, 255), 140)) if L == 5 else im; d = ImageDraw.Draw(im); R = 27
    hx = [(C + R * math.cos(math.radians(30 + 60 * k)), C + R * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    poly(d, hx, (190, 228, 248, 255), (44, 104, 186, 255), 1.6)
    poly(d, [(C + 19 * math.cos(math.radians(30 + 60 * k)), C + 19 * math.sin(math.radians(30 + 60 * k))) for k in range(6)], (216, 242, 253, 255), (110, 170, 226, 255), 1.0)
    for k in range(6):
        a = math.radians(60 * k)
        snowflake(d, C + math.cos(a) * 15, C + math.sin(a) * 15, 3.4, (120, 182, 232, 255))
    if L >= 2:
        for k in range(6): crystal(d, C, C, 60 * k, 11 + (2 if L >= 3 else 0) + (2 if L == 5 else 0), 5.5, 19, ICE, ICE_L)
    for k in range(6):
        crystal(d, C, C, 30 + 60 * k, (13, 15, 17, 19, 21)[L - 1], 8 + (1 if L >= 3 else 0) + (1 if L == 5 else 0), 18, ICE if L < 3 else (110, 206, 252, 255), ICE_L)
    if L >= 3:
        for k in range(6):
            a = math.radians(60 * k); circ(d, C + math.cos(a) * 31, C + math.sin(a) * 31, 1.6, (255, 255, 255, 255), (110, 190, 240, 255), 0.6)
        arc(d, C, C, 12, 0, 360, (150, 220, 255, 255), 1.0)
    if L >= 4:
        arc(d, C, C, 22, 0, 360, (150, 225, 255, 255), 1.2)
        for k in range(6):
            a = math.radians(60 * k + 30); x, y = C + math.cos(a) * 39, C + math.sin(a) * 39
            u = (math.cos(a), math.sin(a)); w = (-u[1], u[0])
            poly(d, [(x + u[0] * 4.2, y + u[1] * 4.2), (x + w[0] * 2.2, y + w[1] * 2.2), (x - u[0] * 4.2, y - u[1] * 4.2), (x - w[0] * 2.2, y - w[1] * 2.2)], ICE_L, (60, 130, 210, 255), 0.9)
    if L == 5:
        arc(d, C, C, 34, 0, 360, (190, 240, 255, 255), 1.0)
    return fin(im)

def frost_head(L, charge=0.0, ang=0.0, burst=-1.0, twinkle=0.0):
    r0 = (7.5, 8.5, 9.5, 10.5, 11.5)[L - 1] * (1 + 0.35 * charge)
    im = canvas(); im = comp(im, glow(C, C, r0 * 2.2, (120, 220, 255), 120 + 110 * charge)); d = ImageDraw.Draw(im)
    def star(r, rot, fill, out):
        pts = []
        for k in range(16):
            a = math.radians(rot + k * 22.5); rr = r if k % 2 == 0 else r * 0.52
            pts.append((C + math.cos(a) * rr, C + math.sin(a) * rr))
        poly(d, pts, fill, out, 1.2)
    if L >= 4: star(r0 * 1.62, -ang, (120, 210, 250, 255), (36, 96, 180, 255))
    star(r0 * 1.25, ang, ICE, (36, 96, 180, 255))
    star(r0 * 0.9, ang + 22.5, ICE_L, None)
    circ(d, C, C, r0 * 0.4, (255, 255, 255, 255), (150, 220, 255, 255), 0.8)
    for k in range(L + 1):
        a = math.radians(ang * 2 + k * 360 / (L + 1)); x, y = C + math.cos(a) * (r0 + 9), C + math.sin(a) * (r0 + 9)
        poly(d, [(x + 3 * math.cos(a), y + 3 * math.sin(a)), (x - 1.8 * math.sin(a), y + 1.8 * math.cos(a)), (x - 3 * math.cos(a), y - 3 * math.sin(a)), (x + 1.8 * math.sin(a), y - 1.8 * math.cos(a))], ICE_L, (60, 130, 210, 255), 0.8)
    if burst >= 0:
        for k in range(8):
            a = math.radians(k * 45 + 22); q = 12 + burst * 14
            crystal(d, C + math.cos(a) * q, C + math.sin(a) * q, math.degrees(a), 5, 3, 0, ICE, ICE_L)
        arc(d, C, C, 10 + burst * 18, 0, 360, (255, 255, 255, int(230 * (1 - burst))), 1.6)
    im = fin(im)
    return im

FROST_ATT = dict(charge=[0, .2, .45, .7, 1, 1, .4, .1], burst=[-1, -1, -1, -1, -1, 0.0, 0.5, -1])
def frost_attack(L): return [frost_head(L, FROST_ATT['charge'][i], i * 6, FROST_ATT['burst'][i]) for i in range(8)]

def twinkles(i, n=8, seed=3):
    im = canvas(); d = ImageDraw.Draw(im); r = random.Random(seed)
    for k in range(6):
        a, q, ph = r.random() * 6.283, 18 + r.random() * 12, r.random()
        al = int(255 * max(0, math.sin((i / n + ph) * 6.283)) ** 2)
        x, y = C + math.cos(a) * q, C + math.sin(a) * q
        snowflake(d, x, y, 2.4, (255, 255, 255, al), 0.9)
    return fin(im)

# ------------------------------------------------------------ rubble / particles
def rubble(kind, seed=5):
    r = random.Random(seed); im = canvas(); d = ImageDraw.Draw(im)
    if kind == 'stone':
        circ(d, C, C, 22, (120, 112, 104, 255), None)
        for _ in range(16):
            a, q = r.random() * 6.283, r.random() * 18
            circ(d, C + math.cos(a) * q, C + math.sin(a) * q, r.uniform(3, 6.5), r.choice([(150, 154, 172, 255), (176, 180, 196, 255), (126, 130, 150, 255)]), OUT, 1.0)
    elif kind == 'wood':
        for _ in range(13):
            a, q = r.random() * 6.283, r.random() * 19
            rrect(d, C + math.cos(a) * q, C + math.sin(a) * q, r.uniform(9, 16), r.uniform(3.2, 5), r.uniform(0, 180), r.choice([WOOD, WOOD_D, WOOD_L]), OUT, 1.0)
        for sx, sy in [(-14, -12), (13, 10)]: circ(d, C + sx, C + sy, 3.2, WOOD_D, OUT, 1.0)
    else:
        d.ellipse(((C - 22) * S, (C - 20) * S, (C + 22) * S, (C + 20) * S), fill=(150, 214, 246, 150))
        for _ in range(13):
            a, q = r.random() * 6.283, r.random() * 17
            crystal(d, C + math.cos(a) * q, C + math.sin(a) * q, r.uniform(0, 360), r.uniform(5, 9), r.uniform(3, 5), 0, ICE, ICE_L)
    return fin(im)

PARTS = {'stone': [(150, 154, 172), (176, 180, 196), (120, 112, 104)], 'wood': [(178, 122, 70), (118, 76, 44), (220, 168, 106)], 'ice': [(140, 218, 252), (226, 248, 255), (64, 142, 222)]}
def particles(kind, tt, seed, n=16, shape='chunk'):
    r = random.Random(seed); im = canvas(); d = ImageDraw.Draw(im)
    if tt <= 0.12: return fin(im)
    for _ in range(n):
        a = r.random() * 6.283; sp = r.uniform(14, 40); sz = r.uniform(1.6, 3.8); col = r.choice(PARTS[kind]) + (255,); rot = r.uniform(0, 360)
        q = sp * (tt - 0.1) ** 0.7 + 8; x, y = C + math.cos(a) * q, C + math.sin(a) * q
        if shape == 'plank': rrect(d, x, y, sz * 3, sz * 0.9, rot + tt * 200, col, OUT, 0.7)
        elif shape == 'shard': crystal(d, x, y, rot + tt * 120, sz * 2.4, sz * 1.3, 0, ICE, ICE_L)
        else: circ(d, x, y, sz, col, OUT, 0.7)
    return fade(fin(im), 1 - sm(0.55, 1.0, tt))

def dust(tt, seed, col=(232, 222, 200), n=9, maxr=30):
    r = random.Random(seed); im = canvas(); d = ImageDraw.Draw(im)
    for k in range(n):
        a = k / n * 6.283 + r.random() * 0.5; q = 8 + tt * maxr * r.uniform(0.7, 1.1); rr = 4 + tt * 6
        d.ellipse(((C + math.cos(a) * q - rr) * S, (C + math.sin(a) * q - rr) * S, (C + math.cos(a) * q + rr) * S, (C + math.sin(a) * q + rr) * S), fill=col + (230,))
    return fade(fin(im.filter(ImageFilter.GaussianBlur(S * 0.8))), 0.85 * (1 - tt) if tt < 1 else 0)

def cracks(intact, seed):
    r = random.Random(seed); l = canvas(); d = ImageDraw.Draw(l)
    for _ in range(6):
        a = r.random() * 6.283; x, y = C, C
        for _ in range(4):
            na = a + r.uniform(-.6, .6); nx, ny = x + math.cos(na) * 8, y + math.sin(na) * 8
            line(d, (x, y), (nx, ny), (40, 32, 40, 255), 1.4); x, y = nx, ny
    l = fin(l); o = comp(intact, l); o.putalpha(intact.split()[3]); return o

def destroyed(intact, kind, shape, n=10, seed=1, rub_seed=5, dust_col=(232, 222, 200), do_dust=True):
    rub = rubble(shape and kind or kind, rub_seed); cr = cracks(intact, seed); out = []
    for i in range(n):
        tt = i / (n - 1)
        ox = math.sin(i * 2.7) * 2.2 * (1 - tt) if i < 6 else 0; oy = math.cos(i * 3.1) * 1.4 * (1 - tt) if i < 6 else 0
        src = cr if tt > 0.12 else intact
        ia = 1 - sm(0.3, 0.75, tt); s = 1 - 0.14 * sm(0.3, 0.8, tt)
        fr = xform(rub, 0.85 + 0.15 * sm(0.4, 1, tt), 0, 0, 0, sm(0.38, 0.95, tt))
        fr = comp(fr, xform(src, s, ox, oy, 0, ia))
        if do_dust and 0.2 < tt < 0.98: fr = comp(fr, dust(tt, seed + i, dust_col))
        out.append(comp(fr, particles('stone' if kind == 'stone' else kind, tt, seed + 7, 16, shape)))
    return out

# ------------------------------------------------------------ spawn
def stone_spawn(L, n=10):
    out = []; base = stone_base(L, 0); head = stone_head(L)
    for i in range(n):
        t = i / (n - 1); s = 0.3 + 0.75 * back(clamp(t / 0.7)) * 0.95 + 0.0
        s = lerp_(0.3, 1.0, back(clamp(t / 0.75)))
        fr = xform(base, s, 0, 0, 0, clamp(t * 3))
        fr = comp(fr, xform(head, lerp_(0.2, 1, back(clamp((t - 0.5) / 0.45))), 0, 0, 0, clamp((t - 0.5) * 4)))
        if t < 0.95: fr = comp(fr, dust(t, 40 + i))
        fr = comp(fr, particles('stone', t * 0.9 + 0.1, 77, 12))
        out.append(fr)
    return out
def lerp_(a, b, t): return a + (b - a) * t

def archer_spawn(L, n=10):
    out = []; base = archer_base(L); head = archer_head(L); q = F // 2
    quads = [((0, 0, q, q), (-38, -38)), ((q, 0, F, q), (38, -38)), ((0, q, q, F), (-38, 38)), ((q, q, F, F), (38, 38))]
    for i in range(n):
        t = i / (n - 1); fr = Image.new('RGBA', (F, F), (0, 0, 0, 0))
        for k, (box, (ox, oy)) in enumerate(quads):
            p = back(clamp((t - k * 0.08) / 0.55)); pc = clamp((t - k * 0.08) / 0.55)
            piece = Image.new('RGBA', (F, F), (0, 0, 0, 0)); piece.paste(base.crop(box), box[:2])
            piece = xform(piece, 1, ox * (1 - p), oy * (1 - p), (1 - p) * (20 if k % 2 else -20), clamp(pc * 4))
            fr.alpha_composite(piece)
        if t > 0.55: fr = comp(fr, xform(head, lerp_(1.5, 1, back(clamp((t - 0.55) / 0.35))), 0, 0, 0, clamp((t - 0.55) * 5)))
        if 0.45 < t < 0.95: fr = comp(fr, dust(clamp((t - 0.4) / 0.6), 9 + i, (214, 186, 140), 7, 26))
        fr = comp(fr, particles('wood', clamp(t * 0.8 + 0.12), 31, 9, 'plank'))
        out.append(fr)
    return out

def frost_spawn(L, n=10):
    out = []; base = frost_base(L); head = frost_head(L)
    for i in range(n):
        t = i / (n - 1); fr = Image.new('RGBA', (F, F), (0, 0, 0, 0))
        for k in range(6):
            m = Image.new('L', (F, F), 0); dm = ImageDraw.Draw(m)
            pts = [(C, C)] + [(C + 80 * math.cos(math.radians(60 * k + a)), C + 80 * math.sin(math.radians(60 * k + a))) for a in (0, 15, 30, 45, 60)]
            dm.polygon(pts, fill=255)
            piece = Image.new('RGBA', (F, F), (0, 0, 0, 0)); piece.paste(base, (0, 0), m)
            sc = lerp_(0.05, 1, back(clamp((t - k * 0.06) / 0.55)))
            fr.alpha_composite(xform(piece, sc, 0, 0, 0, clamp((t - k * 0.06) * 4)))
        if t > 0.5: fr = comp(fr, xform(head, lerp_(0.1, 1, back(clamp((t - 0.5) / 0.4))), 0, 0, 0, clamp((t - 0.5) * 4)))
        fr = comp(fr, twinkles(i * 2, n * 2, 8)) if t > 0.2 else fr
        if 0.3 < t < 0.9: fr = comp(fr, particles('ice', clamp(t * 0.7 + 0.1), 55, 10, 'shard'))
        out.append(fr)
    return out

# ------------------------------------------------------------ idle composites
def stone_idle(L): return [comp(stone_base(L, i / 8), stone_head(L)) for i in range(8)]
def archer_idle(L):
    out = []; angs = [0, -6, -12, -6, 0, 8, 14, 7]; pulls = [0, 0, 0, 0, 0.5, 1.5, 0.6, 0]
    for i in range(8): out.append(comp(archer_base(L), xform(archer_head(L, pulls[i]), 1, 0, 0, -angs[i])))
    return out
def frost_idle(L):
    out = []
    for i in range(8):
        ch = 0.2 + 0.2 * math.sin(i / 8 * 6.283)
        out.append(comp(frost_base(L), frost_head(L, ch, i * 6), twinkles(i)))
    return out

# ------------------------------------------------------------ shadows
def shadow(shape):
    im = canvas(); d = ImageDraw.Draw(im)
    if shape == 'round': d.ellipse(((C - 24) * S, (C - 22) * S, (C + 30) * S, (C + 30) * S), fill=(20, 40, 20, 80))
    else: d.rounded_rectangle(((C - 24) * S, (C - 22) * S, (C + 30) * S, (C + 30) * S), radius=6 * S, fill=(20, 40, 20, 80))
    return fin(im.filter(ImageFilter.GaussianBlur(S * 1.2)))

# ------------------------------------------------------------ projectiles / impacts
def proj_stone():
    im = canvas(32); d = ImageDraw.Draw(im)
    circ(d, 16, 16, 6.2, (156, 160, 178, 255), OUT, 1.3); circ(d, 14.2, 14.2, 2.4, (214, 218, 232, 255), None); circ(d, 18.5, 18.5, 2.2, (118, 122, 142, 255), None)
    return fin(im, 32)
def proj_arrow():
    im = canvas(48, 16); d = ImageDraw.Draw(im)
    line(d, (6, 8), (40, 8), OUT, 3.4); line(d, (6, 8), (40, 8), (168, 124, 80, 255), 2.0)
    poly(d, [(46, 8), (38, 4.2), (38, 11.8)], (214, 218, 230, 255), OUT, 1.0)
    for sy in (-1, 1): poly(d, [(3, 8), (9, 8 + sy * 4.2), (13, 8 + sy * 4.2), (10, 8)], RED, OUT, 0.9)
    return fin(im, 48, 16)
def proj_ice():
    im = canvas(32, 16); d = ImageDraw.Draw(im); im = comp(im, glow(15, 8, 8, (140, 220, 255), 110).crop((0, 0, 32 * S, 16 * S)) if False else Image.new('RGBA', (32 * S, 16 * S))); d = ImageDraw.Draw(im)
    poly(d, [(30, 8), (14, 3), (3, 8), (14, 13)], ICE, (36, 96, 180, 255), 1.3)
    poly(d, [(30, 8), (14, 3), (3, 8)], ICE_L, None); line(d, (6, 8), (26, 8), (255, 255, 255, 220), 0.9)
    return fin(im, 32, 16)

def fx_frames(n, size, fn):
    return [fin(fn(i / (n - 1), i), size) for i in range(n)]
def impact_stone(n=6, size=64):
    def fn(t, i):
        im = canvas(size); d = ImageDraw.Draw(im); c = size / 2; r = random.Random(4)
        for k in range(9):
            a = k / 9 * 6.283 + 0.3; q = 4 + t * 20; rr = 4 + t * 5
            d.ellipse(((c + math.cos(a) * q - rr) * S, (c + math.sin(a) * q - rr) * S, (c + math.cos(a) * q + rr) * S, (c + math.sin(a) * q + rr) * S), fill=(232, 222, 200, 235))
        im = im.filter(ImageFilter.GaussianBlur(S * 0.9)); im = fade(im, 1 - t * 0.85); d = ImageDraw.Draw(im)
        for k in range(7):
            a = r.random() * 6.283; q = 6 + t * r.uniform(14, 26); circ(d, c + math.cos(a) * q, c + math.sin(a) * q, 2.2 * (1 - t * .5), (156, 160, 178, 255), OUT, 0.8)
        return im
    return fx_frames(n, size, lambda t, i: fn(t, i))
def impact_arrow(n=5, size=48):
    def fn(t, i):
        im = canvas(size); d = ImageDraw.Draw(im); c = size / 2; r = random.Random(8)
        for k in range(6):
            a = k / 6 * 6.283 + 0.5; q = 3 + t * 15
            line(d, (c + math.cos(a) * q * 0.5, c + math.sin(a) * q * 0.5), (c + math.cos(a) * q, c + math.sin(a) * q), (255, 244, 190, int(255 * (1 - t))), 2.2 * (1 - t * .5))
        for k in range(4):
            a = r.random() * 6.283; q = 4 + t * 14; rrect(d, c + math.cos(a) * q, c + math.sin(a) * q, 4, 1.5, math.degrees(a) + t * 300, WOOD, OUT, 0.6)
        if t < 0.4: circ(d, c, c, 6 * (1 - t * 2), (255, 255, 240, 255), None)
        return im
    return fx_frames(n, size, fn)
def impact_ice(n=8, size=64):
    def fn(t, i):
        im = canvas(size); c = size / 2
        im = comp(im, Image.new('RGBA', im.size)); d = ImageDraw.Draw(im)
        if t < 0.5: circ(d, c, c, 12 * (1 - t * 1.4) + 3, (255, 255, 255, 255), None)
        arc(d, c, c, 6 + t * 24, 0, 360, (150, 224, 255, int(255 * (1 - t))), 4 * (1 - t) + 1)
        for k in range(8):
            a = math.radians(k * 45 + 10); q = 6 + t * 22
            crystal(d, c + math.cos(a) * q, c + math.sin(a) * q, math.degrees(a), 7 * (1 - t * .4), 4, 0, ICE, ICE_L)
        for k in range(4): snowflake(d, c + math.cos(k * 1.57 + 0.8) * (10 + t * 16), c + math.sin(k * 1.57 + 0.8) * (10 + t * 16), 3, (255, 255, 255, int(255 * (1 - t))), 1.0)
        return im
    return fx_frames(n, size, fn)

# ------------------------------------------------------------ BUILD & EXPORT
spec = {'frame_px': F, 'pivot': [48, 48], 'footprint_cells': [1, 1], 'cell_px': 64, 'towers': {}}
TOWERS = {
    'stone': dict(folder='Stone', base=stone_base, idle=stone_idle, att=stone_attack, spawn=stone_spawn, head=lambda L: stone_head(L),
                  d=('stone', 'chunk', 1, 5, (232, 222, 200)), shadow='round', head_rot=True),
    'archer': dict(folder='Archer', base=archer_base, idle=archer_idle, att=archer_attack, spawn=archer_spawn, head=lambda L: archer_head(L),
                   d=('wood', 'plank', 3, 6, (214, 186, 140)), shadow='square', head_rot=True),
    'frost': dict(folder='Frost', base=frost_base, idle=frost_idle, att=frost_attack, spawn=frost_spawn, head=lambda L: frost_head(L),
                  d=('ice', 'shard', 4, 7, (200, 236, 252)), shadow='round', head_rot=False),
}
cache = {}
for name, T in TOWERS.items():
    fo = f"{ROOT}/Towers/{T['folder']}"
    shadow(T['shadow']).save(f'{fo}/tower_{name}_shadow.png')
    for L in range(1, 6):
        tag = f'tower_{name}_level_{L:02d}'
        b = T['base'](L); h = T['head'](L)
        b.save(f'{fo}/{tag}_base.png'); h.save(f'{fo}/{tag}_head_static.png')
        idle = T['idle'](L); att = T['att'](L); sp = T['spawn'](L)
        intact = idle[0]
        kind, shape, sd, rs, dc = T['d']
        des = destroyed(intact, kind, shape, 10, sd, rs, dc, do_dust=(name != 'frost'))
        strip(idle).save(f'{fo}/{tag}_idle.png'); strip(att).save(f'{fo}/{tag}_head_attack.png')
        strip(sp).save(f'{fo}/{tag}_spawn.png'); strip(des).save(f'{fo}/{tag}_destroyed.png')
        cache[(name, L)] = dict(base=b, head=h, idle=idle, att=att, spawn=sp, des=des)
    spec['towers'][name] = {
        'sheets': {
            'idle': dict(frames=8, fps=8, duration_s=1.0, loop=True, composite=True, note='base+head, head at 0deg'),
            'head_attack': dict(frames=8, fps=16, duration_s=0.5, loop=False, composite=False, note='head only, faces EAST (0deg); engine rotates about pivot (48,48); base stays fixed. Spawn projectile at event frame ' + {'stone': '3', 'archer': '5', 'frost': '5'}[name]),
            'spawn': dict(frames=10, fps=14, duration_s=0.71, loop=False, composite=True),
            'destroyed': dict(frames=10, fps=12, duration_s=0.83, loop=False, composite=True, note='last frame = persistent rubble'),
            'base': dict(frames=1, note='static, layer under head'), 'head_static': dict(frames=1)},
        'levels': 5, 'layout': 'horizontal strip, frame 96x96, left-to-right = playback order',
        'rotating_head': T['head_rot']}

# projectiles & impacts
proj = {'projectile_stone': proj_stone(), 'projectile_arrow': proj_arrow(), 'projectile_ice_shard': proj_ice()}
for k, v in proj.items(): v.save(f'{ROOT}/Projectiles/{k}.png')
imp = {'vfx_stone_impact': impact_stone(), 'vfx_arrow_impact': impact_arrow(), 'vfx_ice_explosion': impact_ice()}
for k, fr in imp.items(): strip(fr).save(f'{ROOT}/VFX/{k}.png')
spec['projectiles'] = {'projectile_stone': '32x32, pivot center', 'projectile_arrow': '48x16, points EAST, pivot (24,8)', 'projectile_ice_shard': '32x16, points EAST, pivot (16,8)'}
spec['impacts'] = {'vfx_stone_impact': dict(frames=6, size=64, fps=14, loop=False), 'vfx_arrow_impact': dict(frames=5, size=48, fps=16, loop=False), 'vfx_ice_explosion': dict(frames=8, size=64, fps=16, loop=False)}
os.makedirs(f'{ROOT}/Documentation', exist_ok=True)
json.dump(spec, open(f'{ROOT}/Documentation/tower_animation_spec.json', 'w'), indent=1)

# ------------------------------------------------------------ PREVIEWS
atlas = Image.open(f'{ROOT}/Environment/Grassland/grassland_tileset_32.png')
gt = [atlas.crop((i * 32, 0, i * 32 + 32, 32)) for i in range(8)]
def grass_bg(w, h, seed=2):
    r = random.Random(seed); bg = Image.new('RGBA', (w, h))
    for y in range(0, h, 32):
        for x in range(0, w, 32): bg.paste(gt[r.randrange(8)], (x, y))
    return bg
def on_grass(fr, scale=3, ang=None):
    bg = grass_bg(F, F, 1); bg.alpha_composite(fr)
    return bg.resize((F * scale, F * scale), Image.BICUBIC).convert('RGB')
def sh_of(name): return Image.open(f"{ROOT}/Towers/{TOWERS[name]['folder']}/tower_{name}_shadow.png")
def assemble(name, L, head, ang=0):
    c = cache[(name, L)]; h = head
    if ang and TOWERS[name]['head_rot']: h = h.rotate(-ang, resample=Image.BICUBIC)
    return comp(sh_of(name), c['base'], h)
def gif(path, frames, fps_list, scale=3):
    fr = [f.convert('P', palette=Image.ADAPTIVE) for f in frames]
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=[int(1000 / f) for f in fps_list], loop=0, disposal=2)
for name in TOWERS:
    for L in range(1, 6):
        c = cache[(name, L)]; frames, fps = [], []
        if L == 1:
            for f in c['spawn']: frames.append(on_grass(comp(sh_of(name), f))); fps.append(14)
        for _ in range(2):
            for f in c['idle']: frames.append(on_grass(comp(sh_of(name), f))); fps.append(8)
        for a in (-40, 30):
            for i, hd in enumerate(c['att']): frames.append(on_grass(assemble(name, L, hd, a))); fps.append(16)
            for _ in range(3): frames.append(on_grass(assemble(name, L, c['head'], a))); fps.append(10)
        if L == 1:
            for f in c['des']: frames.append(on_grass(comp(sh_of(name), f))); fps.append(12)
        gif(f"{ROOT}/Towers/Preview/tower_{name}_level_{L:02d}_demo.gif", frames, fps)

# lineup
cs = 240
line_im = Image.new('RGB', (cs * 5 + 40, cs * 3 + 20), (60, 90, 50))
for r_, name in enumerate(TOWERS):
    for L in range(1, 6):
        bg = grass_bg(F, F, r_ * 3 + L); bg.alpha_composite(assemble(name, L, cache[(name, L)]['head'], 0))
        line_im.paste(bg.resize((cs, cs), Image.BICUBIC).convert('RGB'), ((L - 1) * (cs + 10), r_ * (cs + 10)))
line_im.save(f'{ROOT}/Towers/Preview/towers_lineup_levels_1-5.png')

# on-map preview
P = f'{ROOT}/Environment/Grassland/Preview/layers'
ld = lambda n: Image.open(f'{P}/layer_{n}.png').convert('RGBA')
mp = comp(ld('1_ground'), ld('2_water'), ld('3_path'), ld('4_path_decals'), ld('5_small_decor'), ld('6_objects'), ld('7_grid'))
cellc = lambda x, y: ((x + .5) * 64, (y + .5) * 64)
def put_tower(im, name, L, cx, cy, tgt):
    x, y = cellc(cx, cy); ang = math.degrees(math.atan2(tgt[1] - y, tgt[0] - x))
    spr = assemble(name, L, cache[(name, L)]['head'], ang)
    im.alpha_composite(spr, (int(x - 48), int(y - 48)))
    return ang
sel = Image.open(f'{ROOT}/Environment/Shared/Grid/grid_cell_occupied_64.png')
for (n, L, cx, cy, tg) in [('archer', 3, 5, 3, cellc(4, 5)), ('stone', 4, 10, 6, cellc(9, 5)), ('frost', 5, 13, 4, cellc(14, 5))]:
    mp.alpha_composite(sel, (cx * 64, cy * 64)); 
for (n, L, cx, cy, tg) in [('archer', 3, 5, 3, cellc(4, 5)), ('stone', 4, 10, 6, cellc(9, 5)), ('frost', 5, 13, 4, cellc(14, 5))]:
    put_tower(mp, n, L, cx, cy, tg)
ring = Image.open(f'{ROOT}/Environment/Shared/Grid/grid_range_ring_256.png'); rs = int(ring.width * 1.55)
rg = ring.resize((rs, rs), Image.LANCZOS); x, y = cellc(10, 6); mp.alpha_composite(rg, (int(x - rs / 2), int(y - rs / 2)))
# projectiles in flight
def fly(im, spr, p0, p1, t):
    a = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])); s = spr.rotate(-a, expand=True, resample=Image.BICUBIC)
    px, py = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t; im.alpha_composite(s, (int(px - s.width / 2), int(py - s.height / 2)))
fly(mp, proj['projectile_arrow'], cellc(5, 3), cellc(4, 5), .55)
fly(mp, proj['projectile_stone'], cellc(10, 6), cellc(9, 5), .55)
fly(mp, proj['projectile_ice_shard'], cellc(13, 4), cellc(14, 5), .5)
mp.alpha_composite(imp['vfx_ice_explosion'][3], (int(cellc(14, 5)[0] - 32 + 40), int(cellc(14, 5)[1] - 32 + 30)))
# placement ghost + invalid
for (cx, cy, st) in [(15, 6, 'selected'), (9, 4, 'invalid')]:
    mp.alpha_composite(Image.open(f'{ROOT}/Environment/Shared/Grid/grid_cell_{st}_64.png'), (cx * 64, cy * 64))
    g = fade(comp(cache[('frost', 1)]['base'], cache[('frost', 1)]['head']), 0.55)
    if st == 'invalid': g = fade(comp(cache[('archer', 1)]['base'], cache[('archer', 1)]['head']), 0.5)
    x, y = cellc(cx, cy); mp.alpha_composite(g, (int(x - 48), int(y - 48)))
mp.convert('RGB').save(f'{ROOT}/Environment/Grassland/Preview/prototype_with_starter_towers.png')

# attack sheets contact (head frames) for review
rows = []
for name in TOWERS:
    rows.append(strip(cache[(name, 5)]['att']))
big = Image.new('RGBA', (rows[0].width, F * 3), (112, 192, 72, 255))
for i, r_ in enumerate(rows): big.alpha_composite(r_, (0, i * F))
big.resize((big.width * 2 // 2 , big.height), Image.LANCZOS).convert('RGB').save(f'{ROOT}/Towers/Preview/attack_head_frames_level5.png')

# ======================================================================
# DELIVERABLES: combined sprite sheets + all-level demos
# ======================================================================
import shutil
from PIL import ImageFont
COLS = 10; ROWS = ['build', 'idle', 'attack', 'destroyed']
ROWFPS = {'build': 14, 'idle': 8, 'attack': 16, 'destroyed': 12}
def level_rows(name, L):
    c = cache[(name, L)]
    return {'build': c['spawn'], 'idle': c['idle'], 'attack': [comp(c['base'], h) for h in c['att']], 'destroyed': c['des']}
def level_sheet(name, L):
    rows = level_rows(name, L); sh = Image.new('RGBA', (F * COLS, F * 4), (0, 0, 0, 0))
    for r, k in enumerate(ROWS):
        for i, f in enumerate(rows[k]): sh.paste(f, (i * F, r * F))
    return sh
try: FONT = ImageFont.load_default(size=15); FONT_S = ImageFont.load_default(size=12)
except Exception: FONT = FONT_S = ImageFont.load_default()
atlas_all = {}
for name, T in TOWERS.items():
    fo = f"{ROOT}/Towers/{T['folder']}"; os.makedirs(f'{fo}/SpriteSheets', exist_ok=True)
    LM, TH, GAP = 118, 26, 8; blk = TH + F * 4 + GAP
    master = Image.new('RGBA', (F * COLS, F * 4 * 5), (0, 0, 0, 0))
    lab = Image.new('RGB', (LM + F * COLS, blk * 5), (52, 60, 72)); dl = ImageDraw.Draw(lab)
    meta = {'frame_px': F, 'columns': COLS, 'rows_order': ROWS, 'pivot': [48, 48], 'levels': {}}
    for L in range(1, 6):
        sh = level_sheet(name, L); sh.save(f'{fo}/SpriteSheets/tower_{name}_level_{L:02d}_spritesheet.png')
        master.paste(sh, (0, (L - 1) * F * 4))
        y0 = (L - 1) * blk
        dl.text((LM, y0 + 4), f'{name.upper()} TOWER  -  LEVEL {L}', fill=(255, 255, 255), font=FONT)
        for r, k in enumerate(ROWS):
            dl.text((8, y0 + TH + r * F + F // 2 - 8), k.upper(), fill=(255, 224, 140), font=FONT)
            dl.line((LM, y0 + TH + r * F, LM + F * COLS, y0 + TH + r * F), fill=(80, 90, 104))
        lab.paste(sh, (LM, y0 + TH), sh)
        meta['levels'][str(L)] = {'y_offset_in_master': (L - 1) * F * 4,
            'rows': {k: dict(row=r, y=r * F, frames=len(level_rows(name, L)[k]), fps=ROWFPS[k], loop=(k == 'idle')) for r, k in enumerate(ROWS)}}
    master.save(f'{fo}/SpriteSheets/tower_{name}_ALL_LEVELS_spritesheet.png')
    lab.save(f'{fo}/SpriteSheets/tower_{name}_ALL_LEVELS_spritesheet_LABELED.png')
    meta['notes'] = ('attack row = base + head, head facing EAST. For in-game aiming use the head-only sheets tower_%s_level_NN_head_attack.png and rotate about (48,48). '
                     'Last destroyed frame = persistent rubble. Shadows are separate: tower_%s_shadow.png.' % (name, name))
    json.dump(meta, open(f'{ROOT}/Documentation/tower_{name}_spritesheet_atlas.json', 'w'), indent=1)

# ---------------- demos
CW, CH, BAN = 176, 96, 30
EVENT = {'stone': 3, 'archer': 5, 'frost': 5}
PROJ = {'stone': proj['projectile_stone'], 'archer': proj['projectile_arrow'], 'frost': proj['projectile_ice_shard']}
IMP = {'stone': imp['vfx_stone_impact'], 'archer': imp['vfx_arrow_impact'], 'frost': imp['vfx_ice_explosion']}
BG = {}
for name in TOWERS:
    for L in range(1, 6):
        bg = grass_bg(CW, CH, 20 + L * 3 + len(name)); d = ImageDraw.Draw(bg)
        for rr, col in [(13, (60, 40, 30, 255)), (12, (250, 246, 236, 255)), (9, (220, 60, 66, 255)), (6, (250, 246, 236, 255)), (3, (220, 60, 66, 255))]:
            d.ellipse((150 - rr, 48 - rr, 150 + rr, 48 + rr), fill=col)
        d.text((5, 3), f'LV {L}', fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(30, 30, 30, 255))
        BG[(name, L)] = bg
TIMELINE = ([('BUILD', i, 71) for i in range(10)] + [('IDLE', i, 125) for i in range(16)] +
            [('ATTACK', i, 62) for i in range(22)] * 2 + [('DESTROYED', i, 83) for i in range(10)] + [('DESTROYED', 9, 120)] * 7)
def cell(name, L, kind, idx):
    c = cache[(name, L)]; fr = BG[(name, L)].copy(); sh = sh_of(name)
    if kind == 'BUILD': spr = comp(sh, c['spawn'][idx])
    elif kind == 'IDLE': spr = comp(sh, c['idle'][idx % 8])
    elif kind == 'DESTROYED': spr = comp(sh, c['des'][min(idx, 9)])
    else:
        spr = comp(sh, c['base'], c['att'][idx] if idx < 8 else c['head'])
    fr.alpha_composite(spr, (0, 0))
    if kind == 'ATTACK':
        ev = EVENT[name]; ps = PROJ[name]
        if ev <= idx < ev + 6:
            px = 72 + (140 - 72) * (idx - ev) / 5
            fr.alpha_composite(ps, (int(px - ps.width / 2), int(48 - ps.height / 2)))
        j = idx - ev - 6
        if 0 <= j < len(IMP[name]):
            im_ = IMP[name][j]; fr.alpha_composite(im_, (int(146 - im_.width / 2), int(48 - im_.height / 2)))
    return fr
def demo(names, path, scale=1.5):
    frames, durs = [], []
    for kind, idx, dur in TIMELINE:
        W = CW * 5; H = BAN + CH * len(names)
        im = Image.new('RGB', (W, H), (30, 34, 42)); d = ImageDraw.Draw(im)
        title = ' + '.join(n.upper() for n in names) + ' TOWER' + ('S' if len(names) > 1 else '') + '  -  LEVELS 1 TO 5   |   ' + kind
        d.text((8, 6), title, fill=(255, 226, 140), font=FONT)
        for r, n in enumerate(names):
            for L in range(1, 6): im.paste(cell(n, L, kind, idx).convert('RGB'), ((L - 1) * CW, BAN + r * CH))
        im = im.resize((int(W * scale), int(H * scale)), Image.BICUBIC)
        frames.append(im.convert('P', palette=Image.ADAPTIVE)); durs.append(dur)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1, optimize=False)
for name, T in TOWERS.items():
    demo([name], f"{ROOT}/Towers/Preview/DEMO_{name}_tower_levels_1-5.gif")
demo(list(TOWERS), f"{ROOT}/Towers/Preview/DEMO_ALL_TOWERS_levels_1-5.gif", 1.0)
shutil.make_archive('/mnt/user-data/outputs/GameAssets_Towers_Phase3', 'zip', ROOT)
print('done')
