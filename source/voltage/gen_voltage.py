#!/usr/bin/env python3
"""Cutthroat Carnivore "Voltage" noteskin - texture generator.
Original art by Cutthroat Carnivore, generated procedurally with signed distance
fields at 4x pixel density so everything stays crisp at 1080p and above.
usage: gen_voltage.py <variant: color|pink|red> <out_dir>"""
import colorsys, math, os, random, sys
import numpy as np
from PIL import Image

SS = 4  # pixels per logical unit (64-unit arrow = 256 px)


def grid(w, h):
    W, H = int(round(w * SS)), int(round(h * SS))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    return (xs + 0.5) / SS, (ys + 0.5) / SS


def blank(w, h):
    return np.zeros((int(round(h * SS)), int(round(w * SS)), 4), np.float32)


def cov(d):  # anti-aliased coverage of the region d < 0 (d in logical units)
    return np.clip(0.5 - d * SS, 0.0, 1.0)


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sd_poly(px, py, pts):
    pts = np.asarray(pts, np.float32)
    d = np.full(px.shape, 1e9, np.float32)
    s = np.ones(px.shape, np.float32)
    for i in range(len(pts)):
        ax, ay = pts[i]
        bx, by = pts[i - 1]
        ex, ey = bx - ax, by - ay
        wx, wy = px - ax, py - ay
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        dx, dy = wx - ex * t, wy - ey * t
        d = np.minimum(d, dx * dx + dy * dy)
        c1, c2, c3 = py >= ay, py < by, ex * wy > ey * wx
        s = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -s, s)
    return s * np.sqrt(d)


def sd_segs(px, py, segs):
    """distance to a list of line segments ((x0,y0),(x1,y1))"""
    d = np.full(px.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in segs:
        ex, ey = bx - ax, by - ay
        L = ex * ex + ey * ey + 1e-9
        wx, wy = px - ax, py - ay
        t = np.clip((wx * ex + wy * ey) / L, 0, 1)
        dx, dy = wx - ex * t, wy - ey * t
        d = np.minimum(d, dx * dx + dy * dy)
    return np.sqrt(d)


def over(img, rgb, a):
    """paint straight colour rgb (tuple or HxWx3) with alpha a over premultiplied img"""
    a = np.clip(a, 0, 1)[..., None]
    rgb = np.asarray(rgb, np.float32)
    if rgb.ndim == 1:
        rgb = rgb[None, None, :]
    img[..., :3] = img[..., :3] * (1 - a) + rgb * a
    img[..., 3:] = img[..., 3:] * (1 - a) + a


def save(img, path):
    a = img[..., 3:]
    rgb = np.where(a > 1e-5, img[..., :3] / np.maximum(a, 1e-5), 0)
    out = np.clip(np.concatenate([rgb, a], -1), 0, 1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)


def sheet(frames, cols, rows):
    h, w = frames[0].shape[:2]
    out = np.zeros((h * rows, w * cols, 4), np.float32)
    for i, f in enumerate(frames):
        r, c = divmod(i, cols)
        out[r * h:(r + 1) * h, c * w:(c + 1) * w] = f
    return out


def hsv(h, s, v):
    return colorsys.hsv_to_rgb(h % 1.0, s, v)


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ---------------------------------------------------------------- shapes
# Down-pointing arrow in a 64x64 cell: wide head, solid stem, rounded corners.
ARROW = [(23.5, 5), (40.5, 5), (40.5, 26), (54, 26), (59, 31.5), (32, 58.5),
         (5, 31.5), (10, 26), (23.5, 26)]
# Lightning glyph (points down), centred on its own origin.
BOLT = [(2, -16), (10, -16), (4, -4), (10, -4), (-6, 16), (-1, 1), (-7, 1)]


def arrow_sd(px, py):
    c = 32.0
    pts = [(c + (x - c) * 0.95, c + (y - c) * 0.95) for x, y in ARROW]
    return sd_poly(px, py, pts) - 1.3


def bolt_sd(px, py, cx, cy, scale, rng=None, jit=0.0):
    pts = []
    for x, y in BOLT:
        jx = (rng.random() * 2 - 1) * jit if rng else 0
        jy = (rng.random() * 2 - 1) * jit if rng else 0
        pts.append((cx + (x - 1.5 + jx) * scale, cy + (y + jy) * scale))
    return sd_poly(px, py, pts)


def zigzag(rng, a, b, disp, depth):
    pts = [a, b]
    for _ in range(depth):
        new = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            mx, my = (ax + bx) / 2, (ay + by) / 2
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) + 1e-9
            o = (rng.random() * 2 - 1) * disp
            new += [(mx - dy / L * o, my + dx / L * o), (bx, by)]
        pts = new
        disp *= 0.55
    return pts


