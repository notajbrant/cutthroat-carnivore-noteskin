"""Cutthroat Carnivore noteskin v2 - builds every texture into an output folder.
Usage: python3 fx_v2.py <outdir>
"""
import sys, os, math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
sys.path.insert(0, os.path.dirname(__file__))
import importlib
A = importlib.import_module({"v3": "arrow_v3", "v4": "arrow_v4"}.get(os.environ.get("CC_ARROW"), "arrow_v2"))

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(1666)
CRIMSON = np.array([1.0, 0.06, 0.12]); DEEP = np.array([0.45, 0.0, 0.03]); PINK = np.array([1.0, 0.55, 0.62])
HOT = np.array([1.0, 0.95, 0.95])
QUANT = ['ff1a2e', '2a7bff', 'a63cff', 'ffcc1a', 'ff3cb4', 'ff7a12', '1ee6ff', '3cff62', 'c8ccd8']
def hexc(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
def cycle(n=12):
    import colorsys
    return [np.array(colorsys.hsv_to_rgb(((i / n) * 0.92) % 1.0, 0.92, 1.0)) for i in range(n)]

def save_add(e, path):
    e = np.clip(e, 0, None); a = np.clip(e.max(-1, keepdims=True), 0, 1)
    rgb = np.where(a > 1e-4, np.clip(e / np.maximum(a, 1e-4), 0, 1), 0)
    Image.fromarray((np.concatenate([rgb, a], -1) * 255 + .5).astype(np.uint8), 'RGBA').save(path, optimize=True)

def grid(units, px_per_unit, ss=1):
    n = int(units * px_per_unit * ss); u = n / units
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / u - units / 2
    return n, u, xs, ys

def rasterize_lines(segs, n, u, widths):
    """segs: list of (polyline [(x,y) in px], weight). returns list of distance-based layers."""
    from matplotlib.path import Path  # noqa
    D = np.full((n, n), np.inf); Wt = np.zeros((n, n))
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    for pts, w in segs:
        pts = np.asarray(pts)
        x0, y0 = pts.min(0) - 12 * u; x1, y1 = pts.max(0) + 12 * u
        ix0, iy0 = max(0, int(x0)), max(0, int(y0)); ix1, iy1 = min(n, int(x1) + 1), min(n, int(y1) + 1)
        if ix0 >= ix1 or iy0 >= iy1: continue
        X = xs[iy0:iy1, ix0:ix1]; Y = ys[iy0:iy1, ix0:ix1]
        d = np.full(X.shape, np.inf)
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a; L2 = max(ab @ ab, 1e-9)
            t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / L2, 0, 1)
            d = np.minimum(d, np.hypot(X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1])))
        d = d / (w ** 0.6)            # thinner branches
        sub = D[iy0:iy1, ix0:ix1]; better = d < sub
        sub[better] = d[better]; Wt[iy0:iy1, ix0:ix1][better] = w
    return D / u, Wt

def mid_disp(a, b, rough, depth):
    if depth == 0: return [a, b]
    m = (a + b) / 2; v = b - a; L = np.hypot(*v)
    perp = np.array([-v[1], v[0]]) / max(L, 1e-9)
    m = m + perp * rng.normal(0, rough * L)
    return mid_disp(a, m, rough, depth - 1)[:-1] + mid_disp(m, b, rough, depth - 1)

