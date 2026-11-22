#!/usr/bin/env python3
"""colour-blind-proof rhythm coding: every note value also gets its own fill pattern"""
p = "gen_voltage.py"
s = open(p).read()

s = s.replace('''def glyph_sd(kind, px, py, cx=32, cy=35):''', '''# Fill pattern per rhythm value - readable with no colour vision at all:
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


def glyph_sd(kind, px, py, cx=32, cy=35):''')

old_start = '    t = sstep(6, 58, py)[..., None]\n    fill = np.asarray(R["top"], np.float32) * (1 - t) + np.asarray(R["bot"], np.float32) * t\n'
old_end = '        over(img, R["core"], inner * R["tint"] * (1 - sstep(4, 60, py) * 0.6))\n'
a = s.index(old_start)
b = s.index(old_end) + len(old_end)
s = s[:a] + '''    t = sstep(6, 58, py)[..., None]
    inner = cov(d + 2.6)
    if P["name"] == "Color":
        ptop, pbot, base = R["top"], R["bot"], (0.07, 0.07, 0.09)
    else:
        ptop, pbot, base = mix(R["core"], (0, 0, 0), 0.08), mix(R["core"], (0, 0, 0), 0.5), R["bot"]
    fill = np.asarray(ptop, np.float32) * (1 - t) + np.asarray(pbot, np.float32) * t
    over(img, base, inner)
    pm = pattern_mask(PATTERN[min(row, 8)], px, py, d)
    over(img, fill, inner * pm * (0.4 if hollow else 1.0))
    over(img, (0, 0, 0), 0.32 * inner * sstep(-6.0, -2.6, d))          # bevel shadow
    over(img, (1, 1, 1), cov(d + 3.4) * (1 - sstep(9, 30, py)) * P.get("gloss", 0.3) * pm)   # gloss
''' + s[b:]
s = s.replace('core = (1, 1, 1) if P["name"] == "Color" else R["core"]',
              'core = (1, 1, 1) if P["name"] == "Color" else mix(R["core"], (1, 1, 1), 0.55)')
open(p, "w").write(s)
print("pattern_mask" in s, s.count("pm = pattern_mask"))
