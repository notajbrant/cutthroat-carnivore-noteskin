"""Cutthroat Carnivore noteskin - v2 'Sith armour' arrow renderer (original procedural art).
Glossy black lacquered, faceted armour lit with a key light + studio reflections,
emissive slits/core that burn through the armour in the note colour.
"""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from matplotlib.path import Path

SS = 4
HOT = np.array([1.0, 0.93, 0.92])

def bez(p0, p1, p2, n=10):
    t = np.linspace(0, 1, n)[:, None]
    return list(map(tuple, (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)))

def silhouette():
    R = []
    R += [(0.50, 0.975), (0.968, 0.508)]                  # tip -> right wing edge
    R += [(0.925, 0.285)]                                 # barb spike swept back
    R += bez((0.925, 0.285), (0.86, 0.36), (0.80, 0.40), 6)[1:]
    R += [(0.635, 0.565)]                                 # inner shoulder
    R += [(0.622, 0.175)]                                 # stem right edge
    R += bez((0.622, 0.175), (0.70, 0.13), (0.745, 0.03), 9)[1:]   # horn outer curve
    R += bez((0.745, 0.03), (0.645, 0.075), (0.575, 0.135), 9)[1:]  # horn inner curve
    R += [(0.50, 0.185)]                                  # centre notch
    L = [(1 - x, y) for x, y in reversed(R[1:])]
    return R + L

def poly_sdf(pts, n):
    ys, xs = np.mgrid[0:n, 0:n]
    P = np.stack([(xs + 0.5) / n, (ys + 0.5) / n], -1).reshape(-1, 2)
    pts = np.asarray(pts, float)
    inside = Path(pts).contains_points(P).reshape(n, n)
    d = np.full(P.shape[0], np.inf)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        ab = b - a; t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(*(P - (a + t[:, None] * ab)).T))
    d = d.reshape(n, n) * n
    return np.where(inside, -d, d)

def seg_dist(pts, n):
    ys, xs = np.mgrid[0:n, 0:n]
    P = np.stack([(xs + 0.5) / n, (ys + 0.5) / n], -1).reshape(-1, 2)
    pts = np.asarray(pts, float); d = np.full(P.shape[0], np.inf)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ab = b - a
        t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(*(P - (a + t[:, None] * ab)).T))
    return d.reshape(n, n) * n

_G = {}
def geometry(px=128, ss=SS, shape=None, key='arrow'):
    k = (key, px, ss)
    if k in _G: return _G[k]
    n = px * ss; u = n / 64.0
    sdf = poly_sdf(shape or silhouette(), n)
    # --- height field: rounded bevel + hard creases (faceted helmet look) ---
    B = 3.2 * u
    bev = np.clip(-sdf / B, 0, 1); bev = 1 - (1 - bev) ** 2.2
    spine = seg_dist([(0.5, 0.185), (0.5, 0.975)], n)
    wingL = seg_dist([(0.5, 0.80), (0.075, 0.29)], n)
    wingR = seg_dist([(0.5, 0.80), (0.925, 0.29)], n)
    hornL = seg_dist([(0.40, 0.17), (0.255, 0.03)], n)
    hornR = seg_dist([(0.60, 0.17), (0.745, 0.03)], n)
    ridge = np.maximum.reduce([
        1.0 - spine / (7.0 * u),
        0.75 - np.minimum(wingL, wingR) / (8.0 * u),
        0.55 - np.minimum(hornL, hornR) / (4.0 * u),
    ])
    ridge = np.clip(ridge, 0, None)
    h = bev * (1.0 + 1.9 * ridge) * u * 2.4
    h = gaussian_filter(h, 0.6 * ss)
    gy, gx = np.gradient(h)
    nz = np.ones_like(h)
    nrm = np.sqrt(gx ** 2 + gy ** 2 + nz ** 2)
    N = np.stack([-gx / nrm, -gy / nrm, nz / nrm], -1)
    # emissive slits: inset parallel to each wing, plus a burning core gem
    slitL = seg_dist([(0.255, 0.535), (0.455, 0.735)], n)
    slitR = seg_dist([(0.745, 0.535), (0.545, 0.735)], n)
    stem = seg_dist([(0.5, 0.27), (0.5, 0.50)], n)
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / n
    gem = np.abs(xs - 0.5) / 0.055 + np.abs(ys - 0.635) / 0.085      # diamond metric
    _G[k] = dict(n=n, u=u, sdf=sdf, N=N, slit=np.minimum(slitL, slitR), stem=stem, gem=gem,
                 xs=xs, ys=ys, ridge=ridge)
    return _G[k]

_BOLTS = {}
def _mid(a, b, rough, depth, r):
    if depth == 0: return [a, b]
    m = (a + b) / 2; v = b - a; L = np.hypot(*v)
    m = m + np.array([-v[1], v[0]]) / max(L, 1e-9) * r.normal(0, rough * L)
    return _mid(a, m, rough, depth - 1, r)[:-1] + _mid(m, b, rough, depth - 1, r)

