# -*- coding: utf-8 -*-
"""Cut the man out of the reference photograph and export him for the hero.

    python render/make_cutter.py            # build, write previews to render/out
    python render/make_cutter.py --install  # ...and swap the two PNGs into index.html

The chapter I cutter is not drawn. Eight hand-drawn passes (a figure, an
articulated one, a two-bone arm, a flat shadow, a traced silhouette) all failed
on the same point: they carried no real information about a person. This keeps
the photograph's own pixels, graded down to the scene's light.

Source: render/ref/cutter-reference.png (1024x1536). It is an AI-generated image
the owner supplied, not a photo of a real person or of our own; replace it with
a shoot of our own before anything here is final.

Pipeline, in order:
  1. mask    - robe first, then an explicit head box, then the forearm skin
  2. split   - the arm is everything forward of a slanted line through the
               shoulder, inside the shoulder-to-hands band
  3. grade   - daylight -> dark forest at low sun
  4. export  - two alpha PNGs on ONE shared box, so they stay in register

Placement lives in index.html, not here (#f1-cutter): both <image>s sit at
x=566 y=666 w=80.3 h=150, feet on the ground line. The arm rotates about the
shoulder at world (611.2, 707.5), which is SX,SY below mapped through that box.
If the box or the source changes, recompute the pivot from the printed
fractions and update the rotate() in heroLoop.
"""
import base64
import io as _io
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "render", "ref", "cutter-reference.png")
OUT = os.path.join(ROOT, "render", "out")
HTML = os.path.join(ROOT, "index.html")
os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert("RGB")
W, H = im.size
a = np.asarray(im).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mx, mn = a.max(2), a.min(2)
val = mx / 255.0
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)

# ─── 1. MASK ────────────────────────────────────────────────────────────────
# Order matters: isolate the ROBE and take its largest connected component
# FIRST, then add the head. The other way round let the head band bridge into
# the sky and the "largest component" became the sky.

# the dishdasha: near-white, in the left half of the frame (the axe and the
# palm trunk are to his right and are not wanted)
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

# Head and masar: an EXPLICIT region, read off the image rather than inferred.
# The shoulder-band heuristic kept missing it and shipped a robe with no head,
# which can never read as a person. Inside this box the only thing that is not
# the man is green foliage.
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

# Forearms and hands: dark SKIN, which a brightness mask can never catch, so
# they were left as a black wedge through his middle. Measured: skin is r>g>b
# in 78% of pixels with r-b about +21; foliage is 24% and +6. Confined to the
# span between his sleeves and the haft.
skin_box = np.zeros((H, W), bool)
skin_box[620:840, 430:660] = True
skin = skin_box & (r > g) & (g > b) & ((r - b) > 12)
skin = ndimage.binary_closing(skin, np.ones((11, 11)))
skin = ndimage.binary_opening(skin, np.ones((5, 5)))
print("forearms: %d px" % skin.sum())

full = body | head | skin
# A wide closing bridges sleeve to sleeve across the forearms.
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
full = lab2 == (1 + int(np.argmax(ndimage.sum(full, lab2, range(1, n2 + 1)))))
mask = full

ys, xs = np.nonzero(mask)
print("figure: %d px, bbox x %d-%d y %d-%d"
      % (mask.sum(), xs.min(), xs.max(), ys.min(), ys.max()))

# ─── 2. SPLIT ───────────────────────────────────────────────────────────────
# Shoulder pivot in source px. Everything forward of a slanted line through it,
# in the shoulder-to-hands band, is the arm; the skirt below stays with the body.
SX, SY = 452.0, 470.0
yy, xx = np.mgrid[0:H, 0:W]
forward = xx > (SX - 30) + 0.16 * (yy - SY)
arm = mask & forward & (yy > 380) & (yy < 812)
arm = ndimage.binary_opening(arm, np.ones((7, 7)))
al, an = ndimage.label(arm)
if an:
    arm = al == (1 + int(np.argmax(ndimage.sum(arm, al, range(1, an + 1)))))
# The body keeps the WHOLE mask, arm included. Cutting the arm out left a hole
# that opened as soon as the arm rotated; the rotating arm simply overlays it.
# The cost is a seam at the top of the stroke, which is why the stroke is only
# 12 degrees: a rigid arm rotated further sweeps the blade past the trunk and
# shows the sleeve it left behind. A full swing needs a second pose image.