def lightning(rng, a, b, disp, branches=2, depth=5):
    """main bolt from a to b plus forked branches; returns [(segments, width)]"""
    main = zigzag(rng, a, b, disp, depth)
    out = [(list(zip(main, main[1:])), 1.0)]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for _ in range(branches):
        i = rng.randrange(len(main) // 4, max(len(main) // 4 + 1, 3 * len(main) // 4))
        p = main[i]
        ba = ang + (rng.choice([-1, 1])) * math.radians(rng.uniform(22, 55))
        bl = L * rng.uniform(0.25, 0.45)
        q = (p[0] + math.cos(ba) * bl, p[1] + math.sin(ba) * bl)
        br = zigzag(rng, p, q, disp * 0.5, depth - 1)
        out.append((list(zip(br, br[1:])), 0.55))
    return out


def paint_lightning(img, px, py, bolts, glow, core=(1, 1, 1), w=0.9, gw=2.6, ga=0.9):
    for segs, k in bolts:
        d = sd_segs(px, py, segs)
        over(img, glow, ga * k * np.exp(-d / (gw * (0.6 + 0.4 * k))))
        over(img, mix(glow, core, 0.75), cov(d - w * k * 1.6) * 0.9)
        over(img, core, cov(d - w * k * 0.7))


# ---------------------------------------------------------------- rhythm colours
# 4th, 8th, 12th, 16th, 24th, 32nd, 48th, 64th, 192nd. Each value gets its own
# colour AND its own face symbol, so colour-blind players can still read rhythm.
QUANT = [(1.0, 0.1, 0.1),      # 4th  red      (vivid, and spread in brightness
         (0.08, 0.35, 1.0),    # 8th  blue      so they still separate for
         (0.62, 0.18, 1.0),    # 12th violet    colour-blind eyes)
         (1.0, 0.92, 0.0),     # 16th yellow
         (1.0, 0.3, 0.72),     # 24th pink
         (1.0, 0.52, 0.0),     # 32nd orange
         (0.0, 0.88, 0.92),    # 48th cyan
         (0.12, 0.86, 0.22),   # 64th green
         (0.92, 0.92, 0.95)]
GLYPH = ["bolt", "diamond", "triangle", "circle", "tri_hollow", "ring", "dia_hollow", "ring_small", "dot"]


# Fill pattern per rhythm value - readable with no colour vision at all:
# 4th solid, 8th diagonal stripes, 12th dots, 16th hollow, 24th horizontal
# stripes, 32nd thin hollow, 48th checker, 64th hollow, 192nd thin hollow.
PATTERN = ["solid", "stripes", "dots", "hollow", "hstripes", "hollow_thin", "checker", "hollow", "hollow_thin"]


def pattern_mask(kind, px, py, d):
    if kind == "stripes":
        s = (px - py) % 11.0
        return cov(np.abs(s - 5.5) - 2.9)
    if kind == "hstripes":
        s = py % 9.0
        return cov(np.abs(s - 4.5) - 2.3)
    if kind == "dots":
        dx, dy = (px % 9.0) - 4.5, (py % 9.0) - 4.5
        return cov(np.hypot(dx, dy) - 2.7)
    if kind == "checker":
        return ((np.floor(px / 8) + np.floor(py / 8)) % 2).astype(np.float32)
    if kind == "hollow":
        return 1 - cov(d + 8.0)
    if kind == "hollow_thin":
        return 1 - cov(d + 5.2)
    return np.ones_like(px)


def glyph_sd(kind, px, py, cx=32, cy=35):
    x, y = px - cx, py - cy
    if kind == "bolt":
        return bolt_sd(px, py, cx, cy, 0.78)
    if kind in ("diamond", "dia_hollow"):
        d = (np.abs(x) + np.abs(y) / 1.3 - 9.0) * 0.7
        return np.abs(d + 1.6) - 1.6 if kind == "dia_hollow" else d
    if kind in ("triangle", "tri_hollow"):
        d = sd_poly(px, py, [(cx - 9, cy - 7), (cx + 9, cy - 7), (cx, cy + 9)])
        return np.abs(d + 1.6) - 1.6 if kind == "tri_hollow" else d
    r = np.hypot(x, y)
    if kind == "circle":
        return r - 7.5
    if kind == "ring":
        return np.abs(r - 6.5) - 1.8
    if kind == "ring_small":
        return np.abs(r - 4.5) - 1.5
    return r - 3.5


# ---------------------------------------------------------------- palettes
def palette(variant):
    if variant == "color":
        rows = [dict(top=mix(q, (1, 1, 1), 0.18), bot=mix(q, (0, 0, 0), 0.1), rim=(1, 1, 1),
                     hair=mix(q, (0, 0, 0), 0.55), glow=q, core=(1, 1, 1), tint=0.0) for q in QUANT]
        return dict(rows=rows, outline=(0.03, 0.02, 0.03), bolt_core=(1, 1, 1),
                    bolt_glow=(1.0, 0.12, 0.16), fx=(1.0, 0.22, 0.18), fx2=(1.0, 0.86, 0.6),
                    beam=(0.32, 0.82, 1.0), roll=(1.0, 0.32, 0.16),
                    rec_rim=(0.85, 0.85, 0.9), rec_fill=(0.05, 0.05, 0.07), name="Color")
    if variant == "pink":
        row = dict(top=(0.17, 0.015, 0.1), bot=(0.02, 0.0, 0.012), rim=(1.0, 0.2, 0.66),
                   hair=(1.0, 0.86, 0.95), glow=(1.0, 0.18, 0.64))
        return dict(rows=[dict(row, hair=q, core=q, tint=0.22) for q in QUANT], outline=(0.0, 0.0, 0.0), bolt_core=(1, 0.92, 0.98),
                    bolt_glow=(1.0, 0.16, 0.62), fx=(1.0, 0.2, 0.66), fx2=(1.0, 0.82, 0.95),
                    beam=(1.0, 0.28, 0.72), roll=(1.0, 0.7, 0.9),
                    rec_rim=(0.85, 0.22, 0.58), rec_fill=(0.05, 0.0, 0.03), name="Pink & Black", gloss=0.1, pattern_dark=0.6)
    row = dict(top=(0.17, 0.01, 0.01), bot=(0.02, 0.0, 0.0), rim=(1.0, 0.1, 0.08),
               hair=(1.0, 0.86, 0.8), glow=(1.0, 0.1, 0.07))
    return dict(rows=[dict(row, hair=q, core=q, tint=0.22) for q in QUANT], outline=(0.0, 0.0, 0.0), bolt_core=(1, 0.94, 0.88),
                bolt_glow=(1.0, 0.08, 0.05), fx=(1.0, 0.12, 0.08), fx2=(1.0, 0.85, 0.62),
                beam=(1.0, 0.14, 0.1), roll=(1.0, 0.78, 0.68),
                rec_rim=(0.85, 0.12, 0.1), rec_fill=(0.05, 0.0, 0.0), name="Black & Red", gloss=0.1, pattern_dark=0.6)


# ---------------------------------------------------------------- notes
STRIKE = [1.0, 0.5, 0.22, 0.06]  # face-bolt brightness for the 4 frames of a beat


def tap_frame(P, row, f, hollow=False, glow=True):
    px, py = grid(64, 64)
    d = arrow_sd(px, py)
    R = P["rows"][row]
    I = STRIKE[f]
    img = blank(64, 64)
    if glow:  # soft outer halo so the arrow pops on dark backgrounds
        over(img, R["glow"], 0.45 * np.exp(-np.maximum(d - 2.4, 0) / 2.0))
    over(img, P["outline"], cov(d - 2.6))
    over(img, R["rim"], cov(d))
    over(img, R["hair"], cov(d + 1.9))
    t = sstep(6, 58, py)[..., None]
    inner = cov(d + 2.6)
    if P["name"] == "Color":
        ptop, pbot, base = R["top"], R["bot"], (0.07, 0.07, 0.09)
    else:
        ptop, pbot, base = R["core"], mix(R["core"], (0, 0, 0), 0.3), R["bot"]
    fill = np.asarray(ptop, np.float32) * (1 - t) + np.asarray(pbot, np.float32) * t
    pm = pattern_mask(PATTERN[min(row, 8)], px, py, d)
    over(img, fill, inner * (0.4 if hollow else 1.0))                  # whole body in rhythm colour
    over(img, base, inner * (1 - pm) * P.get("pattern_dark", 0.4))     # pattern = darker tone
    over(img, (0, 0, 0), 0.32 * inner * sstep(-6.0, -2.6, d))          # bevel shadow
    over(img, (1, 1, 1), cov(d + 3.4) * (1 - sstep(9, 30, py)) * P.get("gloss", 0.18) * pm)   # gloss
    gcol = R["glow"] if P["name"] == "Color" else R["core"]
    db = glyph_sd(GLYPH[min(row, 8)], px, py)
    over(img, gcol, inner * (0.25 + 0.75 * I) * np.exp(-np.maximum(db, 0) / 2.4) * 0.9)
    over(img, P["outline"], inner * cov(db - 0.9) * 0.6)                # keyline
    core = (1, 1, 1) if P["name"] == "Color" else mix(R["core"], (1, 1, 1), 0.55)
    over(img, mix(core, (1, 1, 1), 0.25 + 0.55 * I), inner * cov(db))
    if I > 0.4:
        over(img, (1, 1, 1), inner * 0.16 * I)
    return img


def note_sheet(P, hollow=False):
    frames = []
    for r in range(16):
        for f in range(4):
            frames.append(tap_frame(P, min(r, 8), f, hollow, glow=False))
    return sheet(frames, 4, 16)


def rim_frame():
    px, py = grid(64, 64)
    d = arrow_sd(px, py)
    img = blank(64, 64)
    over(img, (1, 1, 1), 0.55 * np.exp(-np.maximum(d - 2.6, 0) / 2.2) * sstep(2.2, 3.0, d))  # halo
    over(img, (1, 1, 1), cov(d) * (1 - cov(d + 2.3)))                                      # thick rim
    return img


def rim_sheet():
    f = rim_frame()
    return sheet([f] * 64, 4, 16)


def receptor_sheet(P):
    px, py = grid(64, 64)
    d = arrow_sd(px, py)
    g = P["rows"][0]["glow"] if P["name"] != "Color" else (1.0, 0.25, 0.2)
    f0 = blank(64, 64)  # resting frame
    over(f0, P["outline"], cov(d - 2.4))
    over(f0, (0.92, 0.92, 0.94), cov(d))
    over(f0, P["outline"], cov(d + 1.9))
    over(f0, P["rec_fill"], cov(d + 2.4) * 0.55)
    over(f0, P["rec_rim"], cov(np.abs(d + 3.6) - 0.35) * 0.45)
    f1 = blank(64, 64)  # beat flash (added on top)
    ad = np.abs(d + 0.8)
    over(f1, g, 0.95 * np.exp(-ad / 1.8))
    over(f1, mix(g, (1, 1, 1), 0.7), cov(ad - 0.7))
    f2 = blank(64, 64)  # press flash
    over(f2, g, cov(d + 1.6) * 0.45 * (1 - sstep(4, 56, py) * 0.5))
    over(f2, (1, 1, 1), cov(np.abs(d + 0.8) - 0.9) * 0.9)
    return sheet([f0, f1, f2], 3, 1)


def bolt_sheet(P, seed):
    """the beat indicator: four slightly different strikes so it never looks canned"""
    frames = []
    for i in range(4):
        rng = random.Random(seed + i)
        px, py = grid(64, 64)
        img = blank(64, 64)
        db = bolt_sd(px, py, 32, 32, 0.95, rng, 1.1)
        over(img, P["bolt_glow"], 0.95 * np.exp(-np.maximum(db, 0) / 3.2))
        arcs = []
        for _ in range(2):
            a = (32 + rng.uniform(-6, 6), 32 + rng.uniform(-12, 12))
            ang = rng.uniform(0, 2 * math.pi)
            b = (a[0] + math.cos(ang) * rng.uniform(12, 20), a[1] + math.sin(ang) * rng.uniform(12, 20))
            arcs += lightning(rng, a, b, 3.0, branches=1, depth=4)
        paint_lightning(img, px, py, arcs, P["bolt_glow"], P["bolt_core"], w=0.45, gw=1.8, ga=0.7)
        over(img, mix(P["bolt_glow"], P["bolt_core"], 0.6), cov(db))
        over(img, (1, 1, 1), cov(db + 1.1))
        frames.append(img)
    return sheet(frames, 4, 1)


def aura_sheet(P, seed):
    frames = []
    g = P["rows"][0]["glow"] if P["name"] != "Color" else P["fx"]
    for i in range(8):
        rng = random.Random(seed * 7 + i)
        px, py = grid(112, 112)
        img = blank(112, 112)
        bolts = []
        for _ in range(4):
            a0 = rng.uniform(0, 2 * math.pi)
            span = math.radians(rng.uniform(40, 80))
            r = rng.uniform(31, 38)
            pts = [(56 + math.cos(a0 + span * k / 5) * r, 56 + math.sin(a0 + span * k / 5) * r) for k in range(6)]
            for p, q in zip(pts, pts[1:]):
                z = zigzag(rng, p, q, 2.6, 3)
                bolts.append((list(zip(z, z[1:])), 0.8))
        paint_lightning(img, px, py, bolts, g, (1, 1, 1), w=0.5, gw=2.4, ga=0.8)
        frames.append(img)
    return sheet(frames, 8, 1)


# ---------------------------------------------------------------- effects
def polar(w, h):
    px, py = grid(w, h)
    x, y = px - w / 2, py - h / 2
    return x, y, np.hypot(x, y)


def fx_flash(P):
    x, y, r = polar(128, 128)
    img = blank(128, 128)
    a = np.clip(np.exp(-(r / 20) ** 2) + 0.35 * np.exp(-r / 26), 0, 1)
    col = np.asarray(P["fx2"], np.float32) * sstep(0, 36, r)[..., None] + (1 - sstep(0, 36, r))[..., None]
    over(img, col, a)
    return img


def star_field(x, y, r, L, w, core):
    def rays(u, v, L, k):
        return np.exp(-np.abs(v) / (w + np.abs(u) * 0.012)) * np.clip(1 - np.abs(u) / L, 0, 1) ** 1.7 * k
    s = rays(x, y, L, 1.0) + rays(y, x, L, 1.0)
    dx, dy = (x + y) * 0.7071, (x - y) * 0.7071
    s += rays(dx, dy, L * 0.5, 0.5) + rays(dy, dx, L * 0.5, 0.5)
    s += np.exp(-(r / core) ** 2) * 1.2 + 0.25 * np.exp(-r / (core * 2.4))
    return np.clip(s, 0, 1)


def fx_star(P, size, L, w, core):
    x, y, r = polar(size, size)
    img = blank(size, size)
    I = star_field(x, y, r, L, w, core)
    col = np.asarray(P["fx"], np.float32) * (1 - np.clip(I * 1.5, 0, 1))[..., None] + np.clip(I * 1.5, 0, 1)[..., None]
    over(img, col, I)
    return img


def fx_ring(P):
    x, y, r = polar(128, 128)
    img = blank(128, 128)
    rd = np.abs(r - 50)
    over(img, P["fx"], 0.6 * np.exp(-rd / 3.5))
    over(img, mix(P["fx"], (1, 1, 1), 0.8), cov(rd - 1.0))
    return img


def fx_lightning(P, seed):
    frames = []
    for i in range(8):
        rng = random.Random(seed * 31 + i)
        px, py = grid(128, 128)
        img = blank(128, 128)
        bolts = []
        a0 = rng.uniform(0, 2 * math.pi)
        n = rng.randint(3, 5)
        for k in range(n):
            ang = a0 + 2 * math.pi * k / n + rng.uniform(-0.35, 0.35)
            r1 = rng.uniform(44, 60)
            a = (64 + math.cos(ang) * 6, 64 + math.sin(ang) * 6)
            b = (64 + math.cos(ang) * r1, 64 + math.sin(ang) * r1)
            bolts += lightning(rng, a, b, 9.0, branches=2, depth=5)
        paint_lightning(img, px, py, bolts, P["fx"], (1, 1, 1), w=0.8, gw=3.0, ga=0.85)
        frames.append(img)
    return sheet(frames, 8, 1)


def fx_ember(P):
    x, y, r = polar(16, 16)
    img = blank(16, 16)
    over(img, P["fx"], np.clip(0.55 * np.exp(-r / 2.6), 0, 1))
    over(img, mix(P["fx2"], (1, 1, 1), 0.5), np.exp(-(r / 2.2) ** 2))
    return img


def fx_holdorb(P, seed):
    frames = []
    for i in range(8):
        rng = random.Random(seed * 13 + i)
        px, py = grid(64, 64)
        x, y = px - 32, py - 32
        r = np.hypot(x, y)
        img = blank(64, 64)
        over(img, P["beam"], np.clip(0.75 * np.exp(-r / 8.5), 0, 1))
        bolts = []
        for _ in range(3):
            a0 = rng.uniform(0, 2 * math.pi)
            a = (32 + math.cos(a0) * 6, 32 + math.sin(a0) * 6)
            b = (32 + math.cos(a0 + 0.6) * rng.uniform(17, 24), 32 + math.sin(a0 + 0.6) * rng.uniform(17, 24))
            bolts += lightning(rng, a, b, 4.0, branches=1, depth=4)
        paint_lightning(img, px, py, bolts, P["beam"], (1, 1, 1), w=0.55, gw=2.0, ga=0.8)
        over(img, (1, 1, 1), np.exp(-(r / 6.5) ** 2))
        frames.append(img)
    return sheet(frames, 8, 1)


def fx_mineblast(P, seed):
    rng = random.Random(seed)
    x, y, r = polar(128, 128)
    th = np.arctan2(y, x)
    spikes = np.zeros_like(r)
    for _ in range(14):
        c = rng.uniform(-math.pi, math.pi)
        dth = np.angle(np.exp(1j * (th - c)))
        spikes = np.maximum(spikes, np.exp(-(dth / 0.09) ** 2) * rng.uniform(0.6, 1.0))
    I = np.clip(np.exp(-r / (10 + 34 * spikes)) * 1.3, 0, 1)
    img = blank(128, 128)
    over(img, P["fx"], I)
    over(img, mix(P["fx2"], (1, 1, 1), 0.6), np.exp(-(r / 10) ** 2))
    return img


def fx_arrowglow():
    px, py = grid(64, 64)
    d = arrow_sd(px, py)
    img = blank(64, 64)
    over(img, (1, 1, 1), np.clip(0.95 * np.exp(-np.maximum(d, 0) / 2.6), 0, 1) * (1 - 0.55 * cov(d + 4.0)))
    return img


def make_shards(P, out, variant):
    """break the arrow into fragments (with glowing crack edges) for the shatter"""
    Pc = P
    if variant == "color":  # neutral crystal shards match every note colour
        crystal = dict(top=(0.97, 0.97, 1.0), bot=(0.6, 0.64, 0.76), rim=(1, 1, 1),
                       hair=(0.32, 0.35, 0.48), glow=(1, 1, 1))
        Pc = dict(P, rows=[crystal] * 9)
    img = tap_frame(Pc, 0, 3, glow=False)
    H, W = img.shape[:2]
    px, py = grid(64, 64)
    rng = random.Random(11)
    pts = [(32 + (x - 32) * 0.95, 32 + (y - 32) * 0.95) for x, y in ARROW]
    seeds = []
    tries = 0
    while len(seeds) < 14 and tries < 20000:
        tries += 1
        sx, sy = rng.uniform(6, 58), rng.uniform(5, 58)
        inside = sd_poly(np.array([[sx]], np.float32), np.array([[sy]], np.float32), pts)[0, 0] - 1.3 < -2
        if inside and all(math.hypot(sx - a, sy - b) > 7.0 for a, b in seeds):
            seeds.append((sx, sy))
    D = np.sqrt(np.stack([(px - sx) ** 2 + (py - sy) ** 2 for sx, sy in seeds]))
    Ds = np.sort(D, 0)
    crack = np.clip(1 - (Ds[1] - Ds[0]) / 0.9, 0, 1)
    res = []
    for i, (sx, sy) in enumerate(seeds):
        others = np.min(np.delete(D, i, 0), 0)
        soft = np.clip(0.5 + (others - D[i]) * SS * 0.5, 0, 1) * (img[..., 3] > 0.003)
        ys, xs = np.nonzero(soft > 0.01)
        if len(xs) == 0:
            continue
        x0, y0 = max(0, (xs.min() // SS - 1) * SS), max(0, (ys.min() // SS - 1) * SS)
        x1, y1 = min(W, (xs.max() // SS + 2) * SS), min(H, (ys.max() // SS + 2) * SS)
        crop = img[y0:y1, x0:x1] * soft[y0:y1, x0:x1, None]
        over(crop, mix(Pc["rows"][0]["rim"], (1, 1, 1), 0.5),
             crack[y0:y1, x0:x1] * (crop[..., 3] > 0.05) * 0.85)
        w, h = (x1 - x0) // SS, (y1 - y0) // SS
        name = "Shard %02d" % (len(res) + 1)
        save(crop, os.path.join(out, "_CC %s (res %dx%d).png" % (name, w, h)))
        res.append((name, (x0 + x1) / 2 / SS - 32, (y0 + y1) / 2 / SS - 32))
    return res


def make_mines(P, out, seed):
    x, y, r = polar(64, 64)
    px, py = x + 32, y + 32
    base = blank(64, 64)
    over(base, P["outline"], cov(r - 19))
    t = sstep(0, 20, np.hypot(x + 5, y + 5))[..., None]
    sph = np.asarray((0.2, 0.19, 0.22), np.float32) * (1 - t) + np.asarray((0.02, 0.02, 0.03), np.float32) * t
    over(base, sph, cov(r - 17))
    rng = random.Random(seed)
    cracks = []
    for k in range(4):
        ang = k * math.pi / 2 + rng.uniform(-0.4, 0.4)
        cracks += lightning(rng, (32, 32), (32 + math.cos(ang) * 13, 32 + math.sin(ang) * 13), 2.5, 1, 3)
    paint_lightning(base, px, py, cracks, P["fx"], P["fx2"], w=0.4, gw=1.4, ga=0.8)
    over(base, P["fx"], cov(np.abs(r - 17) - 0.9))
    over(base, (1, 1, 1), np.exp(-((x + 6) ** 2 + (y + 6) ** 2) / 10) * 0.45)
    save(base, os.path.join(out, "_CC Mine Base (res 64x64).png"))
    glow = blank(64, 64)
    over(glow, P["fx"], np.clip(0.9 * np.exp(-(r / 15) ** 2) + 0.3 * np.exp(-r / 9), 0, 1) * cov(r - 31))
    save(glow, os.path.join(out, "_CC Mine Glow (res 64x64).png"))
    sp = blank(64, 64)
    dsp = np.full(r.shape, 1e9, np.float32)
    for k in range(8):
        a = k * math.pi / 4
        tri = [(32 + math.cos(a - 0.24) * 15, 32 + math.sin(a - 0.24) * 15),
               (32 + math.cos(a) * 29.5, 32 + math.sin(a) * 29.5),
               (32 + math.cos(a + 0.24) * 15, 32 + math.sin(a + 0.24) * 15)]
        dsp = np.minimum(dsp, sd_poly(px, py, tri))
    over(sp, P["outline"], cov(dsp - 1.5))
    over(sp, (0.08, 0.08, 0.1), cov(dsp))
    over(sp, P["fx"], cov(np.abs(dsp + 0.6) - 0.55) * 0.95)
    save(sp, os.path.join(out, "_CC Mine Spokes (res 64x64).png"))


# ---------------------------------------------------------------- holds
EDGE = 19.0


def tri_wave(t):
    return 2 * np.abs(2 * (t % 1.0) - 1) - 1


def beam(P, px, py, f, roll, shape_d, rings=True):
    B = P["roll"] if roll else P["beam"]
    ax = np.abs(px - 32)
    cx = 32 + 6 * tri_wave((py + f * 4) / 16) if roll else 32
    dc = np.abs(px - cx)
    body = cov(shape_d)
    img = blank(px.shape[1] / SS, px.shape[0] / SS)
    over(img, P["outline"], cov(shape_d - 1.6))
    over(img, mix(B, (0, 0, 0), 0.72), body * 0.85)
    over(img, B, body * np.exp(-dc / (4.0 if roll else 6.0)) * 0.95)
    over(img, mix(B, (1, 1, 1), 0.85), body * cov(dc - (1.3 if roll else 2.4)))
    over(img, B, cov(np.abs(shape_d + 0.9) - 0.75))
    if rings and not roll:
        for k in (0, 1):
            yc = f * 8 + k * 32
            dy = ((py - yc - 3.5 * (ax / EDGE) ** 2 + 16) % 32) - 16
            over(img, B, body * np.exp(-np.abs(dy) / 2.6) * 0.5)
            over(img, mix(B, (1, 1, 1), 0.65), body * cov(np.abs(dy) - 0.9) * 0.9)
    return img


def dim(img):
    g = img[..., :3].mean(-1, keepdims=True)
    img[..., :3] = (img[..., :3] * 0.35 + g * 0.65) * 0.55
    img[..., 3:] *= 0.85
    return img


def make_holds(P, out):
    for kind, roll in (("Hold", False), ("Roll", True)):
        for act in ("Active", "Inactive"):
            frames = []
            for f in range(4):
                px, py = grid(64, 64)
                im = beam(P, px, py, f, roll, np.abs(px - 32) - EDGE)
                frames.append(im if act == "Active" else dim(im))
            save(sheet(frames, 4, 1), os.path.join(out, "Down %s Body %s 4x1 (res 256x64).png" % (kind, act)))
            px, py = grid(64, 32)
            top = beam(P, px, py, 0, roll, np.abs(px - 32) - EDGE, rings=False)
            top *= sstep(0, 30, py)[..., None]
            save(top if act == "Active" else dim(top), os.path.join(out, "Down %s TopCap %s (res 64x32).png" % (kind, act)))
            ext = EDGE * np.sqrt(np.clip(1 - (np.maximum(py - 8, 0) / 21) ** 2, 0, 1))
            bot = beam(P, px, py, 0, roll, np.abs(px - 32) - ext, rings=False)
            save(bot if act == "Active" else dim(bot), os.path.join(out, "Down %s BottomCap %s (res 64x32).png" % (kind, act)))


# ---------------------------------------------------------------- build
HERE = os.path.dirname(os.path.abspath(__file__))


def build(variant, out):
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png") or f.endswith(".lua"):
            os.remove(os.path.join(out, f))
    P = palette(variant)
    seed = {"color": 1, "pink": 2, "red": 3}[variant]
    J = lambda n: os.path.join(out, n)
    save(note_sheet(P), J("_CC Tap Note 4x16 (res 256x1024).png"))
    save(note_sheet(P, hollow=True), J("_CC Tap Lift 4x16 (res 256x1024).png"))
    save(rim_sheet(), J("_CC Tap Rim 4x16 (res 256x1024).png"))
    save(receptor_sheet(P), J("_CC Receptor 3x1 (res 192x64).png"))
    save(bolt_sheet(P, seed * 101), J("_CC Bolt 4x1 (res 256x64).png"))
    save(aura_sheet(P, seed), J("_CC Aura 8x1 (res 896x112).png"))
    save(fx_flash(P), J("_CC FX Flash (res 128x128).png"))
    save(fx_star(P, 128, 62, 1.3, 8.0), J("_CC FX Star (res 128x128).png"))
    save(fx_star(P, 32, 15, 0.6, 2.6), J("_CC FX Twinkle (res 32x32).png"))
    save(fx_ring(P), J("_CC FX Ring (res 128x128).png"))
    W = dict(P, fx=(1, 1, 1), fx2=(1, 1, 1))
    save(fx_ring(W), J("_CC FX RingW (res 128x128).png"))
    save(fx_star(W, 32, 15, 0.6, 2.6), J("_CC FX TwinkleW (res 32x32).png"))
    save(fx_arrowglow(), J("_CC FX ArrowGlow (res 64x64).png"))
    save(fx_lightning(P, seed), J("_CC FX Lightning 8x1 (res 1024x128).png"))
    save(fx_ember(P), J("_CC FX Ember (res 16x16).png"))
    save(fx_holdorb(P, seed), J("_CC FX HoldOrb 8x1 (res 512x64).png"))
    save(fx_mineblast(P, seed), J("_CC FX MineBlast (res 128x128).png"))
    make_mines(P, out, seed)
    make_holds(P, out)
    shards = make_shards(P, out, variant)
    lua = os.path.join(HERE, "lua")
    for f in os.listdir(lua):
        src = open(os.path.join(lua, f), encoding="utf-8").read()
        if f == "Down Explosion.lua":
            rows = "\n".join('\t{ "%s", %.1f, %.1f },' % s for s in shards)
            src = src.replace("--@SHARDS@", rows)
        src = src.replace("@VARIANT@", P["name"])
        open(os.path.join(out, f), "w", encoding="utf-8").write(src)
    print("built", variant, "->", out, len(os.listdir(out)), "files")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
