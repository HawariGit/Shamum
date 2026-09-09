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

# 2. head and masar: an EXPLICIT region, read off the image rather than
#    inferred. The shoulder-band heuristic kept missing it and shipped a robe
#    with no head, which can never read as a person. Inside this box the only
#    thing that is not the man is green foliage.
HX0, HY0, HX1, HY1 = 375, 200, 585, 458
box = np.zeros((H, W), bool)
box[HY0:HY1, HX0:HX1] = True
green = (g > r + 6) & (g > b + 6)
head = box & ~green
head = ndimage.binary_closing(head, np.ones((9, 9)))
head = ndimage.binary_opening(head, np.ones((7, 7)))
hl, hn = ndimage.label(head)
if hn:
    head = hl == (1 + int(np.argmax(ndimage.sum(head, hl, range(1, hn + 1)))))
print("head: %d px, %d components" % (head.sum(), hn))

# 3. forearms and hands: dark SKIN, which a brightness mask can never catch, so
#    they were left as a black wedge through his middle. Measured: skin is
#    r>g>b in 78% of pixels with r-b about +21; foliage is 24% and +6. Confined
#    to the span between his sleeves and the haft.
skin_box = np.zeros((H, W), bool)
skin_box[620:840, 430:660] = True
skin = skin_box & (r > g) & (g > b) & ((r - b) > 12)
skin = ndimage.binary_closing(skin, np.ones((11, 11)))
skin = ndimage.binary_opening(skin, np.ones((5, 5)))
print("forearms: %d px" % skin.sum())

full = body | head | skin
# His forearms and hands are dark skin, so the brightness mask dropped them
# and left a hole through his middle that the scene showed through. A wide
# closing bridges sleeve to sleeve across them.
full = ndimage.binary_closing(full, np.ones((41, 41)))
# Sunlit ground and leaves cling to his right edge as thin bright spurs that
# survive a plain opening. Eroding then dilating by a larger element severs
# them; the few px it costs the figure are invisible at display size.
full = ndimage.binary_erosion(full, np.ones((11, 11)))
fl, fn = ndimage.label(full)
if fn:
    full = fl == (1 + int(np.argmax(ndimage.sum(full, fl, range(1, fn + 1)))))
full = ndimage.binary_dilation(full, np.ones((9, 9)))
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