def bolt_tree(start, angle, length, depth, segs_out, weight=1.0, rough=0.22):
    end = start + np.array([math.cos(angle), math.sin(angle)]) * length
    pts = mid_disp(np.array(start, float), end, rough, 5)
    segs_out.append((pts, weight))
    if depth > 0:
        for i in range(2 + int(rng.integers(0, 3))):
            k = int(rng.integers(len(pts) // 4, len(pts) - 2))
            ang = angle + rng.choice([-1, 1]) * (0.35 + rng.random() * 0.7)
            bolt_tree(pts[k], ang, length * (0.25 + rng.random() * 0.35), depth - 1, segs_out, weight * 0.6, rough * 1.1)

def shade_lightning(D, Wt, intensity=1.0):
    core = np.exp(-(D / 0.33) ** 2) * Wt
    inner = np.exp(-(D / 1.1) ** 2) * Wt
    outer = np.exp(-(D / 3.2) ** 2) * Wt
    haze = np.exp(-(D / 9.0) ** 2) * Wt
    e = (HOT[None, None] * core[..., None] * 1.4 + PINK[None, None] * inner[..., None] * 0.9
         + CRIMSON[None, None] * outer[..., None] * 0.95 + DEEP[None, None] * haze[..., None] * 0.9)
    return e * intensity

def lightning_sheet(path, frames=8, units=128, ppu=2, ss=2, mode='burst'):
    sheets = []
    for f in range(frames):
        n, u, xs, ys = grid(units, ppu, ss); segs = []
        c = np.array([n / 2, n / 2])
        if mode == 'burst':
            for b in range(4 + int(rng.integers(0, 3))):
                ang = rng.random() * 2 * math.pi
                bolt_tree(c + rng.normal(0, 2 * u, 2), ang, (36 + rng.random() * 22) * u, 2, segs)
        else:   # orb crackle
            for b in range(5 + int(rng.integers(0, 3))):
                ang = rng.random() * 2 * math.pi; r0 = 9 * u
                st = c + np.array([math.cos(ang), math.sin(ang)]) * r0
                bolt_tree(st, ang + rng.normal(0, 0.6), (12 + rng.random() * 13) * u, 1, segs, 0.9, 0.3)
        D, Wt = rasterize_lines(segs, n, u, None)
        e = shade_lightning(D, Wt)
        if mode != 'burst':
            r = np.hypot(xs, ys)
            e += HOT * np.exp(-(r / 4.5) ** 2)[..., None] * 1.2 + CRIMSON * np.exp(-(r / 11) ** 2)[..., None] * 1.0
        r_ = np.hypot(xs, ys)
        e *= np.clip((units / 2 * 0.97 - r_) / (units * 0.16), 0, 1)[..., None] ** 1.5   # no square edges
        sheets.append(A.downsample(e, ss))
    save_add(np.concatenate(sheets, 1), path)

def fx_singles():
    n, u, xs, ys = grid(128, 2, 2); r = np.hypot(xs, ys); a = np.arctan2(ys, xs)
    # flash with anamorphic streak
    e = HOT * np.exp(-(r / 7) ** 2)[..., None] * 1.5 + CRIMSON * np.exp(-(r / 22) ** 2)[..., None] * 1.0
    e += (PINK * 0.6 + CRIMSON * 0.4) * (np.exp(-(ys / 1.3) ** 2 - (xs / 58) ** 2))[..., None] * 1.1
    save_add(A.downsample(e, 2), f'{OUT}/_CC FX Flash (res 128x128).png')
    ring = np.exp(-((r - 54) / 1.4) ** 2) * 1.2 + np.exp(-((r - 50) / 4.5) ** 2) * 0.45 + np.exp(-((r - 44) / 1.0) ** 2) * 0.5
    save_add(A.downsample(np.repeat(ring[..., None], 3, -1), 2), f'{OUT}/_CC FX Ring (res 128x128).png')
    rays = np.zeros_like(r)
    for k in range(22):
        th = rng.random() * 2 * math.pi; ln = 34 + rng.random() * 28; wd = 0.025 + rng.random() * 0.04
        rel = np.abs((a - th + math.pi) % (2 * math.pi) - math.pi)
        fall = np.clip(1 - r / ln, 0, 1)
        rays = np.maximum(rays, np.exp(-(rel / (wd * np.maximum(fall, 0.05))) ** 2) * fall ** 1.5)
    e = CRIMSON * rays[..., None] * 1.2 + HOT * (rays ** 5)[..., None] * 1.1
    save_add(A.downsample(e, 2), f'{OUT}/_CC FX Rays (res 128x128).png')
    # dark smoke ring (normal blend): sells the "evil" weight of each hit
    noise = sum(gaussian_filter(rng.random((n, n)), s) * w for s, w in [(3, 1), (7, 1.2), (14, 1.0)])
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    puff = np.exp(-((r - 30) / 16) ** 2) * np.clip(noise * 1.8 - 0.35, 0, 1)
    rgb = np.stack([0.10 + 0.12 * puff, 0.01 + 0.01 * puff, 0.02 + 0.02 * puff], -1)
    alpha = np.clip(puff * 0.85, 0, 1)
    prem = np.concatenate([rgb * alpha[..., None], alpha[..., None]], -1)
    A.save_premul(A.downsample(prem, 2), f'{OUT}/_CC FX Smoke (res 128x128).png')
    em = CRIMSON * (np.exp(-((r - 28) / 6) ** 2) + np.exp(-(r / 10) ** 2) * 0.8)[..., None] + HOT * np.exp(-(r / 4) ** 2)[..., None]
    save_add(A.downsample(em, 2), f'{OUT}/_CC FX MineBlast (res 128x128).png')
    # spark streak + ember
    n2, u2 = 64 * 2, 2 * 2
    ys2, xs2 = (np.mgrid[0:16 * 2 * 2, 0:n2 * 2] + 0.5) / u2 - np.array([4, 16])[:, None, None] * 2
    st = np.exp(-((xs2 / 26) ** 2 + (ys2 / 1.8) ** 2))
    save_add(A.downsample(CRIMSON * st[..., None] * 1.3 + HOT * (st ** 6)[..., None], 2), f'{OUT}/_CC FX Spark (res 32x8).png')
    n3, u3, xs3, ys3 = grid(16, 2, 4); eb = np.exp(-(np.hypot(xs3, ys3) / 2.6) ** 2)
    save_add(A.downsample(np.array([1, .3, .1]) * eb[..., None] * 1.2 + HOT * (eb ** 5)[..., None], 4), f'{OUT}/_CC FX Ember (res 16x16).png')

def aura(path, frames=8, units=112, ppu=2, ss=2):
    n = units * ppu * ss; sc = 64 / units; off = (1 - sc) / 2
    sil = [(off + x * sc, off + y * sc) for x, y in A.silhouette()]
    sdf = A.poly_sdf(sil, n); u = n / units
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / u - units / 2
    th = np.arctan2(ys, xs); up = np.clip(-np.sin(th), 0, 1)
    out = []
    for f in range(frames):
        t = f / frames * 2 * math.pi; sp = np.zeros_like(th)
        for k, amp in [(7, .5), (13, .32), (23, .18), (41, .1)]:
            sp += amp * (0.5 + 0.5 * np.cos(k * th + rng.random() * 6.28 + t * (1 + k / 9)))
        sp = sp ** 2.4
        reach = (2.0 + 16 * sp * (0.4 + 0.8 * up)) * u
        dd = np.clip(sdf, 0, None)
        flame = np.exp(-dd / reach) * (sdf > -0.8 * u) * np.clip(1 - dd / (26 * u), 0, 1)
        e = (DEEP * flame[..., None] * 1.0 + CRIMSON * (flame ** 2)[..., None] * 1.2 + HOT * (flame ** 6)[..., None] * 0.9
             + CRIMSON * np.exp(-np.clip(sdf + 0.3 * u, 0, None) / (1.6 * u))[..., None] * 0.5)
        out.append(A.downsample(e, ss))
    save_add(np.concatenate(out, 1), path)

def hold_parts(kind):
    K = 'Hold' if kind == 'hold' else 'Roll'
    ppu, ss = 2, 4
    def body(active, units_h, seed):
        Wn = 64 * ppu * ss; Hn = units_h * ppu * ss; u = Wn / 64
        X = np.tile((np.arange(Wn) + .5) / u - 32, (Hn, 1)); Y = np.tile(((np.arange(Hn) + .5) / u)[:, None], (1, Wn))
        prem = np.zeros((Hn, Wn, 4)); half = 21
        chan = np.clip(half + 0.5 - np.abs(X), 0, 1)
        prem[..., 3] = chan * 0.82; prem[..., :3] = np.array([0.01, 0.0, 0.005]) * prem[..., 3:4]
        # black lacquer rails with a cold specular stripe
        rail = chan * np.clip((np.abs(X) - (half - 4)) * 2, 0, 1)
        prof = np.cos((np.abs(X) - (half - 2)) / 2 * math.pi / 2).clip(0, 1)
        rgb = 0.03 + np.stack([prof ** 12 * 0.9] * 3, -1) * np.array([0.8, 0.85, 1.0]) + np.stack([prof * 0.06] * 3, -1)
        prem[..., :3] = prem[..., :3] * (1 - rail[..., None]) + rgb * rail[..., None]
        prem[..., 3] = np.maximum(prem[..., 3], rail)
        e = np.zeros((Hn, Wn, 3)); dim = 1.0 if active else 0.32
        if kind == 'hold':   # lightsaber blade: white core, crimson bloom, gentle seamless flicker
            fl = 1 + 0.08 * np.sin(Y / units_h * 2 * math.pi * 3) + 0.05 * np.sin(Y / units_h * 2 * math.pi * 7 + 1)
            e += HOT * np.exp(-(X / (1.8 * fl)) ** 2)[..., None] * 1.3
            e += CRIMSON * np.exp(-(X / (5.5 * fl)) ** 2)[..., None] * 1.1
            e += DEEP * np.exp(-(X / 13) ** 2)[..., None] * 0.9
        else:                # roll: force lightning crawling down the channel (tiles seamlessly)
            n = Wn
            for b in range(2):
                pts = mid_disp(np.array([Wn / 2, -2.0]), np.array([Wn / 2, Hn + 2.0]), 0.12 + 0.05 * b, 6)
                pts = [np.array([np.clip(p[0], 6 * u, Wn - 6 * u), p[1]]) for p in pts]
                D, Wt = rasterize_lines([(pts, 1.0 - 0.35 * b)], max(Wn, Hn), u, None)
                D = D[:Hn, :Wn]; Wt = Wt[:Hn, :Wn]
                e += shade_lightning(D, Wt, 1.0)
        e *= dim
        if not active:
            g = e.mean(-1, keepdims=True); e = e * 0.3 + g * 0.7
        a = np.clip(e.max(-1), 0, 1)
        prem[..., :3] = prem[..., :3] * (1 - a[..., None] * 0.0) + e   # additive light on top
        prem[..., 3] = np.clip(prem[..., 3] + a * 0.5, 0, 1)
        prem[..., :3] = np.minimum(prem[..., :3], prem[..., 3:4])
        return prem, X, Y, u
    for active in (True, False):
        st = 'Active' if active else 'Inactive'
        b, *_ = body(active, 64, 1)
        A.save_premul(A.downsample(b, ss), f'{OUT}/Down {K} Body {st} (res 64x64).png')
        cap, X, Y, u = body(active, 32, 2)
        taper = 21 * np.clip(1 - (Y / 30) ** 1.6, 0, 1) + 0.6
        m = gaussian_filter(np.clip(taper - np.abs(X) + 0.5, 0, 1), 0.6 * u)
        cap *= m[..., None]
        A.save_premul(A.downsample(cap, ss), f'{OUT}/Down {K} BottomCap {st} (res 64x32).png')
        A.save_premul(A.downsample(cap[::-1].copy(), ss), f'{OUT}/Down {K} TopCap {st} (res 64x32).png')

def mine():
    n, u, xs, ys = grid(64, 2, 4); r = np.hypot(xs, ys); ang = np.arctan2(ys, xs)
    # black orb with molten fractures
    nz = np.sqrt(np.clip(1 - (r / 16) ** 2, 0, 1)); orb = np.clip(16.5 - r, 0, 1)
    nx, ny = xs / 16, ys / 16
    Lk = np.array([-0.45, -0.62, 0.64]); Lk /= np.linalg.norm(Lk)
    spec = np.clip((nx * Lk[0] + ny * Lk[1] + nz * Lk[2]) * 0.5 + 0.5, 0, 1) ** 40 * 1.5
    rim = (1 - nz) ** 3
    rgb = 0.02 + spec[..., None] * np.array([.85, .9, 1]) + rim[..., None] * CRIMSON * 0.5
    segs = []
    c = np.array([n / 2, n / 2])
    for k in range(6):
        a0 = k / 6 * 2 * math.pi + rng.random() * 0.5
        segs.append((mid_disp(c, c + np.array([math.cos(a0), math.sin(a0)]) * 15 * u, 0.25, 4), 1.0))
    D, Wt = rasterize_lines(segs, n, u, None)
    e = shade_lightning(D, Wt, 0.8) * orb[..., None]
    prem = np.concatenate([(rgb + e) * orb[..., None], orb[..., None]], -1)
    prem[..., :3] = np.minimum(prem[..., :3], prem[..., 3:4])
    A.save_premul(A.downsample(prem, 4), f'{OUT}/_CC Mine Base (res 64x64).png')
    bl = np.zeros_like(r)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        rel = (ang - a + math.pi) % (2 * math.pi) - math.pi
        w = 0.30 * np.clip(1 - (r - 15) / 15, 0, 1) - rel * 0.18
        bl = np.maximum(bl, ((np.abs(rel - 0.1) < w) & (r > 15) & (r < 30.5)).astype(float))
    bl = gaussian_filter(bl, 0.5 * u)
    sp = np.clip(np.cos(ang * 8 + 0.4), 0, 1) ** 6 * 0.5
    rgb = 0.04 + sp[..., None] * np.array([.8, .85, 1]) + CRIMSON * gaussian_filter(bl, 1.5 * u)[..., None] * 0.15
    A.save_premul(A.downsample(np.concatenate([rgb * bl[..., None], bl[..., None]], -1), 4), f'{OUT}/_CC Mine Spokes (res 64x64).png')
    save_add(A.downsample(CRIMSON * np.exp(-(r / 12) ** 2)[..., None] * 1.3, 4), f'{OUT}/_CC Mine Glow (res 64x64).png')

def notes():
    fr = 128
    for name, pal in (('Quant', [hexc(h) for h in QUANT]), ('Cycle', cycle())):
        for mode, el in (('note', 'Tap Note'), ('lift', 'Tap Lift')):
            sheet = np.zeros((16 * fr, 4 * fr, 4))
            for r_, c in enumerate(pal):
                for f in range(4):
                    sheet[r_ * fr:(r_ + 1) * fr, f * fr:(f + 1) * fr] = A.render(c, f, mode=mode)
            A.save_premul(sheet, f'{OUT}/_CC {el} {name} 4x16 (res 256x1024).png')

def receptor():
    c = CRIMSON
    fr = [A.render(c, mode='receptor_base'), A.render(c, mode='receptor_flash'), A.render(c, mode='receptor_press')]
    A.save_premul(np.concatenate(fr, 1), f'{OUT}/_CC Receptor 3x1 (res 192x64).png')

if __name__ == '__main__':
    what = sys.argv[2:] or ['notes', 'receptor', 'aura', 'fx', 'lightning', 'holds', 'mine']
    if 'notes' in what: notes()
    if 'receptor' in what: receptor()
    if 'aura' in what: aura(f'{OUT}/_CC Receptor Aura 8x1 (res 896x112).png')
    if 'fx' in what: fx_singles()
    if 'lightning' in what:
        lightning_sheet(f'{OUT}/_CC FX Lightning 8x1 (res 1024x128).png')
        lightning_sheet(f'{OUT}/_CC FX HoldOrb 8x1 (res 512x64).png', units=64, mode='orb')
    if 'holds' in what: hold_parts('hold'); hold_parts('roll')
    if 'mine' in what: mine()
    print('done', what)

# ---------------- shatter: fracture the arrow into armour shards (particles) ----------------
def shards(nshards=int(os.environ.get('CC_SHARDS', 12)), seed=9):
    from scipy.ndimage import distance_transform_edt
    r = np.random.default_rng(seed)
    g = A.geometry(128); n, u, d = g['n'], g['u'], g['sdf']
    sc = np.array([float(v) for v in os.environ['CC_SHARD_COL'].split(',')]) if os.environ.get('CC_SHARD_COL') else CRIMSON
    full = A.render(sc, 2, mode='note')                 # 128x128 premultiplied (bolt off)
    inside_ss = d <= 0
    cov = A.downsample(inside_ss[..., None].astype(float))[..., 0]
    # seed points spread over the silhouette (rejection sampling with min spacing)
    pts = []
    while len(pts) < nshards:
        p = r.random(2) * n
        if d[int(p[1]), int(p[0])] < -1.2 * u and all(np.hypot(*(p - q)) > (11 if nshards <= 12 else 6.2) * u for q in pts):
            pts.append(p)
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    lab = np.argmin([(xs - p[0]) ** 2 + (ys - p[1]) ** 2 for p in pts], axis=0)
    lab_ds = lab[::A.SS, ::A.SS]
    entries = []
    for k in range(nshards):
        own = (lab == k)
        dist_other = distance_transform_edt(own | ~inside_ss) / u       # distance to neighbouring shards only
        crack = np.exp(-(dist_other / 0.55) ** 2) * own * inside_ss
        crackc = np.exp(-(dist_other / 0.2) ** 2) * own * inside_ss
        if os.environ.get('CC_SHARD_COL'):
            crack = crack * 1.0
        cov_k = A.downsample((own & inside_ss)[..., None].astype(float))[..., 0]
        e = A.downsample(CRIMSON * crack[..., None] * 1.3 + HOT * crackc[..., None] * 0.9)
        img = full * (cov_k / np.maximum(cov, 1e-4))[..., None]
        img[..., 3] = cov_k
        img[..., :3] = img[..., :3] * cov_k[..., None] / np.maximum(full[..., 3:4], 1e-4) if False else img[..., :3]
        img[..., :3] = np.minimum(img[..., :3] + e * cov_k[..., None], img[..., 3:4])
        yy, xx = np.nonzero(cov_k > 0.01)
        y0, y1, x0, x1 = yy.min() - 2, yy.max() + 3, xx.min() - 2, xx.max() + 3
        if (y1 - y0) % 2: y1 += 1
        if (x1 - x0) % 2: x1 += 1
        crop = img[max(0, y0):y1, max(0, x0):x1]
        hh, ww = crop.shape[:2]
        if hh % 2: crop = np.pad(crop, ((0, 1), (0, 0), (0, 0))); hh += 1
        if ww % 2: crop = np.pad(crop, ((0, 0), (0, 1), (0, 0))); ww += 1
        name = f'_CC Shard {k + 1:02d} (res {ww // 2}x{hh // 2}).png'
        A.save_premul(crop, f'{OUT}/{name}')
        cx = (max(0, x0) + ww / 2) / 2 - 32; cy = (max(0, y0) + hh / 2) / 2 - 32   # centre in noteskin units
        entries.append((f'_CC Shard {k + 1:02d}', round(cx, 2), round(cy, 2)))
    with open(f'{OUT}/_CC Shards.lua', 'w') as f:
        f.write('-- Generated: shard texture names and their resting offsets (noteskin units, Down arrow)\nreturn {\n')
        for nm, cx, cy in entries:
            f.write(f'\t{{ tex = "{nm}", x = {cx}, y = {cy} }},\n')
        f.write('}\n')
    # micro debris: solid molten slivers (hot core -> crimson -> dark edge)
    n2, u2, xs2, ys2 = grid(16, 2, 4)
    tri = A.poly_sdf([(0.5, 0.04), (0.78, 0.92), (0.30, 0.70)], n2) / u2
    m = np.clip(0.5 - tri * 3, 0, 1)
    depth = np.clip(-tri / 1.6, 0, 1)
    rgb = CRIMSON * (0.55 + 0.45 * depth)[..., None] * 1.1 + HOT * (depth ** 3)[..., None] * 0.8
    prem = np.concatenate([np.minimum(rgb * m[..., None], m[..., None]), m[..., None]], -1)
    A.save_premul(A.downsample(prem, 4), f'{OUT}/_CC FX Debris (res 16x16).png')
    return entries

if __name__ == '__main__' and 'shards' in sys.argv[2:]:
    print(shards())
