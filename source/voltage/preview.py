#!/usr/bin/env python3
"""contact sheet of the generated noteskins on dark and light backgrounds"""
import glob, os, sys
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
CELL = 160


def find(d, prefix):
    return sorted(glob.glob(os.path.join(d, prefix + "*.png")))[0]


def crop(img, cols, rows, c, r):
    w, h = img.width // cols, img.height // rows
    return img.crop((c * w, r * h, (c + 1) * w, (r + 1) * h))


def items(d):
    note = Image.open(find(d, "_CC Tap Note"))
    rec = Image.open(find(d, "_CC Receptor"))
    bolt = Image.open(find(d, "_CC Bolt"))
    lit = Image.open(find(d, "_CC FX Lightning"))
    body = Image.open(find(d, "Down Hold Body Active"))
    roll = Image.open(find(d, "Down Roll Body Active"))
    out = [crop(note, 4, 16, 0, r) for r in range(9)] + [crop(note, 4, 16, 3, 0),
           crop(rec, 3, 1, 0, 0), crop(bolt, 4, 1, 0, 0), crop(body, 4, 1, 0, 0)]
    return out


skins = sorted(glob.glob(os.path.join(OUT, "*")))
rows = []
for s in skins:
    for bg in ((12, 12, 16), (150, 170, 190)):
        rows.append((s, bg))
sheet = Image.new("RGBA", (CELL * 13, CELL * len(rows)), (0, 0, 0, 255))
for ri, (s, bg) in enumerate(rows):
    for ci, im in enumerate(items(s)):
        cell = Image.new("RGBA", (CELL, CELL), bg + (255,))
        im = im.convert("RGBA")
        k = min(CELL / im.width, CELL / im.height) * 0.92
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        cell.alpha_composite(im, ((CELL - im.width) // 2, (CELL - im.height) // 2))
        sheet.alpha_composite(cell, (ci * CELL, ri * CELL))
sheet.convert("RGB").save(sys.argv[1])
print("saved", sys.argv[1])
