"""Cutthroat Carnivore noteskin - original procedural art generator.
All artwork is generated from scratch (signed distance fields + procedural noise).
Usage: python3 gen_art.py <outdir>
"""
import sys, os, math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt, zoom as ndzoom
from matplotlib.path import Path

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(66613)

SS = 4            # supersample factor
PX = 2            # output pixels per noteskin unit (2x = crisp "doubleres")

# ---------- colour ----------
def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) / 255 for i in (0, 2, 4)])

CRIMSON = hexc('ff1428'); BLOOD = hexc('5a0008'); HOT = hexc('fff0f0')
QUANT = [  # ITG-readable quantization colours, tuned for the brand
    ('4th',   'ff1a2e'), ('8th',  '2a7bff'), ('12th', 'a63cff'), ('16th', 'ffcc1a'),
    ('24th',  'ff3cb4'), ('32nd', 'ff7a12'), ('48th', '1ee6ff'), ('64th', '3cff62'),
    ('192nd', 'c8ccd8'),
]
def cycle_palette(n=12):
    import colorsys
    return [np.array(colorsys.hsv_to_rgb(((i / n) * 0.92) % 1.0, 0.92, 1.0)) for i in range(n)]

# ---------- geometry ----------
def poly_sdf(pts, size):
    """Signed distance (in pixels of `size` grid) to polygon given in 0..1 coords. Negative inside."""
    h, w = size
    ys, xs = np.mgrid[0:h, 0:w]
    P = np.stack([(xs + 0.5) / w, (ys + 0.5) / h], -1).reshape(-1, 2)
    pts = np.asarray(pts, float)
    inside = Path(pts).contains_points(P).reshape(h, w)
    d = np.full(P.shape[0], np.inf)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        q = a + t[:, None] * ab
        d = np.minimum(d, np.hypot(*(P - q).T))
    d = d.reshape(h, w) * w
    return np.where(inside, -d, d)

def polyline_dist(pts, size, closed=False):
    h, w = size
    ys, xs = np.mgrid[0:h, 0:w]
    P = np.stack([(xs + 0.5) / w, (ys + 0.5) / h], -1).reshape(-1, 2)
    pts = np.asarray(pts, float); d = np.full(P.shape[0], np.inf)
    n = len(pts) if closed else len(pts) - 1
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        ab = b - a; t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(*(P - (a + t[:, None] * ab)).T))
    return d.reshape(h, w) * w

# Down-pointing armoured blade arrow, with cowl "ears" notched into the stem top.
ARROW = [(0.50, 0.955), (0.955, 0.505), (0.825, 0.375), (0.625, 0.575), (0.625, 0.075),
         (0.555, 0.135), (0.50, 0.095), (0.445, 0.135), (0.375, 0.075), (0.375, 0.575),
         (0.175, 0.375), (0.045, 0.505)]
CORE_V = [(0.215, 0.505), (0.50, 0.79), (0.785, 0.505)]      # energy chevron along the wings
CORE_S = [(0.50, 0.24), (0.50, 0.60)]                        # energy slit down the stem

# ---------- image helpers ----------
def blur(a, s): return gaussian_filter(a, s) if s > 0 else a
def down(img, f=SS):
    h, w, c = img.shape
    return img.reshape(h // f, f, w // f, f, c).mean((1, 3))

def save_premul(prem, path):
    """prem: HxWx4 premultiplied float -> straight-alpha PNG."""
    a = np.clip(prem[..., 3:4], 0, 1)
    rgb = np.where(a > 1e-4, prem[..., :3] / np.maximum(a, 1e-4), 0)
    out = np.concatenate([np.clip(rgb, 0, 1), a], -1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)

def save_additive(emis, path):
    """emis: HxWx3 emitted light for BlendMode_Add sprites."""
    e = np.clip(emis, 0, None)
    a = np.clip(e.max(-1, keepdims=True), 0, 1)
    rgb = np.where(a > 1e-4, np.clip(e / np.maximum(a, 1e-4), 0, 1), 0)
    out = np.concatenate([rgb, a], -1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)

def over(dst, rgb, alpha):
    """Composite straight rgb/alpha layer over premultiplied dst."""
    a = np.clip(alpha, 0, 1)[..., None]
    dst[..., :3] = rgb * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)

def add_light(dst, rgb, k):
    k = np.clip(k, 0, None)[..., None]
    dst[..., :3] += rgb * k
    dst[..., 3:4] = np.clip(dst[..., 3:4] + k * 0.9, 0, 1)

