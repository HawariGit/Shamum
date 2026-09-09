# -*- coding: utf-8 -*-
"""Generate chapter I's tree: branch structure + foliage, as SVG.

The old canopy was three stacked ellipses ~500px across with lighter ellipses
inside them as highlights, a hard-edged elliptical "saucer" underneath, and two
thin diagonals standing in for branches. It read as cartoon broccoli on a stick.

Two things were wrong and only one of them is "ellipses":

1. SIZE AND COUNT. Foliage reads as foliage when the mass is built from many
   small overlapping shapes with a broken outer edge. Three enormous ones read
   as a blob. This uses ~150 small ellipses clustered on real branch tips.
2. NO BRANCHING. A tree's silhouette IS its branching. This grows the limbs
   recursively so the forks thin and spread the way a real one does.

Aquilaria is a tall, straight-boled tropical evergreen with a relatively narrow,
open crown - not a lollipop. The crown here is ~360 wide against the old ~550,
and taller, so the trunk stays the dominant vertical.

Palette: the tree is BACKLIT (f1-sun sits behind it at 720,330), so this is a
near-silhouette in warm darks rather than flat mid-green. That also stops
chapter I being the only green thing on an otherwise gold-and-near-black site.

Deterministic: fixed seed, so re-running produces the same tree.
"""
import math
import random

random.seed(20260909)

TRUNK_TOP = 558.0          # where the drawn trunk path ends; limbs start here
TRUNK_HALF = 11.0          # half-width of the stem at that height

branches = []              # (x1,y1,x2,y2,width,depth)
tips = []                  # (x,y,depth) for foliage clustering


def grow(x, y, ang, length, width, depth):
    """One limb, then its children. Angle in degrees, 0 = straight up."""
    if depth > 4 or length < 11:
        tips.append((x, y, depth))
        return
    rad = math.radians(ang)
    # a slight curve per limb so nothing is a straight stick
    mx = x + math.sin(rad) * length * 0.5 + random.uniform(-4, 4)
    my = y - math.cos(rad) * length * 0.5
    x2 = x + math.sin(rad) * length
    y2 = y - math.cos(rad) * length
    branches.append((x, y, mx, my, x2, y2, width, depth))
    # two or three children, splitting away from the parent angle
    n = 2 if random.random() < 0.88 else 3
    for i in range(n):
        spread = random.uniform(16, 34) * (1 if i % 2 == 0 else -1)
        if n == 3 and i == 2:
            spread = random.uniform(-10, 10)
        grow(x2, y2,
             ang + spread + random.uniform(-6, 6),
             length * random.uniform(0.62, 0.78),
             max(1.4, width * 0.62),
             depth + 1)


# three limbs off the main stem, and the stem itself continuing up
grow(720, TRUNK_TOP, random.uniform(-3, 3), 92, TRUNK_HALF * 1.7, 0)
grow(712, TRUNK_TOP + 6, -26, 74, TRUNK_HALF * 1.2, 1)
grow(729, TRUNK_TOP + 4, 27, 76, TRUNK_HALF * 1.25, 1)

# ── branch paths, darkest first so thin twigs sit over thick limbs ──
branches.sort(key=lambda b: -b[6])
bpaths = []
for (x1, y1, mx, my, x2, y2, w, d) in branches:
    col = ["#241505", "#201204", "#1B0F03", "#170C02", "#130A02"][min(d, 4)]
    bpaths.append(
        '<path d="M%.1f %.1f Q%.1f %.1f %.1f %.1f" stroke="%s" stroke-width="%.1f" '
        'fill="none" stroke-linecap="round"/>' % (x1, y1, mx, my, x2, y2, col, w))

# ── foliage: many small masses clustered on the tips ──
# Backlit, so the body is near-black warm and only the outer edge catches sun.
BODY = ["#101B0A", "#0C1507", "#141F0C", "#0A1206", "#17240E"]
RIM = ["#2C3C1A", "#35471F", "#233110"]
cx_all = 720.0
cy_all = 350.0
back, mid, front = [], [], []
for (tx, ty, d) in tips:
    n = random.randint(2, 4)
    for _ in range(n):
        a = random.uniform(0, math.tau)
        r = random.uniform(0, 26)
        ex = tx + math.cos(a) * r
        ey = ty + math.sin(a) * r * 0.72
        rx = random.uniform(6, 26)
        ry = rx * random.uniform(0.52, 0.74)
        rot = random.uniform(-28, 28)
        # distance from the crown centre decides depth and whether it is rim-lit
        dist = math.hypot(ex - cx_all, (ey - cy_all) * 1.5) / 210.0
        edge = dist > 0.86 and random.random() < 0.16
        col = random.choice(RIM) if edge else random.choice(BODY)
        op = random.uniform(0.55, 0.85) if edge else random.uniform(0.72, 0.96)
        el = ('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" '
              'opacity="%.2f" transform="rotate(%.0f %.1f %.1f)"/>'
              % (ex, ey, rx, ry, col, op, rot, ex, ey))
        (back if dist > 0.75 else (mid if dist > 0.42 else front)).append((ey, el))

for grp in (back, mid, front):
    grp.sort(key=lambda t: t[0])          # higher shapes behind lower ones

print("branches %d   foliage %d (back %d / mid %d / front %d)"
      % (len(bpaths), len(back) + len(mid) + len(front), len(back), len(mid), len(front)))
xs = [t[0] for t in tips]; ys = [t[1] for t in tips]
print("crown extent  x %.0f-%.0f (%.0f wide)   y %.0f-%.0f"
      % (min(xs), max(xs), max(xs) - min(xs), min(ys), max(ys)))

svg = []
svg.append("            <!-- Limbs: grown recursively, thinning and spreading. -->")
svg += ["            " + p for p in bpaths]
for name, grp in (("can-back", back), ("can-mid", mid), ("can-front", front)):
    svg.append('            <g id="%s">' % name)
    svg += ["              " + e for _, e in grp]
    svg.append("            </g>")

open(r"C:\onedrive\Shm\render\out\tree_svg.txt", "w", encoding="utf-8").write("\n".join(svg))
print("wrote render/out/tree_svg.txt  (%d lines)" % len(svg))
