"""Cutthroat Carnivore noteskin v4 'Inferno' - solid filled arrows in dark forged, coloured
metal (note colour), heavy black outline, sharp facets, hammered/scratched surface, burning
cracks that flare on the beat. Original procedural art.
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter
import arrow_v3 as V3
from arrow_v2 import poly_sdf, seg_dist, downsample, save_premul, add_to_rgba, bez

SS = 4
HOT = np.array([1.0, 0.90, 0.75])
silhouette = V3.silhouette
geometry = V3.geometry
FLASH = [1.0, 0.5, 0.28, 0.18]
BOLT_ON = [1.0, 0.85, 0.0, 0.0]     # bolt lit for the first half of every beat, dark for the second
BOLT = [(0.49, 0.205), (0.605, 0.205), (0.528, 0.43), (0.605, 0.43), (0.43, 0.875), (0.474, 0.545), (0.398, 0.545)]
_BD = {}
def bolt_sdf(n):
    if n not in _BD: _BD[n] = poly_sdf(BOLT, n)
    return _BD[n]

def render(col, frame=0, nframes=4, mode='note', px=128):
    g = geometry(px); n, u, d, N = g['n'], g['u'], g['sdf'], g['N']
    col = np.asarray(col, float)
    fl = FLASH[frame % 4]
    inside = np.clip(0.5 - d, 0, 1)
    out = np.zeros((n, n, 4))
    if mode in ('note', 'lift'):
        nz = N[..., 2]
        Lk = np.array([-0.5, -0.62, 0.6]); Lk /= np.linalg.norm(Lk)
        H = Lk + np.array([0, 0, 1.0]); H /= np.linalg.norm(H)
        diff = np.clip(N @ Lk, 0, 1)
        spec = np.clip(N @ H, 0, 1) ** 22 * 0.35
        Lu = np.array([0.1, 0.9, 0.45]); Lu /= np.linalg.norm(Lu)
        underl = np.clip(N @ Lu, 0, 1) ** 2
        # coloured forged metal: deep, slightly desaturated, darker toward the tail
        grey = col.mean()
        metal_col = (col * 0.85 + grey * 0.15) * 0.48
        tail = np.clip(1.15 - g['ys'] * 1.05, 0.35, 1.0)                # tail end sinks into shadow
        hamm = 1 + 0.14 * g['hammer']
        alb = metal_col * hamm[..., None] * (0.55 + 0.45 * (1 - tail))[..., None]
        wear = np.clip(g['wear'] * 0.7 + g['scr'] * 0.9, 0, 1)
        alb = alb * (1 - wear[..., None]) + (metal_col * 0.6 + 0.22) * wear[..., None]
        rgb = alb * (0.30 + 1.15 * diff[..., None]) + spec[..., None] * np.array([1.0, 0.95, 0.9])
        # dark-chrome reflections: hard light/dark bands broken up by the hammered surface
        nz_ = np.clip(nz, 0, 1)
        R = np.stack([2 * nz_ * N[..., 0], 2 * nz_ * N[..., 1], 2 * nz_ * nz_ - 1], -1)
        band = np.clip(np.sin((R[..., 1] * 5.5 + R[..., 0] * 1.5) * math.pi) * 1.4, 0, 1) ** 2
        fres = 0.25 + 0.75 * (1 - nz_) ** 3
        rgb += (col * 0.55 + 0.25) * (band * fres * 0.38)[..., None]
        rgb += (col * 0.5 + np.array([0.6, 0.05, 0.0]) * 0.5) * underl[..., None] * 0.22
        rgb *= np.clip(1 - g['cav'] * 1.1, 0.15, 1)[..., None]            # soot in the creases
        # burning cracks
        D = g['crackD']; inn = g['inner']
        core = np.exp(-(D / 0.22) ** 2) * inn; glow = np.exp(-(D / 0.55) ** 2) * inn
        heat = np.exp(-(D / 1.6) ** 2) * inn
        k = 0.55
        fl = 0.35   # cracks are steady texture now; the bolt carries the beat
        crack_col = col * 0.5 + np.array([1.0, 0.45, 0.1]) * 0.5         # molten, note-tinted
        rgb = rgb * (1 - np.clip(glow, 0, 1)[..., None] * 0.7) \
            + HOT * (core * (0.7 + 0.6 * fl))[..., None] + crack_col * (glow * 1.0 * k)[..., None] \
            + col * (heat * 0.16 * k)[..., None]
        # heavy black outline + a thin hot inner edge in the note colour
        outline = np.clip(1 - (-d) / (1.15 * u), 0, 1) ** 1.5 * inside
        rgb = rgb * (1 - outline[..., None] * 0.92)
        edge = np.exp(-((d + 1.3 * u) / (0.28 * u)) ** 2) * inside
        rgb += col * edge[..., None] * (0.55 + 0.35 * fl)
        # ---- the beat bolt: snaps ON on the beat, OFF for the back half ----
        on = BOLT_ON[frame % 4] if mode == 'note' else 0.0
        bd = bolt_sdf(n) / u
        bin_ = np.clip(0.5 - bd * 4, 0, 1)                                   # bolt interior (AA)
        bedge = np.exp(-((bd + 0.35) / 0.35) ** 2) * (bd < 0.2)
        # OFF: an engraved, smouldering groove
        rgb = rgb * (1 - bin_[..., None] * 0.75) + col * (bedge * 0.35)[..., None] + np.array([0.08, 0.01, 0.0]) * bin_[..., None]
        if on > 0:
            corew = np.clip(-bd / 0.9, 0, 1)
            lit = HOT * (bin_ * (0.55 + 0.45 * corew))[..., None] * 1.25 + col * (np.exp(-np.clip(bd, 0, None) / 0.9) * (bd > -0.2))[..., None] * 1.3
            rgb = rgb * (1 - on * bin_[..., None]) + lit * on
        if mode == 'lift':
            inside = inside * (1 - np.clip((-d - 4 * u) / u, 0, 1) * 0.65)
        out[..., :3] = np.minimum(rgb, 1.6) * inside[..., None]; out[..., 3] = inside
        # dark shadow halo + tight colour glow so it reads on any background
        shadow = np.clip(gaussian_filter(inside, 2.4 * u) * 1.7, 0, 1) * (1 - inside) * 0.75
        src = col * gaussian_filter(inside, 1.0 * u)[..., None] * (0.25 + 0.35 * (BOLT_ON[frame % 4] if mode == 'note' else 0))
        glow_out = gaussian_filter(src, (1.6 * u, 1.6 * u, 0)) * (1 - inside)[..., None]
        out[..., :3] += glow_out
        out[..., 3] = np.clip(out[..., 3] + shadow + glow_out.max(-1), 0, 1)
    else:
        return V3.render(col, frame, nframes, mode, px)
    return downsample(out)
