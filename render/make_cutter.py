# -*- coding: utf-8 -*-
"""Pull a clean human silhouette out of the reference image.

Eight hand-drawn passes failed on anatomy. A traced outline carries the
proportion and gesture that hand-placed coordinates cannot.

Order matters: isolate the ROBE and take its largest connected component FIRST,
then grow the head from that component. Doing it the other way round let the
head band bridge into the sky and the "largest component" became the sky.
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC = r"C:\Users\ASUS\Downloads\ChatGPT Image Sep 9, 2026, 03_16_31 PM.png"
OUT = r"C:\onedrive\Shm\render\out"

im = Image.open(SRC).convert("RGB")
W, H = im.size
a = np.asarray(im).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mx, mn = a.max(2), a.min(2)
val = mx / 255.0
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)

# 1. the dishdasha: near-white, almost colourless, in the left half of the frame
#    (the axe and the palm trunk are to his right and are not wanted)
ROI = np.zeros((H, W), bool)
ROI[int(H * 0.22):, int(W * 0.12):int(W * 0.52)] = True
# Measured, not guessed: robe val median 0.75 / sat 0.23; foliage 0.15 / 0.19;
# trunk 0.22. BRIGHTNESS separates them, saturation does not - the old
# sat < 0.14 was discarding the robe itself.
robe = (val > 0.55) & (sat < 0.35) & ROI
robe = np.asarray(Image.fromarray((robe * 255).astype(np.uint8))
                  .filter(ImageFilter.MedianFilter(9))) > 127
# Sunlit gaps in the foliage touch the robe along its edge. Opening snaps those
# thin bridges so the component filter keeps the man and drops the background.
robe = ndimage.binary_opening(robe, np.ones((15, 15)))

lab, n = ndimage.label(robe)
sizes = ndimage.sum(robe, lab, range(1, n + 1))
body = lab == (1 + int(np.argmax(sizes)))
ys, xs = np.nonzero(body)
print("robe: %d components, kept %d px, bbox x %d-%d y %d-%d"
      % (n, body.sum(), xs.min(), xs.max(), ys.min(), ys.max()))

# 2. head and masar: take the band above the shoulders, drop anything green or
#    sky-blue, then keep only the piece that actually TOUCHES the robe. A plain
#    rectangle here was being swallowed whole and shipped as a square head.
notleaf = ~((g > r + 10) & (g > b + 10))
notsky = ~((b > r + 12) & (b > g + 6))
# The band has to sit over the SHOULDERS, not over the robe's left edge - the
# head is offset right of the body's centroid and the first attempt searched a
# column the head was never in.
sh = ys.min()
top_rows = (np.arange(H)[:, None] < sh + int(H * 0.06)) & body
tcols = np.nonzero(top_rows.any(0))[0]
band = np.zeros((H, W), bool)
band[max(0, sh - int(H * 0.20)):sh + 10,
     max(0, tcols.min() - 40):min(W, tcols.max() + 40)] = True
print("shoulder columns x %d-%d -> head band x %d-%d"
      % (tcols.min(), tcols.max(), max(0, tcols.min() - 40), min(W, tcols.max() + 40)))
head = band & notleaf & notsky & (val > 0.26)
head = ndimage.binary_opening(head, np.ones((9, 9)))
hl, hn = ndimage.label(head)
keep = np.zeros((H, W), bool)
shoulders = ndimage.binary_dilation(body, np.ones((31, 31)))
for i in range(1, hn + 1):
    piece = hl == i
    if (piece & shoulders).any() and piece.sum() > 150:
        keep |= piece
head = keep
print("head: %d of %d pieces touch the robe (%d px)" % ((keep.sum() > 0), hn, keep.sum()))

full = body | head
full = ndimage.binary_closing(full, np.ones((13, 13)))
full = ndimage.binary_fill_holes(full)
lab2, n2 = ndimage.label(full)
sizes2 = ndimage.sum(full, lab2, range(1, n2 + 1))
full = lab2 == (1 + int(np.argmax(sizes2)))

ys2, xs2 = np.nonzero(full)
print("figure: %d px, bbox x %d-%d y %d-%d  (%.0f x %.0f)"
      % (full.sum(), xs2.min(), xs2.max(), ys2.min(), ys2.max(),
         xs2.max() - xs2.min(), ys2.max() - ys2.min()))

prev = np.asarray(im).copy()
prev[~full] = (prev[~full] * 0.20).astype(np.uint8)
Image.fromarray(prev).resize((560, int(560 * H / W)), Image.LANCZOS).save(
    os.path.join(OUT, "trace_mask.png"))
Image.fromarray((full * 255).astype(np.uint8)).resize(
    (560, int(560 * H / W)), Image.LANCZOS).save(os.path.join(OUT, "trace_flat.png"))
np.save(os.path.join(OUT, "trace_mask.npy"), full)
print("wrote trace_mask.png / trace_flat.png")

# ── Stage 2 (see scratchpad cutout.py / install.py in the session that made
# this): the mask is split into body and arm on a shared bounding box, exported
# as alpha PNGs and embedded as <image> in index.html. The body keeps the WHOLE
# mask - cutting the arm out of it left a hole that opened up the moment the arm
# rotated. The rotating arm simply overlays it.
