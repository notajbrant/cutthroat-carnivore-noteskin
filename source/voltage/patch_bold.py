#!/usr/bin/env python3
"""bolder rhythm colour (whole body coloured, pattern = darker tone) + white FX
layers the explosion tints with the column's direction colour"""
p = "gen_voltage.py"
s = open(p).read()

old = '''    over(img, base, inner)
    pm = pattern_mask(PATTERN[min(row, 8)], px, py, d)
    over(img, fill, inner * pm * (0.4 if hollow else 1.0))'''
new = '''    pm = pattern_mask(PATTERN[min(row, 8)], px, py, d)
    over(img, fill, inner * (0.4 if hollow else 1.0))                  # whole body in rhythm colour
    over(img, base, inner * (1 - pm) * P.get("pattern_dark", 0.55))     # pattern = darker tone'''
assert old in s
s = s.replace(old, new)
s = s.replace('name="Pink & Black", gloss=0.1)', 'name="Pink & Black", gloss=0.1, pattern_dark=0.78)')
s = s.replace('name="Black & Red", gloss=0.1)', 'name="Black & Red", gloss=0.1, pattern_dark=0.78)')
s = s.replace('ptop, pbot, base = mix(R["core"], (0, 0, 0), 0.08), mix(R["core"], (0, 0, 0), 0.5), R["bot"]',
              'ptop, pbot, base = R["core"], mix(R["core"], (0, 0, 0), 0.3), R["bot"]')

# white FX layers + arrow-shaped glow burst
s = s.replace("def make_shards(P, out, variant):", '''def fx_arrowglow():
    px, py = grid(64, 64)
    d = arrow_sd(px, py)
    img = blank(64, 64)
    over(img, (1, 1, 1), np.clip(0.95 * np.exp(-np.maximum(d, 0) / 2.6), 0, 1) * (1 - 0.55 * cov(d + 4.0)))
    return img


def make_shards(P, out, variant):''')
s = s.replace('''    save(fx_ring(P), J("_CC FX Ring (res 128x128).png"))''', '''    save(fx_ring(P), J("_CC FX Ring (res 128x128).png"))
    W = dict(P, fx=(1, 1, 1), fx2=(1, 1, 1))
    save(fx_ring(W), J("_CC FX RingW (res 128x128).png"))
    save(fx_star(W, 32, 15, 0.6, 2.6), J("_CC FX TwinkleW (res 32x32).png"))
    save(fx_arrowglow(), J("_CC FX ArrowGlow (res 64x64).png"))''')
open(p, "w").write(s)
print("ok", s.count("pattern_dark"), "fx_arrowglow" in s)