# soften the cut edge so he does not read as a sticker
alpha_body = np.clip(ndimage.gaussian_filter(mask.astype(np.float32), 1.6) * 1.15, 0, 1)
alpha_arm = np.clip(ndimage.gaussian_filter(arm.astype(np.float32), 1.6) * 1.15, 0, 1)

# ─── 3. GRADE ───────────────────────────────────────────────────────────────
# The reference is bright daylight; the scene is a dark forest at low sun.
# 0.42 left him blazing white against a near-black forest - pasted on rather
# than lit by the scene. A white dishdasha should still be the brightest thing
# here, but only just.
gr = a / 255.0
lum = gr @ np.array([0.299, 0.587, 0.114], np.float32)
gr = gr * 0.20 + lum[..., None] * 0.06
gr *= np.array([1.06, 0.94, 0.78], np.float32)      # warm
gr = np.clip(gr, 0, 1)

# ─── 4. EXPORT ──────────────────────────────────────────────────────────────
BOX = (xs.min() - 4, ys.min() - 4, xs.max() + 5, ys.max() + 5)
print("box", BOX, " source figure %dx%d" % (BOX[2] - BOX[0], BOX[3] - BOX[1]))


def export(alpha, name):
    x0, y0, x1, y1 = BOX
    rgba = np.dstack([(gr[y0:y1, x0:x1] * 255).astype(np.uint8),
                      (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)])
    img = Image.fromarray(rgba, "RGBA")
    # 420 tall: he is 150 world px normally and 390 at the chapter I push-in,
    # so anything beyond ~420 is weight the page carries for nothing.
    sc = 420.0 / img.height
    if sc < 1:
        img = img.resize((max(1, int(img.width * sc)), int(img.height * sc)), Image.LANCZOS)
    img = img.quantize(colors=128, method=Image.FASTOCTREE).convert("RGBA")
    buf = _io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    raw = buf.getvalue()
    print("  %-5s %sx%s  %.0f KB" % (name, img.width, img.height, len(raw) / 1024))
    img.save(os.path.join(OUT, "cutter_%s.png" % name))
    return img, "data:image/png;base64," + base64.b64encode(raw).decode()


body_img, body_uri = export(alpha_body, "body")
_, arm_uri = export(alpha_arm, "arm")

print("pivot fraction %.4f %.4f  (of the shared box)"
      % ((SX - BOX[0]) / float(BOX[2] - BOX[0]), (SY - BOX[1]) / float(BOX[3] - BOX[1])))

card = Image.new("RGB", body_img.size, (24, 18, 12))
card.paste(body_img, (0, 0), body_img)
card.save(os.path.join(OUT, "cutter_preview.png"))

prev = np.asarray(im).copy()
prev[~mask] = (prev[~mask] * 0.20).astype(np.uint8)
Image.fromarray(prev).resize((560, int(560 * H / W)), Image.LANCZOS).save(
    os.path.join(OUT, "cutter_mask.png"))
print("wrote render/out/cutter_{body,arm,preview,mask}.png")

# ─── INSTALL ────────────────────────────────────────────────────────────────
# Swaps only the two href payloads, in document order (body, then arm), inside
# #f1-cutter. Placement, rig and the drawn axe are left alone.
s = open(HTML, encoding="utf-8", newline="").read()
start = s.index('<g id="f1-cutter"')
end = s.index('<!-- Roots reaching down', start)
block = s[start:end]
live = re.findall(r'href="(data:image/png;base64,[^"]+)"', block)
if len(live) != 2:
    sys.exit("expected 2 images in #f1-cutter, found %d" % len(live))
same = live == [body_uri, arm_uri]
print("index.html cutter %s this build" % ("MATCHES" if same else "DIFFERS from"))

if "--install" in sys.argv and not same:
    block = block.replace(live[0], body_uri, 1).replace(live[1], arm_uri, 1)
    open(HTML, "w", encoding="utf-8", newline="").write(s[:start] + block + s[end:])
    print("installed; index.html is now %.0f KB" % (os.path.getsize(HTML) / 1024))
