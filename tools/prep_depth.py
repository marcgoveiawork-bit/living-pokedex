"""Clean a raw depth map so it matches its photo and doesn't tear the image.

usage: python3 tools/prep_depth.py <photo> <raw-depth> <out-depth> [--fill x0,y0,x1,y1] [--cap x0,y0,x1,y1] [--clear x0,y0,x1,y1]

--fill: a box (in photo pixels) where the depth tool missed part of the subject, e.g. a
flame or smoke. Subject pixels in that box with backdrop-like depth are filled in from the
depth of the adjoining subject part, so the missed part moves with the body instead of the wall.
--cap: a box where the depth tool got part of the subject badly wrong (e.g. a flame
reading as far nearer than the tail it sits on). Depth in the box is capped at the typical subject
depth just outside the box, so correct (farther) parts inside the box are left alone.

Steps: resize to the photo, find the subject (anything that isn't plain studio
backdrop), throw away depth "halos" that spill onto the backdrop, widen the
subject's depth edge a few pixels so stretching happens in the empty backdrop
rather than on the subject, then normalise.
--clear: a box where the depth tool drew a halo onto empty backdrop (e.g. a glow above the
head). Inside the box only colour decides what is subject, so the halo is dropped.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

photo, raw, out = sys.argv[1:4]
rgb = np.asarray(Image.open(photo).convert("RGB")).astype(float)
h, w = rgb.shape[:2]
k = max(1, round(w / 512))
odd = lambda n: int(n) * k // 2 * 2 + 1
d = np.asarray(Image.open(raw).convert("L").resize((w, h), Image.BICUBIC)).astype(float)

# Backdrop depth: one smooth value per row (dark wall up top, floor rising below).
row = np.percentile(d, 8, axis=1)
row = np.minimum.accumulate(row[::-1])[::-1]          # never nearer than rows below it
row = np.convolve(np.pad(row, 12 * k, mode="edge"), np.ones(24 * k + 1) / (24 * k + 1), mode="valid")
bg = np.repeat(row[:, None], w, axis=1)

# Subject = coloured or dark pixels; the backdrop is near-white and unsaturated.
sat = rgb.max(2) - rgb.min(2)
# White/grey parts of the subject (a pale belly, claws) look like backdrop by colour, so also
# count anything the depth map says is clearly near, then fill fully enclosed holes.
near = d > bg + 0.5 * (np.percentile(d[:int(h * .8)], 99) - bg)
near[int(h * .8):] = False                              # ignore the floor rising toward the camera
if "--clear" in sys.argv:
    for spec in sys.argv[sys.argv.index("--clear") + 1].split(";"):      # several boxes: "a,b,c,d;e,f,g,h"
        x0, y0, x1, y1 = map(int, spec.split(","))
        near[y0:y1, x0:x1] = False
fg = ((sat > 28) | (rgb.min(2) < 150) | near).astype(np.uint8) * 255
fg = Image.fromarray(fg).filter(ImageFilter.MedianFilter(odd(5)))             # drop speckle
flood = fg.copy()
from PIL import ImageDraw
for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0)]:
    if flood.getpixel(xy) == 0: ImageDraw.floodfill(flood, xy, 128)
fg = Image.fromarray(np.where(np.asarray(flood) == 0, 255, np.asarray(fg)).astype(np.uint8))
fg = fg.filter(ImageFilter.MaxFilter(odd(9)))                                  # widen the edge
soft = np.asarray(fg.filter(ImageFilter.GaussianBlur(2 * k))).astype(float) / 255

# Optional: fill parts of the subject the depth tool missed (flames, smoke).
if "--fill" in sys.argv:
    x0, y0, x1, y1 = map(int, sys.argv[sys.argv.index("--fill") + 1].split(","))
    box = np.zeros((h, w), bool); box[y0:y1, x0:x1] = True
    subj = np.asarray(fg) > 0
    hole = box & subj & (d < bg + 0.25 * (d[subj].max() - bg))
    # Use the depth of the adjoining, correctly-measured part of the subject (e.g. the tail tip).
    near = box & subj & ~hole
    d = np.where(hole, np.percentile(d[near], 75) if near.any() else d, d)
    print("filled", int(hole.sum()), "missed subject pixels")

if "--cap" in sys.argv:
    x0, y0, x1, y1 = map(int, sys.argv[sys.argv.index("--cap") + 1].split(","))
    box = np.zeros((h, w), bool); box[y0:y1, x0:x1] = True
    m = 40 * k
    ring = np.zeros((h, w), bool); ring[max(0, y0 - m):y1 + m, max(0, x0 - m):x1 + m] = True
    subj = np.asarray(fg) > 0
    near = ring & ~box & subj & (d > bg + 0.25 * (d[subj].max() - bg))
    if near.any():
        d = np.where(box, np.minimum(d, np.median(d[near])), d)
        print("capped box at depth", round(float(d[box].max()), 1))

# Subject depth, grown outward so its edge fully covers the silhouette.
grown = np.asarray(Image.fromarray(d.astype(np.uint8)).filter(ImageFilter.MaxFilter(odd(9)))).astype(float)
hi = np.percentile(d[np.asarray(fg) > 0], 99.5)       # clip stray hot spots
res = np.minimum(grown, hi) * soft + bg * (1 - soft)
res = (res - res.min()) / (res.max() - res.min()) * 255
Image.fromarray(res.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.3 * k)).save(out)
print(out, f"{w}x{h}", "subject covers %.0f%%" % (100 * (np.asarray(fg) > 0).mean()))