def fbm(h, w, seed, octaves=4, period=None):
    r = np.random.default_rng(seed); acc = np.zeros((h, w)); amp = 1; tot = 0
    for o in range(octaves):
        cell = max(2, int(min(h, w) / (4 * 2 ** o)))
        gh, gw = h // cell + 2, w // cell + 2
        g = r.random((gh, gw))
        if period:  # wrap vertically for tiling textures
            g[-2:] = g[:2]
        up = ndzoom(g, (h / (gh - 1) * 1.0001, w / (gw - 1) * 1.0001), order=3)[:h, :w]
        acc += up * amp; tot += amp; amp *= 0.5
    return acc / tot

# ---------- the arrow ----------
GEO = {}
def arrow_geometry(units=64):
    key = units
    if key in GEO: return GEO[key]
    n = units * PX * SS
    sdf = poly_sdf(ARROW, (n, n))
    u = n / units                                  # px per unit (supersampled)
    gy, gx = np.gradient(sdf)
    nrm = np.hypot(gx, gy) + 1e-6; nx, ny = gx / nrm, gy / nrm
    corev = polyline_dist(CORE_V, (n, n)); cores = polyline_dist(CORE_S, (n, n))
    ys, xs = np.mgrid[0:n, 0:n] / n
    GEO[key] = dict(n=n, u=u, sdf=sdf, nx=nx, ny=ny, corev=corev, cores=cores, xs=xs, ys=ys)
    return GEO[key]

def render_arrow(col, frame, nframes=4, hollow=False, units=64):
    g = arrow_geometry(units); n, u, d = g['n'], g['u'], g['sdf']
    col = np.asarray(col, float)
    img = np.zeros((n, n, 4))
    phase = frame / nframes
    pulse = 0.78 + 0.22 * math.cos(phase * 2 * math.pi)
    # outer energy aura (kept tight so it never bleeds into neighbouring frames)
    aura = np.exp(-np.clip(d, 0, None) / (1.6 * u)) * (d > 0) * (0.55 + 0.25 * pulse)
    over(img, col * 0.9 + 0.1, aura * 0.85)
    inside = d <= 0
    # obsidian armour body with a cold top-left key light
    L = np.array([-0.62, -0.78])
    shade = -(g['nx'] * L[0] + g['ny'] * L[1])
    depth = np.clip(-d / (4.2 * u), 0, 1)
    base = np.stack([0.07 + 0.07 * (1 - g['ys'])] * 3, -1) * np.array([1.0, 0.97, 1.06])
    bevel = (1 - depth)[..., None] * np.clip(shade, -1, 1)[..., None] * 0.42 + (1 - depth)[..., None] * 0.10
    body = base + bevel * np.array([0.85, 0.85, 0.95]) + col * 0.10 * (1 - depth)[..., None]
    # armour seam (panel line) and a faint inner highlight
    seam = np.exp(-((-d - 6.2 * u) / (0.45 * u)) ** 2)
    body = body * (1 - 0.65 * seam[..., None]) + np.exp(-((-d - 7.0 * u) / (0.4 * u)) ** 2)[..., None] * 0.06
    # glossy helmet sheen (top-left)
    sheen = np.exp(-(((g['xs'] - 0.33) ** 2 + (g['ys'] - 0.30) ** 2) / 0.012)) * 0.10
    body = body + sheen[..., None]
    if hollow:
        body = body * (depth < 0.55)[..., None]
        bodya = inside * np.where(depth < 0.55, 1.0, 0.25)
    else:
        bodya = inside * 1.0
    over(img, np.clip(body, 0, 1), bodya)
    # energy rim: lightsaber edge, white-hot centre into the colour
    rimd = np.abs(d + 0.75 * u)
    rim = np.exp(-(rimd / (0.7 * u)) ** 2) * (d < 0.6 * u)
    hot = np.exp(-(rimd / (0.28 * u)) ** 2)
    add_light(img, col, rim * (1.05 + 0.25 * pulse))
    add_light(img, HOT, hot * 0.55 * inside)
    if not hollow:
        # reactor core: chevron + stem slit, flickering with the beat
        flick = 0.85 + 0.15 * math.sin(phase * 6 * math.pi + 1.3)
        cd = g['corev']
        coreg = np.exp(-(cd / (1.35 * u)) ** 2) * inside * (np.clip(-d, 0, None) > 2.6 * u)
        corew = np.exp(-(cd / (0.42 * u)) ** 2) * inside * (np.clip(-d, 0, None) > 2.6 * u)
        add_light(img, col, coreg * 1.25 * pulse * flick)
        add_light(img, HOT, corew * 0.9 * pulse * flick)
    return down(img)

