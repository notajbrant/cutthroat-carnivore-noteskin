"""Hyper-beam holds (Kamehameha / MvC style): white-hot core, crimson energy, energy rings
rushing down the beam (4 frames per beat), plus gold helix-lightning rolls. Original art.
Usage: python3 beam_v4.py <outdir>
"""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from arrow_v2 import downsample, save_premul

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
PPU, SS = 2, 4
HOT = np.array([1.0, 0.96, 0.92])

def to_rgba(e):
    e = np.clip(e, 0, None)
    a = np.clip(e.max(-1), 0, 1)
    return np.concatenate([np.minimum(e, a[..., None]), a[..., None]], -1)   # premultiplied

def grid(h_units):
    W = 64 * PPU * SS; H = h_units * PPU * SS; u = W / 64
    X = np.tile((np.arange(W) + .5) / u - 32, (H, 1)); Y = np.tile(((np.arange(H) + .5) / u)[:, None], (1, W))
    return X, Y

def ring_layer(X, Y, yc, a=26.0, b=5.0, w=0.085):
    e = np.sqrt((X / a) ** 2 + ((Y - yc) / b) ** 2)
    line = np.exp(-((e - 1) / w) ** 2)
    front = (Y >= yc).astype(float) * 0.65 + 0.35          # near side of the ring brighter
    return line * front

def beam_frame(kind, f, active, h_units=64, period=32.0):
    X, Y = grid(h_units)
    shift = f * period / 4                                  # rings advance a quarter period per frame
    wob = 1 + 0.10 * np.sin((Y + shift * 2) / h_units * 2 * math.pi * 2) + 0.05 * np.sin((Y - shift) / h_units * 2 * math.pi * 5 + 1)
    if kind == 'hold':
        core_c, mid_c, aura_c = HOT, np.array([1.0, 0.22, 0.16]), np.array([0.55, 0.0, 0.04])
    else:
        core_c, mid_c, aura_c = HOT, np.array([1.0, 0.72, 0.12]), np.array([0.6, 0.12, 0.0])
    ax = np.abs(X)
    e = (core_c * np.exp(-(ax / (5.0 * wob)) ** 2)[..., None] * 1.5
         + mid_c * np.exp(-(ax / (13.5 * wob)) ** 2)[..., None] * 1.1
         + aura_c * np.exp(-(ax / (22 * wob)) ** 2)[..., None] * 1.0)
    # flowing streaks along the beam
    streak = 0.5 + 0.5 * np.sin(X * 1.9) * np.sin((Y - shift * 2) / h_units * 2 * math.pi * 3 + X * 0.4)
    e += mid_c * (np.exp(-(ax / 11) ** 2) * streak ** 6 * 0.6)[..., None]
    if kind == 'roll':      # gold double-helix lightning twisting round the core
        for ph in (0, math.pi):
            hx = 10 * np.sin((Y - shift * 2) / period * 2 * math.pi + ph)
            dd = np.abs(X - hx)
            depth = 0.6 + 0.4 * np.cos((Y - shift * 2) / period * 2 * math.pi + ph)
            e += (HOT * np.exp(-(dd / 0.7) ** 2)[..., None] * 1.1 + mid_c * np.exp(-(dd / 2.2) ** 2)[..., None]) * depth[..., None]
    if active:
        rings = np.zeros_like(X)
        for k in range(-1, int(h_units / period) + 2):
            rings = np.maximum(rings, ring_layer(X, Y, k * period + shift))
        e += (HOT * 0.7 + mid_c * 0.5) * rings[..., None] * 1.3
    else:
        g = e.mean(-1, keepdims=True); e = (e * 0.25 + g * 0.75) * 0.35
    return e

def build(kind):
    K = 'Hold' if kind == 'hold' else 'Roll'
    for active in (True, False):
        st = 'Active' if active else 'Inactive'
        frames = [downsample(to_rgba(beam_frame(kind, f, active)), SS) for f in range(4)]
        save_premul(np.concatenate(frames, 1), f'{OUT}/Down {K} Body {st} 4x1 (res 256x64).png')
        # bottom cap: the beam's leading end - tapers to a blazing point
        X, Y = grid(32)
        e = beam_frame(kind, 0, active, h_units=32)
        taper = np.clip(1 - (Y / 30) ** 1.4, 0, 1)
        m = np.clip((taper * 26 + 1 - np.abs(X)) / 3, 0, 1)
        e = e * m[..., None]
        flare = np.exp(-((X / 6) ** 2 + ((Y - 22) / 7) ** 2))
        e += HOT * flare[..., None] * (0.9 if active else 0.3)
        cap = downsample(to_rgba(e), SS)
        save_premul(cap, f'{OUT}/Down {K} BottomCap {st} (res 64x32).png')
        save_premul(cap[::-1].copy(), f'{OUT}/Down {K} TopCap {st} (res 64x32).png')

if __name__ == '__main__':
    build('hold'); build('roll'); print('beams done')
