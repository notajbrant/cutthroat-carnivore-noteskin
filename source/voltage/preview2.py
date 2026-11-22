#!/usr/bin/env python3
"""how notes look in play: rhythm colour/pattern x direction rim colour, per variant"""
import glob, os, sys
from PIL import Image, ImageChops

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
CELL = 130
DIRS = [("Left", 90, (0.88, 0.32, 1.0)), ("Down", 0, (0.12, 0.86, 1.0)),
        ("Up", 180, (1, 1, 1)), ("Right", -90, (1.0, 0.55, 0.08))]


def find(d, prefix):
    return sorted(glob.glob(os.path.join(d, prefix + "*.png")))[0]


def crop(img, cols, rows, c, r):
    w, h = img.width // cols, img.height // rows
    return img.crop((c * w, r * h, (c + 1) * w, (r + 1) * h)).convert("RGBA")


def tint(img, rgb):
    r, g, b, a = img.split()
    f = [int(x * 255) for x in rgb]
    return Image.merge("RGBA", (r.point(lambda v: v * f[0] // 255), g.point(lambda v: v * f[1] // 255),
                                b.point(lambda v: v * f[2] // 255), a))


skins = [os.path.join(OUT, n) for n in ("cutthroat-carnivore-voltage", "cutthroat-carnivore-voltage-pink",
                                         "cutthroat-carnivore-voltage-red")]
sheet = Image.new("RGBA", (CELL * 20, CELL * len(skins)), (14, 14, 18, 255))
for ri, d in enumerate(skins):
    note, rim = Image.open(find(d, "_CC Tap Note")), Image.open(find(d, "_CC Tap Rim"))
    rec = Image.open(find(d, "_CC Receptor"))
    cells = []
    for q in range(4):
        for name, rot, col in DIRS:
            im = crop(note, 4, 16, 1, q)
            im.alpha_composite(tint(crop(rim, 4, 16, 1, q), col))
            cells.append(im.rotate(-rot, resample=Image.BICUBIC))
    for name, rot, col in DIRS:
        cells.append(tint(crop(rec, 3, 1, 0, 0), col).rotate(-rot, resample=Image.BICUBIC))
    for ci, im in enumerate(cells):
        im = im.resize((int(CELL * 0.92), int(CELL * 0.92)), Image.LANCZOS)
        sheet.alpha_composite(im, (ci * CELL + 5, ri * CELL + 5))
sheet.convert("RGB").save(sys.argv[1])
print("saved")
