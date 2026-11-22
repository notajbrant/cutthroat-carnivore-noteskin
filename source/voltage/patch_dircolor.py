#!/usr/bin/env python3
"""direction colours: a separate rim+halo layer that the Lua tints per column"""
p = "gen_voltage.py"
s = open(p).read()

# notes: no baked halo (the rim layer brings a direction-coloured one)
s = s.replace("frames.append(tap_frame(P, min(r, 8), f, hollow))",
              "frames.append(tap_frame(P, min(r, 8), f, hollow, glow=False))")

# rim layer sheet (white, tinted in Lua), same 4x16 layout as the notes
s = s.replace("def receptor_sheet(P):", '''def rim_frame():
    px, py = grid(64, 64)
    d = arrow_sd(px, py)
    img = blank(64, 64)
    over(img, (1, 1, 1), 0.55 * np.exp(-np.maximum(d - 2.6, 0) / 2.2) * sstep(2.2, 3.0, d))  # halo
    over(img, (1, 1, 1), cov(d) * (1 - cov(d + 2.3)))                                      # thick rim
    return img


def rim_sheet():
    f = rim_frame()
    return sheet([f] * 64, 4, 16)


def receptor_sheet(P):''')

# receptor frame rim drawn light so the Lua can tint it by direction
s = s.replace('''    over(f0, P["rec_rim"], cov(d))
    over(f0, P["outline"], cov(d + 1.6))''', '''    over(f0, (0.92, 0.92, 0.94), cov(d))
    over(f0, P["outline"], cov(d + 1.9))''')

s = s.replace('''    save(note_sheet(P, hollow=True), J("_CC Tap Lift 4x16 (res 256x1024).png"))''',
'''    save(note_sheet(P, hollow=True), J("_CC Tap Lift 4x16 (res 256x1024).png"))
    save(rim_sheet(), J("_CC Tap Rim 4x16 (res 256x1024).png"))''')
open(p, "w").write(s)
print(s.count("rim_sheet"), "glow=False" in s)
