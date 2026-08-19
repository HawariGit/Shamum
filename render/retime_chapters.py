"""
Give each chapter its own band of p so a shelf never covers a chapter that
is still playing.

Before, the chapters overlapped heavily — II ran to 0.72 while III started at
0.52, and IV started at 0.80 while III ran to 0.97 — which was fine for one
continuous journey but means any shelf boundary lands mid-animation. The
oils shelf was arriving at p 0.789 while the flacon's cap seals at 0.88.

After:
    chapter I    0.00 – 0.30
    chapter II   0.24 – 0.62      -> Bukhoor shelf
    chapter III  0.62 – 0.88      -> Oils shelf
    chapter IV   0.88 – 1.00      -> Fragrances shelf

Usage: python render/retime_chapters.py [--apply]
"""

import sys, io

APPLY = "--apply" in sys.argv
SRC = "index.html"
html = open(SRC, encoding="utf-8").read()

# (old, new, label) — every one must match exactly once
EDITS = [
    # ── camera and the drop between floors ──
    ("var fallT = seg(p, 0.56, 0.68);",
     "var fallT = seg(p, 0.63, 0.71);", "fall between floors"),
    ("if (p < 0.26)      camY = 0;",
     "if (p < 0.24)      camY = 0;", "cam hold floor 1"),
    ("else if (p < 0.40) camY = sstep(seg(p, 0.26, 0.40)) * 900;",
     "else if (p < 0.36) camY = sstep(seg(p, 0.24, 0.36)) * 900;", "cam pan 1->2"),
    ("else if (p < 0.56) camY = 900;",
     "else if (p < 0.63) camY = 900;", "cam hold floor 2"),
    ("else if (p < 0.68) camY = 900 + sstep(fallT) * 900;",
     "else if (p < 0.71) camY = 900 + sstep(fallT) * 900;", "cam pan 2->3"),
    ("else if (p < 0.80) camY = 1800;",
     "else if (p < 0.885) camY = 1800;", "cam hold floor 3"),
    ("else if (p < 0.92) camY = 1800 + sstep(seg(p, 0.80, 0.92)) * 900;",
     "else if (p < 0.94) camY = 1800 + sstep(seg(p, 0.885, 0.94)) * 900;", "cam pan 3->4"),

    # ── chapter II must be finished before the bukhoor shelf ──
    ("if (p > 0.18 && p < 0.72) {",
     "if (p > 0.18 && p < 0.66) {", "f2 gate"),
    ("(1 - eIn(seg(p, 0.56, 0.64)))",
     "(1 - eIn(seg(p, 0.53, 0.61)))", "smoke fade out"),

    # ── the falling drop ──
    ("if (p > 0.44 && p < 0.70) {",
     "if (p > 0.50 && p < 0.73) {", "drop gate"),
    ("var formT = seg(p, 0.47, 0.56);",
     "var formT = seg(p, 0.54, 0.63);", "drop forms"),
    ("var dropVisible = p >= 0.47 && p < 0.68;",
     "var dropVisible = p >= 0.54 && p < 0.71;", "drop visible"),

    # ── chapter III inside 0.62–0.88 ──
    ("if (p > 0.52 && p < 0.97) {",
     "if (p > 0.60 && p < 0.90) {", "f3 gate"),
    ("op(sc.f3spot, eOut(seg(p, 0.60, 0.70)) * 0.85);",
     "op(sc.f3spot, eOut(seg(p, 0.645, 0.72)) * 0.85);", "f3 spot"),
    ("var spotEnv = eOut(seg(p, 0.60, 0.72));",
     "var spotEnv = eOut(seg(p, 0.645, 0.735));", "f3 motes"),
    ("var spT = seg(p, 0.675, 0.735);",
     "var spT = seg(p, 0.705, 0.75);", "f3 splash"),
    ("var lvT = eOut(seg(p, 0.68, 0.80));",
     "var lvT = eOut(seg(p, 0.71, 0.80));", "f3 fill"),
    ("var stillIn  = eOut(seg(p, 0.575, 0.665));",
     "var stillIn  = eOut(seg(p, 0.625, 0.70));", "still arrives"),
    ("var stillOut = eOut(seg(p, 0.795, 0.855));",
     "var stillOut = eOut(seg(p, 0.80, 0.845));", "still withdraws"),
    ("var dripWin = seg(p, 0.655, 0.805);",
     "var dripWin = seg(p, 0.695, 0.80);", "drip window"),
    ("var capT = eOut(seg(p, 0.80, 0.88));",
     "var capT = eOut(seg(p, 0.80, 0.865));", "cap seals"),

    # ── chapter IV inside 0.88–1.00 ──
    ("if (p > 0.80) {",
     "if (p > 0.86) {", "f4 gate"),
    ("var f4in = eOut(seg(p, 0.86, 0.96));",
     "var f4in = eOut(seg(p, 0.885, 0.945));", "f4 arrives"),
    ("var pressT = seg(p, 0.900, 0.930);",
     "var pressT = seg(p, 0.952, 0.976);", "atomizer press"),
    ("var mistEnv = eOut(seg(p, 0.912, 0.952));",
     "var mistEnv = eOut(seg(p, 0.960, 0.988));", "spray mist"),
    ("var f4env = eOut(seg(p, 0.88, 0.97));",
     "var f4env = eOut(seg(p, 0.90, 0.975));", "f4 sparks"),

    # ── chapter titles follow their chapters ──
    ("chReveal(sc.ht2, seg(p, 0.41, 0.465), seg(p, 0.535, 0.575));",
     "chReveal(sc.ht2, seg(p, 0.40, 0.45), seg(p, 0.545, 0.585));", "title II"),
    ("chReveal(sc.ht3, seg(p, 0.705, 0.76), seg(p, 0.785, 0.825));",
     "chReveal(sc.ht3, seg(p, 0.665, 0.715), seg(p, 0.815, 0.855));", "title III"),
    ("chReveal(sc.ht4, seg(p, 0.955, 0.99), 0);",
     "chReveal(sc.ht4, seg(p, 0.90, 0.94), 0);", "title IV"),
    ("sc.ht4.style.pointerEvents = p > 0.965 ? 'auto' : 'none';",
     "sc.ht4.style.pointerEvents = p > 0.915 ? 'auto' : 'none';", "title IV clicks"),

    # ── canvas fx ──
    ("+ eOut(seg(p, 0.86, 1))*0.25;",
     "+ eOut(seg(p, 0.885, 1))*0.25;", "fx floor 4"),
    ("var burstT = seg(p, 0.935, 0.98);",
     "var burstT = seg(p, 0.952, 0.99);", "fx spray burst"),
]

fails = []
for old, new, label in EDITS:
    n = html.count(old)
    if n != 1:
        fails.append("%-22s matched %d times: %s" % (label, n, old[:56]))
        continue
    html = html.replace(old, new, 1)
    print("  %-22s ok" % label)

if fails:
    print("\nFAILED:")
    for f in fails:
        print("  " + f)
    sys.exit(1)

print("\nall %d thresholds retimed" % len(EDITS))
if APPLY:
    with io.open(SRC, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    print("WRITTEN")
else:
    print("dry run — pass --apply")