def panel_lightning(frame, n, u):
    """Distance field (units) of the crackling bolt network inside the arrow face for one frame."""
    k = (frame, n)
    if k in _BOLTS: return _BOLTS[k]
    r = np.random.default_rng(400 + frame)
    S = lambda x, y: np.array([x * n, y * n])
    paths = [_mid(S(0.5, 0.20), S(0.5, 0.90), 0.10, 5, r)]
    hub = paths[0][int(len(paths[0]) * 0.62)]
    paths += [_mid(hub, S(0.14, 0.50), 0.13, 4, r), _mid(hub, S(0.86, 0.50), 0.13, 4, r)]
    for _ in range(5):
        base = paths[int(r.integers(0, 3))]; p = base[int(r.integers(2, len(base) - 2))]
        ang = r.random() * 2 * math.pi
        paths.append(_mid(p, p + np.array([math.cos(ang), math.sin(ang)]) * (5 + r.random() * 7) * u, 0.18, 3, r))
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    D = np.full((n, n), np.inf)
    for i, pts in enumerate(paths):
        w = 1.0 if i < 3 else 0.6
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a; t = np.clip(((xs - a[0]) * ab[0] + (ys - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            D = np.minimum(D, np.hypot(xs - (a[0] + t * ab[0]), ys - (a[1] + t * ab[1])) / w)
    _BOLTS[k] = D / u
    return _BOLTS[k]

FLASH = [1.0, 0.62, 0.40, 0.30]          # brightness per quarter beat: strike on the beat, then decay

def env(R, red):
    rx, ry, rz = R[..., 0], R[..., 1], R[..., 2]
    soft = np.exp(-(((rx + 0.42) ** 2) / 0.05 + ((ry + 0.55) ** 2) / 0.03)) * 2.2      # key softbox
    strip = np.exp(-((rx - 0.62) ** 2) / 0.006) * np.clip(-ry + 0.3, 0, 1) * 0.55      # cold strip light
    under = np.clip(ry, 0, 1) ** 1.6 * 0.9                                              # hellfire from below
    base = 0.012
    cool = np.array([0.80, 0.86, 1.0])
    return (base + soft[..., None] * cool + strip[..., None] * cool + under[..., None] * red)

def render(col, frame=0, nframes=4, mode='note', px=128):
    """mode: note | lift | receptor_base | receptor_flash | receptor_press"""
    g = geometry(px)
    n, u, d, N = g['n'], g['u'], g['sdf'], g['N']
    col = np.asarray(col, float)
    ph = frame / nframes
    beat = 0.5 + 0.5 * math.cos(ph * 2 * math.pi)                  # 1 on the beat
    heart = 0.80 + 0.20 * beat
    inside = np.clip(0.5 - d / 1.0, 0, 1)                           # AA'd coverage at SS res
    V = np.array([0, 0, 1.0])
    nz = N[..., 2]
    Rf = np.stack([2 * nz * N[..., 0], 2 * nz * N[..., 1], 2 * nz * nz - 1], -1)
    fres = 0.045 + 0.955 * (1 - np.clip(nz, 0, 1)) ** 4
    Lk = np.array([-0.45, -0.62, 0.64]); Lk /= np.linalg.norm(Lk)
    Hk = (Lk + V); Hk /= np.linalg.norm(Hk)
    diff = np.clip(N @ Lk, 0, 1)
    spec = np.clip(N @ Hk, 0, 1) ** 90 * 2.6
    redenv = col * 0.55 + np.array([0.6, 0.0, 0.03]) * 0.45         # underglow picks up the note colour
    albedo = np.array([0.075, 0.07, 0.08]) + col * 0.05
    # micro-scratches so it reads as worn armour, not plastic
    rng = np.random.default_rng(31)
    grain = gaussian_filter(rng.random((n, n)), 0.7 * SS) - 0.5
    rough = 1 + grain[..., None] * 0.35
    armour = albedo * (0.45 + diff[..., None] * 1.2) + col * 0.035 + fres[..., None] * env(Rf, redenv) * rough + spec[..., None] * np.array([1, 0.97, 0.95])
    # emissive
    slit = np.exp(-(g['slit'] / (1.15 * u)) ** 2); slitc = np.exp(-(g['slit'] / (0.42 * u)) ** 2)
    stem = np.exp(-(g['stem'] / (1.0 * u)) ** 2); stemc = np.exp(-(g['stem'] / (0.38 * u)) ** 2)
    gem = np.clip(1.25 - g['gem'], 0, 1); gemc = np.clip(1.0 - g['gem'] * 1.6, 0, 1)
    emis_mask = np.clip(slit + stem * 0.9 + gem, 0, 1)
    hotmask = np.clip(slitc + stemc * 0.9 + gemc, 0, 1)
    out = np.zeros((n, n, 4))
    if mode in ('note', 'lift'):
        e = mode == 'note'
        fl = FLASH[frame % 4] if e else 0.35
        panel = np.clip((-d - 3.0 * u) / (0.5 * u), 0, 1)               # recessed face inside the armour bevel
        D = panel_lightning(frame % 4, n, u)
        boltc = np.exp(-(D / 0.30) ** 2); bolti = np.exp(-(D / 0.9) ** 2); bolto = np.exp(-(D / 2.6) ** 2)
        lightning = (HOT * (boltc * fl)[..., None] * 1.1 + col * (bolti * (0.55 + 0.6 * fl))[..., None] * 1.2
                     + col * (bolto * (0.35 + 0.5 * fl))[..., None] * 0.8) * panel[..., None]
        base_glow = col * (0.20 + 0.22 * fl) * panel[..., None] * (0.7 + 0.3 * np.exp(-np.clip(-d - 3 * u, 0, None) / (5 * u)))[..., None]
        if not e:
            lightning *= 0.35; base_glow *= 0.25
        surf = armour * (1 - panel[..., None] * 0.92) + base_glow + lightning
        gemk = np.clip(1.25 - g['gem'], 0, 1) * panel
        surf += (HOT * 0.9 + col * 0.6) * gemk[..., None] * (0.6 + 0.6 * fl) * (1 if e else 0.3)
        rim = np.exp(-((d + 0.75 * u) / (0.75 * u)) ** 2)
        rimc = np.exp(-((d + 0.75 * u) / (0.25 * u)) ** 2)
        surf += col * rim[..., None] * (0.9 + 0.4 * fl) + HOT * rimc[..., None] * 0.3
        if mode == 'lift':
            inside = inside * (1 - panel * 0.6)
        glow_src = col * (panel * (0.45 + 0.5 * fl) + rim * 0.6)[..., None]
        bloom = gaussian_filter(glow_src, sigma=(2.6 * u, 2.6 * u, 0)) * 1.8 + gaussian_filter(glow_src, sigma=(0.9 * u, 0.9 * u, 0)) * 0.6
        out[..., :3] = np.minimum(surf, 1.6) * inside[..., None]
        out[..., 3] = inside
        ga = np.clip(bloom.max(-1), 0, 1) * (1 - inside) * 0.85
        out[..., :3] += bloom / np.maximum(bloom.max(-1, keepdims=True), 1e-4) * ga[..., None]
        out[..., 3] += ga
    elif mode == 'receptor_base':
        frame_band = inside * np.clip((d + 3.6 * u) / (0.6 * u), 0, 1)       # lacquered frame
        visor = inside * (1 - np.clip((d + 3.6 * u) / (0.6 * u), 0, 1))       # smoked glass
        rgb = armour * 1.6 + np.array([0.05, 0.05, 0.06])
        rim = np.exp(-((d + 0.4 * u) / (0.35 * u)) ** 2) + np.exp(-((d + 3.6 * u) / (0.3 * u)) ** 2) * 0.7
        rgb = rgb + col * rim[..., None] * 1.1 + HOT * (np.exp(-((d + 0.4 * u) / (0.15 * u)) ** 2))[..., None] * 0.35
        out[..., :3] = rgb * frame_band[..., None] + np.array([0.03, 0.0, 0.005]) * visor[..., None] * 0.55
        out[..., 3] = frame_band + visor * 0.55
    elif mode == 'receptor_flash':      # additive beat flash
        rim = np.exp(-((d + 0.9 * u) / (0.9 * u)) ** 2)
        hot = np.exp(-((d + 0.9 * u) / (0.3 * u)) ** 2)
        e = col[None, None] * rim[..., None] * 1.2 + HOT * hot[..., None] * 0.8
        out = add_to_rgba(e)
    elif mode == 'receptor_press':      # visor ignites
        fill = inside * (0.4 + 0.6 * np.exp(-np.clip(-d, 0, None) / (3.5 * u)))
        e = col[None, None] * fill[..., None] * 1.1 + HOT * (emis_mask * inside)[..., None] * 0.6 + col * (emis_mask * inside)[..., None]
        out = add_to_rgba(e)
    return downsample(out)

def add_to_rgba(e):
    a = np.clip(e.max(-1), 0, 1)
    rgb = e / np.maximum(e.max(-1, keepdims=True), 1e-4)
    return np.concatenate([rgb * a[..., None], a[..., None]], -1)  # premultiplied

def downsample(img, f=SS):
    h, w, c = img.shape
    return img.reshape(h // f, f, w // f, f, c).mean((1, 3))

def save_premul(prem, path):
    a = np.clip(prem[..., 3:4], 0, 1)
    rgb = np.where(a > 1e-4, prem[..., :3] / np.maximum(a, 1e-4), 0)
    out = np.concatenate([np.clip(rgb, 0, 1), a], -1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)