def build_note_sheet(palette, path, rows=16, hollow=False):
    fr = 64 * PX; sheet = np.zeros((rows * fr, 4 * fr, 4))
    for r, c in enumerate(palette):
        for f in range(4):
            sheet[r * fr:(r + 1) * fr, f * fr:(f + 1) * fr] = render_arrow(c, f, hollow=hollow)
    save_premul(sheet, path)

# ---------- receptor ----------
def build_receptor(path):
    g = arrow_geometry(); n, u, d = g['n'], g['u'], g['sdf']
    frames = []
    # 0: base - gunmetal frame, dark see-through visor, thin crimson edge
    img = np.zeros((n, n, 4))
    frame_band = (d <= 0) & (d > -3.4 * u)
    L = np.array([-0.62, -0.78]); shade = -(g['nx'] * L[0] + g['ny'] * L[1])
    metal = 0.20 + 0.16 * np.clip(shade, -1, 1)
    over(img, np.stack([metal * 0.95, metal * 0.95, metal * 1.05], -1), frame_band * 1.0)
    over(img, np.array([0.02, 0.0, 0.01]), ((d <= -3.4 * u) * 0.42))
    edge = np.exp(-((d + 0.5 * u) / (0.45 * u)) ** 2) + np.exp(-((d + 3.3 * u) / (0.35 * u)) ** 2) * 0.6
    add_light(img, CRIMSON, edge * 0.75)
    frames.append(down(img))
    # 1: beat flash - white-hot rim only
    img = np.zeros((n, n, 4))
    fl = np.exp(-((d + 1.2 * u) / (1.3 * u)) ** 2)
    add_light(img, CRIMSON * 0.6 + 0.4, fl * 1.2)
    add_light(img, HOT, np.exp(-((d + 1.2 * u) / (0.45 * u)) ** 2) * 0.8)
    frames.append(down(img))
    # 2: press - visor floods with red energy
    img = np.zeros((n, n, 4))
    fill = (d <= 0) * (0.35 + 0.65 * np.exp(-np.clip(-d, 0, None) / (4 * u)))
    over(img, CRIMSON, fill * 0.85)
    add_light(img, HOT, np.exp(-((d + 1.0 * u) / (0.6 * u)) ** 2) * 0.9)
    frames.append(down(img))
    save_premul(np.concatenate(frames, 1), path)

