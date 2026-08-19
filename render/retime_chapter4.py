"""Give chapter IV room to be watched filling.

The fill was landing entirely inside the camera's pan up to floor 4. Measured
on the page: at 8.3vh the camera is at -1923 and the bottle is empty, at 8.6vh
the camera is at -2695 and the bottle is 99% full. So the flacon arrived in
frame already filled and the fill itself was never seen on a settled camera.

Chapter III does not have this problem: the camera reaches floor 3 at p 0.71
and the oil fill runs 0.71-0.80, so the fill starts exactly as the camera
stops. Chapter IV is retimed to the same shape.

    before                              after
    cam pan 3->4  0.885 - 0.940         0.885 - 0.918
    bottle settle 0.885 - 0.945         0.885 - 0.925
    fill          0.900 - 0.948         0.925 - 0.948
    press         0.952 - 0.976         unchanged
    mist          0.960 - 0.988         unchanged

The pan is quicker but not out of character: 0.033 of p, against 0.08 for the
floor 2->3 pan which is 0.34 of a viewport of scroll - at gap3's new height the
new pan is 0.38 of a viewport. gap3 grows from 190vh to 260vh so the fill gets
about a third of a viewport of scroll, comparable to chapter III's 0.38. Gap
height is the pacing dial and is independent of every threshold here.

All-or-nothing: every anchor must match exactly once.
"""

import io
import sys

PATH = "index.html"
src = io.open(PATH, encoding="utf-8").read()

EDITS = [
    # ── camera reaches floor 4 sooner, so there is room to watch the fill ──
    ("else if (p < 0.94) camY = 1800 + sstep(seg(p, 0.885, 0.94)) * 900;",
     "else if (p < 0.918) camY = 1800 + sstep(seg(p, 0.885, 0.918)) * 900;",
     "cam pan 3->4"),
    ("  else               camY = 2700;",
     "  else               camY = 2700;",
     "cam hold floor 4 (unchanged, checked)"),

    # ── glow, rays, halo and the bottle settle before the fill starts ──
    ("  var f4in = eOut(seg(p, 0.885, 0.945));",
     "  var f4in = eOut(seg(p, 0.885, 0.925));",
     "f4 settle"),

    # ── the fill now begins on a stopped camera and a settled bottle ──
    ("  var f4lv = eOut(seg(p, 0.90, 0.948));",
     "  var f4lv = eOut(seg(p, 0.925, 0.948));",
     "fill window"),
    ("""The flacon fills, the way the vial does on floor 3. It runs 0.90 to 0.948:
     it starts once the bottle is most of the way out of the dark (f4in is 0.70
     at 0.90) and is finished before the atomizer is pressed at 0.952, so the
     bottle is full at the moment it is used rather than being pressed empty.""",
     """The flacon fills, the way the vial does on floor 3, and for the same
     reason on the same terms: the camera reaches floor 4 at 0.918 and the
     bottle has settled by 0.925, so the fill runs 0.925 to 0.948 on a stopped
     camera and finishes a beat before the atomizer is pressed at 0.952. Run
     earlier it played out during the pan, and the flacon arrived already full.""",
     "fill comment"),
]

out = src
for old, new, label in EDITS:
    n = out.count(old)
    if n != 1:
        print("ABORT: %-28s matched %d times (need 1)" % (label, n))
        sys.exit(1)

for old, new, label in EDITS:
    out = out.replace(old, new, 1)

# ── gap3 gets more scroll so the retimed beats are not rushed ──
for old, new, label in [
    ('.chapter-gap[data-chapter="3"] { height: 190vh; }',
     '.chapter-gap[data-chapter="3"] { height: 260vh; }', "gap3 desktop"),
    ('  .chapter-gap[data-chapter="3"] { height: 165vh; }',
     '  .chapter-gap[data-chapter="3"] { height: 225vh; }', "gap3 mobile"),
]:
    n = out.count(old)
    if n != 1:
        print("ABORT: %-28s matched %d times (need 1)" % (label, n))
        sys.exit(1)
    out = out.replace(old, new, 1)

io.open(PATH, "w", encoding="utf-8", newline="").write(out)
print("chapter IV retimed; gap3 190vh -> 260vh (165 -> 225 mobile)")
