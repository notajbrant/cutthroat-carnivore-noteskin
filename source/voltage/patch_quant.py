#!/usr/bin/env python3
"""switch Voltage from beat-cycle colours to rhythm (quantization) colours + face glyphs"""
p = "gen_voltage.py"
s = open(p).read()

# 1) quant table + glyphs
s = s.replace("# ---------------------------------------------------------------- palettes", '''# ---------------------------------------------------------------- rhythm colours
# 4th, 8th, 12th, 16th, 24th, 32nd, 48th, 64th, 192nd. Each value gets its own
# colour AND its own face symbol, so colour-blind players can still read rhythm.
QUANT = [(1.0, 0.16, 0.16), (0.18, 0.45, 1.0), (0.72, 0.28, 1.0), (1.0, 0.88, 0.1),
         (1.0, 0.36, 0.76), (1.0, 0.55, 0.05), (0.1, 0.9, 0.95), (0.2, 0.9, 0.32), (0.72, 0.72, 0.75)]
GLYPH = ["bolt", "diamond", "triangle", "circle", "tri_hollow", "ring", "dia_hollow", "ring_small", "dot"]


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


# ---------------------------------------------------------------- palettes''')

# 2) palettes: rows per rhythm value
s = s.replace('''        rows = []
        for i in range(12):
            h = (i / 12.0) % 1.0
            rows.append(dict(top=hsv(h, 0.42, 1.0), bot=hsv(h, 1.0, 0.88), rim=(1, 1, 1),
                             hair=hsv(h, 1.0, 0.42), glow=hsv(h, 0.85, 1.0)))''',
'''        rows = [dict(top=mix(q, (1, 1, 1), 0.5), bot=mix(q, (0, 0, 0), 0.12), rim=(1, 1, 1),
                     hair=mix(q, (0, 0, 0), 0.55), glow=q, core=(1, 1, 1), tint=0.0) for q in QUANT]''')
s = s.replace('''        return dict(rows=[row] * 12, outline=(0.0, 0.0, 0.0), bolt_core=(1, 0.92, 0.98),''',
'''        return dict(rows=[dict(row, hair=q, core=q, tint=0.22) for q in QUANT], outline=(0.0, 0.0, 0.0), bolt_core=(1, 0.92, 0.98),''')
s = s.replace('''    return dict(rows=[row] * 12, outline=(0.0, 0.0, 0.0), bolt_core=(1, 0.94, 0.88),''',
'''    return dict(rows=[dict(row, hair=q, core=q, tint=0.22) for q in QUANT], outline=(0.0, 0.0, 0.0), bolt_core=(1, 0.94, 0.88),''')

# 3) face: rhythm glyph in the rhythm colour, flashing on the beat
s = s.replace('''    db = bolt_sd(px, py, 32, 35, 0.78)
    over(img, P["bolt_glow"], inner * (0.18 + 0.82 * I) * np.exp(-np.maximum(db, 0) / 2.4) * 0.9)
    over(img, P["outline"], inner * cov(db - 0.8) * 0.55)               # keyline
    over(img, mix(P["bolt_glow"], P["bolt_core"], 0.35 + 0.65 * I), inner * cov(db) * (0.55 + 0.45 * I))''',
'''    if R.get("tint"):  # dark skins: the face glows in the rhythm colour
        over(img, R["core"], inner * R["tint"] * (1 - sstep(4, 60, py) * 0.6))
    gcol = R["glow"] if P["name"] == "Color" else R["core"]
    db = glyph_sd(GLYPH[min(row, 8)], px, py)
    over(img, gcol, inner * (0.25 + 0.75 * I) * np.exp(-np.maximum(db, 0) / 2.4) * 0.9)
    over(img, P["outline"], inner * cov(db - 0.9) * 0.6)                # keyline
    core = (1, 1, 1) if P["name"] == "Color" else R["core"]
    over(img, mix(core, (1, 1, 1), 0.25 + 0.55 * I), inner * cov(db))''')

# 4) sheet rows = rhythm values
s = s.replace("frames.append(tap_frame(P, r % 12, f, hollow))", "frames.append(tap_frame(P, min(r, 8), f, hollow))")
s = s.replace("rows=[crystal] * 12", "rows=[crystal] * 9")
open(p, "w").write(s)
print("glyph_sd" in s, s.count("for q in QUANT"), "min(r, 8)" in s)
