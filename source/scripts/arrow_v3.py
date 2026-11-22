"""Cutthroat Carnivore noteskin v3 'Forged' - hammered, scratched dark iron, serrated blade
silhouette, armour cracked open with energy burning through the fractures (note colour),
blazing on every beat. Original procedural art.
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter
import arrow_v2 as V2          # reuse sdf / helpers / save
from arrow_v2 import poly_sdf, seg_dist, downsample, save_premul, add_to_rgba, bez

SS = 4
HOT = np.array([1.0, 0.92, 0.85])

def silhouette():
    # v2's barbed blade outline (reads instantly as an arrow), with a longer, meaner tip
    pts = V2.silhouette()
    return [(0.50, 0.99) if (abs(x - 0.5) < 1e-6 and y > 0.9) else (x, y) for x, y in pts]

def _mid(a, b, rough, depth, r):
    if depth == 0: return [a, b]
    m = (a + b) / 2; v = b - a; L = np.hypot(*v)
    m = m + np.array([-v[1], v[0]]) / max(L, 1e-9) * r.normal(0, rough * L)
    return _mid(a, m, rough, depth - 1, r)[:-1] + _mid(m, b, rough, depth - 1, r)

def _polys_dist(paths, n, weights=None):
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    D = np.full((n, n), np.inf)
    for i, pts in enumerate(paths):
        w = 1.0 if weights is None else weights[i]
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a; t = np.clip(((xs - a[0]) * ab[0] + (ys - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            D = np.minimum(D, np.hypot(xs - (a[0] + t * ab[0]), ys - (a[1] + t * ab[1])) / w)
    return D

_G = {}
def geometry(px=128, ss=SS):
    k = (px, ss)
    if k in _G: return _G[k]
    n = px * ss; u = n / 64.0
    sil = silhouette()
    sdf = poly_sdf(sil, n)
    r = np.random.default_rng(666)
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / n
    # ---- forged height field ----
    B = 2.4 * u
    bev = np.clip(-sdf / B, 0, 1); bev = 1 - (1 - bev) ** 2.5
    spine = seg_dist([(0.5, 0.185), (0.5, 0.985)], n)
    wingL = seg_dist([(0.5, 0.80), (0.075, 0.29)], n); wingR = seg_dist([(0.5, 0.80), (0.925, 0.29)], n)
    hornL = seg_dist([(0.40, 0.17), (0.255, 0.03)], n); hornR = seg_dist([(0.60, 0.17), (0.745, 0.03)], n)
    ridge = np.clip(np.maximum.reduce([1.0 - spine / (6.0 * u), 0.8 - np.minimum(wingL, wingR) / (7.0 * u),
                                       0.6 - np.minimum(hornL, hornR) / (3.5 * u)]), 0, None)
    hammer = sum(gaussian_filter(r.random((n, n)), s * ss) * w for s, w in [(1.5, 0.6), (4, 1.0), (9, 0.8)])
    hammer = (hammer - hammer.mean()) / (hammer.std() + 1e-6)
    # scratches: thin random grooves
    scr = np.zeros((n, n))
    for _ in range(26):
        p0 = r.random(2) * n; ang = r.normal(-0.6, 0.5); L = (6 + r.random() * 22) * u
        p1 = p0 + np.array([math.cos(ang), math.sin(ang)]) * L
        d = seg_dist([tuple(p0 / n), tuple(p1 / n)], n)
        scr = np.maximum(scr, np.exp(-(d / (0.18 * u)) ** 2) * r.uniform(0.4, 1.0))
    # fracture network (static cracks the energy burns through)
    c = np.array([0.5, 0.64]) * n
    paths, wts = [], []
    ends = [(0.5, 0.95), (0.13, 0.50), (0.87, 0.50), (0.5, 0.26), (0.30, 0.38), (0.70, 0.38), (0.33, 0.70), (0.67, 0.70)]
    for e in ends:
        pts = _mid(c, np.array(e) * n, 0.16, 5, r); paths.append(pts); wts.append(1.0)
        for _ in range(2):
            p = pts[int(r.integers(len(pts) // 3, len(pts) - 1))]
            ang = r.random() * 2 * math.pi
            paths.append(_mid(p, p + np.array([math.cos(ang), math.sin(ang)]) * (3 + r.random() * 6) * u, 0.25, 3, r)); wts.append(0.55)
    crackD = _polys_dist(paths, n, wts) / u
    inner = np.clip((-sdf - 1.6 * u) / (0.8 * u), 0, 1)               # cracks stay off the rim
    h = (bev * (1.0 + 1.7 * ridge) * 2.2 + hammer * 0.10 * bev - scr * 0.35 * bev
         - np.exp(-(crackD / 0.9) ** 2) * inner * 1.2) * u
    h = gaussian_filter(h, 0.5 * ss)
    gy, gx = np.gradient(h)
    nrm = np.sqrt(gx ** 2 + gy ** 2 + 1)
    N = np.stack([-gx / nrm, -gy / nrm, 1 / nrm], -1)
    cav = np.clip((gaussian_filter(h, 3 * ss) - h) / u, 0, None)       # soot in the creases
    edge_wear = np.exp(-((sdf + 0.9 * u) / (0.9 * u)) ** 2) + ridge ** 6 * 0.6
    _G[k] = dict(n=n, u=u, sdf=sdf, N=N, cav=cav, wear=edge_wear, scr=scr, crackD=crackD, inner=inner,
                 xs=xs, ys=ys, hammer=hammer)
    return _G[k]

FLASH = [1.0, 0.55, 0.32, 0.22]

def shade_metal(g, col, under=0.35):
    N = g['N']; nz = N[..., 2]
    Lk = np.array([-0.5, -0.62, 0.6]); Lk /= np.linalg.norm(Lk)
    H = Lk + np.array([0, 0, 1.0]); H /= np.linalg.norm(H)
    diff = np.clip(N @ Lk, 0, 1)
    spec = np.clip(N @ H, 0, 1) ** 28 * 0.45                       # satin, not gloss
    Lu = np.array([0.15, 0.85, 0.5]); Lu /= np.linalg.norm(Lu)     # hellfire bounce from below
    underl = np.clip(N @ Lu, 0, 1) ** 2
    iron = np.array([0.06, 0.055, 0.06]) * (1 + 0.12 * g['hammer'][..., None])
    worn = np.array([0.24, 0.23, 0.25])
    wear = np.clip(g['wear'] * (0.5 + 0.5 * np.clip(g['hammer'], 0, 1)) + g['scr'] * 0.8, 0, 1)
    alb = iron * (1 - wear[..., None]) + worn * wear[..., None]
    rgb = alb * (0.22 + diff[..., None] * 1.25) + spec[..., None] * np.array([0.9, 0.9, 1.0])
    rgb += (col * 0.6 + np.array([0.5, 0.0, 0.0]) * 0.4) * underl[..., None] * under * 0.35
    rgb *= np.clip(1 - g['cav'] * 0.9, 0.25, 1)[..., None]
    return rgb

def render(col, frame=0, nframes=4, mode='note', px=128):
    g = geometry(px); n, u, d = g['n'], g['u'], g['sdf']
    col = np.asarray(col, float)
    fl = FLASH[frame % 4]
    inside = np.clip(0.5 - d, 0, 1)
    out = np.zeros((n, n, 4))
    if mode in ('note', 'lift'):
        e = 1.0 if mode == 'note' else 0.35
        metal = shade_metal(g, col)
        D = g['crackD']; inn = g['inner']
        # per-frame crawling sparks along the cracks
        rr = np.random.default_rng(90 + frame)
        crawl = gaussian_filter(rr.random((n, n)), 2.5 * SS); crawl = np.clip((crawl - crawl.mean()) / crawl.std(), 0, None)
        core = np.exp(-(D / 0.26) ** 2) * inn
        glow = np.exp(-(D / 0.85) ** 2) * inn
        heat = np.exp(-(D / 3.0) ** 2) * inn                           # metal heated around the fractures
        k = (0.45 + 0.75 * fl) * e
        emis = (HOT * (core * (0.75 + 0.6 * fl) * (0.8 + 0.4 * crawl))[..., None]
                + col * (glow * 1.15 * k)[..., None] + col * (heat * 0.42 * k)[..., None])
        # thin colour rim so the note reads at speed on any background
        rim = np.exp(-((d + 0.55 * u) / (0.5 * u)) ** 2)
        emis += col * (rim * (1.0 + 0.3 * fl) * e)[..., None]
        rgb = metal * (1 - np.clip(glow, 0, 1)[..., None] * 0.85) + emis
        if mode == 'lift':
            inside = inside * (1 - np.clip((-d - 4 * u) / u, 0, 1) * 0.6)
        out[..., :3] = np.minimum(rgb, 1.5) * inside[..., None]; out[..., 3] = inside
        # dark smoky halo + tight colour bloom from the cracks and rim
        src = col * (glow * 0.6 + rim * 0.5)[..., None] * k
        bloom = gaussian_filter(src, (1.8 * u, 1.8 * u, 0)) * 1.4
        ga = np.clip(bloom.max(-1), 0, 0.85) * (1 - inside)
        smoke = np.clip(gaussian_filter(inside, 2.6 * u) * 1.6, 0, 1) * (1 - inside) * 0.8
        out[..., 3] += smoke * (1 - ga)                                   # soot shadow keeps it readable on bright bgs
        out[..., :3] += bloom / np.maximum(bloom.max(-1, keepdims=True), 1e-4) * ga[..., None]
        out[..., 3] = np.clip(out[..., 3] + ga, 0, 1)
    elif mode == 'receptor_base':
        frame_band = inside * np.clip((d + 3.2 * u) / (0.6 * u), 0, 1)
        visor = inside * (1 - np.clip((d + 3.2 * u) / (0.6 * u), 0, 1))
        metal = shade_metal(g, col, under=0.2) * 1.8 + 0.05
        rim = np.exp(-((d + 0.45 * u) / (0.42 * u)) ** 2) * 1.6 + np.exp(-((d + 3.2 * u) / (0.3 * u)) ** 2) * 0.9
        hotl = np.exp(-((d + 0.45 * u) / (0.14 * u)) ** 2)
        rgb = metal + col * rim[..., None] + HOT * hotl[..., None] * 0.45
        out[..., :3] = rgb * frame_band[..., None] + np.array([0.02, 0.0, 0.0]) * visor[..., None] * 0.75
        out[..., 3] = frame_band + visor * 0.75
        # dark backing so the receptors never disappear into busy song art
        shadow = np.clip(gaussian_filter(inside, 2.4 * u) * 1.7, 0, 1) * (1 - inside) * 0.85
        out[..., 3] = np.clip(out[..., 3] + shadow, 0, 1)
        out[..., :3] = np.minimum(out[..., :3], out[..., 3:4] + 0.5)
    elif mode == 'receptor_flash':
        rim = np.exp(-((d + 0.8 * u) / (0.8 * u)) ** 2); hot = np.exp(-((d + 0.8 * u) / (0.26 * u)) ** 2)
        out = add_to_rgba(col[None, None] * rim[..., None] * 1.1 + HOT * hot[..., None] * 0.7)
    elif mode == 'receptor_press':
        D = g['crackD']; inn = g['inner'] * (d < 0)
        e = (col * (np.exp(-(D / 1.0) ** 2) * inn)[..., None] * 1.3 + HOT * (np.exp(-(D / 0.3) ** 2) * inn)[..., None]
             + col * (inside * 0.35)[..., None])
        out = add_to_rgba(e)
    return downsample(out)