def build_aura(path, nframes=8, units=112):
    """Ki aura: jagged energy spikes bursting off the receptor silhouette (additive)."""
    n = units * PX * SS // 2
    sc = 64 / units; off = (1 - sc) / 2
    pts = [(off + x * sc, off + y * sc) for x, y in ARROW]
    sdf = poly_sdf(pts, (n, n)); u = n / units
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / u - units / 2
    th = np.arctan2(ys, xs)
    up = np.clip(-np.sin(th), 0, 1)              # 1 = pointing up the screen
    frames = []
    for f in range(nframes):
        t = f / nframes * 2 * math.pi
        spikes = np.zeros_like(th)
        for k, amp in [(7, 0.5), (13, 0.32), (23, 0.18)]:
            ph = rng.random() * 6.28
            spikes += amp * (0.5 + 0.5 * np.cos(k * th + ph + t * (1 + k / 9)))
        spikes = spikes ** 2.2
        reach = (2.5 + 15 * spikes * (0.45 + 0.75 * up)) * u
        flame = np.exp(-np.clip(sdf, 0, None) / reach) * (sdf > -1.0 * u)
        flame *= np.clip(1 - np.clip(sdf, 0, None) / (26 * u), 0, 1)
        halo = np.exp(-np.clip(sdf + 0.4 * u, 0, None) / (2.0 * u))
        emis = (CRIMSON[None, None] * flame[..., None] * 1.15 + HOT[None, None] * (flame ** 4)[..., None] * 0.7
                + CRIMSON[None, None] * halo[..., None] * 0.4)
        frames.append(down(emis, SS // 2))
    save_additive(np.concatenate(frames, 1), path)

# ---------- holds / rolls ----------
def hold_body(kind, active, units_h=64):
    W = 64 * PX * SS; H = units_h * PX * SS; u = W / 64
    xs = (np.arange(W) + 0.5) / u - 32           # -32..32 units
    X = np.tile(xs, (H, 1)); Y = np.tile(((np.arange(H) + 0.5) / u)[:, None], (1, W))
    img = np.zeros((H, W, 4))
    half = 23
    chan = np.abs(X) <= half
    rail = (np.abs(X) > half - 4.5) & chan
    # dark channel
    over(img, np.array([0.03, 0.02, 0.025]), chan * 0.78)
    # gunmetal rails with bevel
    rs = 0.18 + 0.14 * np.cos((np.abs(X) - (half - 2.25)) / 2.25 * math.pi / 2)
    over(img, np.stack([rs, rs * 0.98, rs * 1.06], -1), rail * 1.0)
    edge = np.exp(-((np.abs(X) - (half - 4.6)) / 0.45) ** 2)
    if kind == 'hold':
        col = CRIMSON if active else np.array([0.55, 0.55, 0.6])
        nz = fbm(H, W, 7, period=True)
        beam = np.exp(-(X / (7.5 + 2.5 * nz)) ** 2)
        line = np.exp(-(X / 1.2) ** 2)
        add_light(img, col, beam * (1.0 if active else 0.45))
        add_light(img, HOT if active else np.array([0.8, 0.8, 0.85]), line * (0.85 if active else 0.3))
        add_light(img, col, edge * (0.6 if active else 0.25))
    else:  # roll: electric zig-zag bolt, gold-hot, tiles every 32 units
        col = np.array([1.0, 0.72, 0.08]) if active else np.array([0.6, 0.55, 0.45])
        period = 32.0
        tri = 2 * np.abs((Y / period) % 1 - 0.5)          # 0..1 triangle wave
        zx = (tri - 0.5) * 2 * 12.0
        dd = np.abs(X - zx)
        bolt = np.exp(-(dd / 2.6) ** 2); boltw = np.exp(-(dd / 0.9) ** 2)
        add_light(img, CRIMSON if active else col * 0.6, np.exp(-(dd / 6.5) ** 2) * (0.7 if active else 0.3))
        add_light(img, col, bolt * (1.1 if active else 0.45))
        add_light(img, HOT, boltw * (0.9 if active else 0.25))
        add_light(img, col, edge * (0.5 if active else 0.2))
    return img, X, Y, u

def build_hold_parts(outdir, kind):
    K = 'Hold' if kind == 'hold' else 'Roll'
    for active in (True, False):
        st = 'Active' if active else 'Inactive'
        body, X, Y, u = hold_body(kind, active)
        save_premul(down(body), f'{outdir}/Down {K} Body {st} (res 64x64).png')
        # bottom cap: channel tapers to a blade point, 32 units tall
        cap, X2, Y2, _ = hold_body(kind, active, units_h=32)
        taper = 23 * (1 - Y2 / 32) ** 0.9 + 0.5
        mask = (np.abs(X2) <= taper).astype(float)
        mask = blur(mask, 0.8 * u)
        cap[..., :4] *= mask[..., None]
        tipglow = np.exp(-((X2 / 3.0) ** 2 + ((Y2 - 22) / 6.0) ** 2))
        add_light(cap, (CRIMSON if kind == 'hold' else np.array([1, .72, .08])) * (1 if active else 0.4), tipglow * 0.8)
        save_premul(down(cap), f'{outdir}/Down {K} BottomCap {st} (res 64x32).png')
        save_premul(down(cap[::-1].copy()), f'{outdir}/Down {K} TopCap {st} (res 64x32).png')

# ---------- mine ----------
def build_mine(outdir):
    n = 64 * PX * SS; u = n / 64
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / u - 32
    r = np.hypot(xs, ys); ang = np.arctan2(ys, xs)
    # base: black armoured orb with crimson fractures
    img = np.zeros((n, n, 4))
    orb = r < 17
    sh = np.clip(1 - np.hypot(xs + 6, ys + 6) / 26, 0, 1)
    over(img, np.stack([0.05 + 0.22 * sh] * 3, -1) * np.array([1, 0.95, 1.05]), orb * 1.0)
    crack = np.zeros((n, n))
    for k in range(7):
        a0 = k / 7 * 2 * math.pi + rng.random() * 0.4
        pts = [(0.5, 0.5)]; rr = 0
        aa = a0
        while rr < 16:
            rr += 3 + rng.random() * 3; aa += (rng.random() - 0.5) * 0.9
            pts.append((0.5 + rr * math.cos(aa) / 64, 0.5 + rr * math.sin(aa) / 64))
        crack = np.maximum(crack, np.exp(-(polyline_dist(pts, (n, n)) / (0.7 * u)) ** 2))
    add_light(img, CRIMSON, crack * orb * 1.2)
    add_light(img, HOT, np.exp(-(r / 3.5) ** 2) * 0.9)
    save_premul(down(img), f'{outdir}/_CC Mine Base (res 64x64).png')
    # spokes: eight hooked blades
    img = np.zeros((n, n, 4))
    bl = np.zeros((n, n))
    for k in range(8):
        a = k / 8 * 2 * math.pi
        rel = (ang - a + math.pi) % (2 * math.pi) - math.pi
        w = 0.32 * np.clip(1 - (r - 15) / 14, 0, 1) - rel * 0.15
        bl = np.maximum(bl, ((np.abs(rel - 0.1) < w) & (r > 15) & (r < 30)).astype(float))
    bl = blur(bl, 0.5 * u)
    over(img, np.array([0.16, 0.15, 0.18]), bl)
    add_light(img, CRIMSON, blur(bl, 1.2 * u) * 0.35)
    save_premul(down(img), f'{outdir}/_CC Mine Spokes (res 64x64).png')
    # glow: additive red heartbeat
    em = CRIMSON[None, None] * np.exp(-(r / 13) ** 2)[..., None] * 1.2
    save_additive(down(em), f'{outdir}/_CC Mine Glow (res 64x64).png')

# ---------- explosion FX (additive) ----------
def fx_grid(units, ss=SS):
    n = units * PX * ss; u = n / units
    ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / u - units / 2
    return n, u, xs, ys, np.hypot(xs, ys), np.arctan2(ys, xs)

def build_fx(outdir):
    # core flash: white-hot centre, crimson corona
    n, u, xs, ys, r, a = fx_grid(128, 2)
    em = HOT[None, None] * np.exp(-(r / 9) ** 2)[..., None] * 1.3 + CRIMSON[None, None] * np.exp(-(r / 26) ** 2)[..., None] * 0.9
    save_additive(down(em, 2), f'{outdir}/_CC FX Flash (res 128x128).png')
    # shockwave ring (white; tinted per judgment in Lua)
    ring = np.exp(-((r - 52) / 2.2) ** 2) + 0.35 * np.exp(-((r - 49) / 6) ** 2)
    save_additive(down(np.repeat(ring[..., None], 3, -1), 2), f'{outdir}/_CC FX Ring (res 128x128).png')
    # ki-burst rays
    rays = np.zeros_like(r)
    for k in range(18):
        th = k / 18 * 2 * math.pi + rng.random() * 0.2; ln = 38 + rng.random() * 24; wd = 0.05 + rng.random() * 0.05
        rel = np.abs((a - th + math.pi) % (2 * math.pi) - math.pi)
        rays = np.maximum(rays, np.exp(-(rel / (wd * np.clip(1 - r / ln, 0.05, 1))) ** 2) * np.clip(1 - r / ln, 0, 1))
    em = CRIMSON[None, None] * rays[..., None] * 1.1 + HOT[None, None] * (rays ** 4)[..., None]
    save_additive(down(em, 2), f'{outdir}/_CC FX Rays (res 128x128).png')
    # spark streak and ember
    n2 = 32 * PX * SS; u2 = n2 / 32
    ys2, xs2 = (np.mgrid[0:n2 // 4, 0:n2] + 0.5) / u2 - np.array([4, 16])[:, None, None]
    st = np.exp(-((xs2 / 14) ** 2 + (ys2 / 1.6) ** 2))
    em = CRIMSON[None, None] * st[..., None] * 1.2 + HOT[None, None] * (st ** 6)[..., None]
    save_additive(down(em), f'{outdir}/_CC FX Spark (res 32x8).png')
    n3 = 16 * PX * SS; u3 = n3 / 16
    ys3, xs3 = (np.mgrid[0:n3, 0:n3] + 0.5) / u3 - 8
    eb = np.exp(-(np.hypot(xs3, ys3) / 3.2) ** 2)
    em = np.array([1.0, 0.35, 0.12])[None, None] * eb[..., None] + HOT[None, None] * (eb ** 5)[..., None]
    save_additive(down(em), f'{outdir}/_CC FX Ember (res 16x16).png')

def lightning_bolt(start, angle, length, rough, depth, segs, out):
    pts = [start]; x, y = start; step = length / segs
    for i in range(segs):
        angle += rng.normal(0, rough); x += math.cos(angle) * step; y += math.sin(angle) * step
        pts.append((x, y))
        if depth > 0 and rng.random() < 0.28:
            lightning_bolt((x, y), angle + rng.choice([-1, 1]) * (0.5 + rng.random() * 0.6),
                           length * (0.25 + rng.random() * 0.3), rough * 1.1, depth - 1, max(3, segs // 2), out)
    out.append((pts, depth))

def build_lightning(outdir, nframes=8, units=128, radial=True, name='_CC FX Lightning'):
    ss = 2; n = units * PX * ss; u = n / units
    frames = []
    for f in range(nframes):
        bolts = []
        nb = 4 + int(rng.integers(0, 3))
        for b in range(nb):
            ang = rng.random() * 2 * math.pi
            if radial:
                lightning_bolt((0.5, 0.5), ang, (34 + rng.random() * 26) / units, 0.45, 2, 12, bolts)
            else:  # arcs hugging a 16-unit orb
                r0 = 15 / units; a0 = ang
                start = (0.5 + r0 * math.cos(a0), 0.5 + r0 * math.sin(a0))
                lightning_bolt(start, a0 + math.pi / 2 * rng.choice([-1, 1]), (16 + rng.random() * 14) / units, 0.7, 1, 8, bolts)
        glow = np.zeros((n, n)); core = np.zeros((n, n))
        for pts, depth in bolts:
            d = polyline_dist(pts, (n, n)) / u
            wgt = 1.0 if depth >= 2 else 0.7
            glow = np.maximum(glow, np.exp(-(d / 2.4) ** 2) * wgt)
            core = np.maximum(core, np.exp(-(d / 0.55) ** 2) * wgt)
        em = CRIMSON[None, None] * glow[..., None] * 1.15 + HOT[None, None] * core[..., None]
        if not radial:
            ys, xs = (np.mgrid[0:n, 0:n] + 0.5) / u - units / 2
            rr = np.hypot(xs, ys)
            em += CRIMSON[None, None] * np.exp(-(rr / 14) ** 2)[..., None] * 0.9 + HOT[None, None] * np.exp(-(rr / 6) ** 2)[..., None] * 0.8
        frames.append(down(em, ss))
    save_additive(np.concatenate(frames, 1), f'{outdir}/{name} {nframes}x1 (res {units * nframes}x{units}).png')

def build_mine_blast(outdir):
    n, u, xs, ys, r, a = fx_grid(128, 2)
    em = CRIMSON[None, None] * (np.exp(-((r - 30) / 8) ** 2) + np.exp(-(r / 12) ** 2) * 0.8)[..., None] \
        + HOT[None, None] * np.exp(-(r / 5) ** 2)[..., None]
    save_additive(down(em, 2), f'{outdir}/_CC FX MineBlast (res 128x128).png')

if __name__ == '__main__':
    which = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if which in ('all', 'notes'):
        quant = [hexc(h) for _, h in QUANT]
        build_note_sheet(quant, f'{OUT}/_CC Tap Note Quant 4x16 (res 256x1024).png')
        build_note_sheet(cycle_palette(), f'{OUT}/_CC Tap Note Cycle 4x16 (res 256x1024).png')
        build_note_sheet(quant, f'{OUT}/_CC Tap Lift Quant 4x16 (res 256x1024).png', hollow=True)
        build_note_sheet(cycle_palette(), f'{OUT}/_CC Tap Lift Cycle 4x16 (res 256x1024).png', hollow=True)
    if which in ('all', 'rest'):
        build_receptor(f'{OUT}/_CC Receptor 3x1 (res 192x64).png')
        build_aura(f'{OUT}/_CC Receptor Aura 8x1 (res 896x112).png')
        build_hold_parts(OUT, 'hold'); build_hold_parts(OUT, 'roll')
        build_mine(OUT); build_fx(OUT); build_mine_blast(OUT)
        build_lightning(OUT)
        build_lightning(OUT, units=64, radial=False, name='_CC FX HoldOrb')
    print('done')
