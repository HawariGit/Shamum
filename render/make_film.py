# -*- coding: utf-8 -*-
"""Cut the Mandle film down for the site.

    python render/make_film.py              # everything
    python render/make_film.py --only loop  # or --only film

Source: SHAMUM's own Instagram reel for Mandle, 1080x1920 HEVC, 41.7s, sitting
untracked at the repo root as "VID_20260819_235210_113 (1).mp4" (29 MB - too
big to commit, and never deployed). It carries two things that must not reach
the page: the @SHAMUMOFFICIAL handle and burned-in subtitles.

THE CROP. Both overlays sit outside one horizontal band. The handle is at
0.25-0.31 of the height (top right) or 0.66-0.73 (lower left) depending on the
shot, and the subtitles are at 0.84-0.90. Rows 614-1258 (0.32-0.655) are clean
on every shot up to the Instagram end card at 37.67s, and 1080x644 is a
1.68:1 widescreen frame - the vertical reel becomes a cinematic one. Checked on
a 1 fps contact sheet with the band drawn in; redo that if the source changes.

The subtitles are cropped away, so the page re-typesets the film's words itself
(FILM_CAPTIONS in index.html), synced to currentTime.

Outputs, all in assets/film/:
  mandle-film.mp4   0-37.4s, with sound, for the #film section
  mandle-loop.mp4   ~8s, silent, the landing screen behind the wordmark
  mandle-film.webp  poster: the bottle on satin
  mandle-loop.webp  poster: the loop's first frame
"""
import os
import subprocess
import sys

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "VID_20260819_235210_113 (1).mp4")
OUT = os.path.join(ROOT, "assets", "film")
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(OUT, exist_ok=True)

BAND = "crop=1080:644:0:614"
FILM_END = 37.4          # the end card cuts in at 37.67

# Landing loop: only the warm, abstract shots. The reel cuts every ~0.8s, which
# is right for Instagram and frantic behind a wordmark, so these are slowed to
# 0.4x with motion interpolation. The satin bottle is left out on purpose: its
# label monogram would sit directly under the SHAMUM logo. Boundaries are exact
# frame cuts, measured from a band-only frame difference.
# It OPENS on the flame: a dark frame with warm light in it is what the rest of
# the site looks like, and it is the first thing anyone sees. The pale-gold
# shots come after, when the wordmark has already been read.
LOOP = [                 # (start, end) in source seconds
    (27.10, 27.95),      # the flame
    (0.00, 0.78),        # oil in the flask
    (3.00, 3.60),        # the gold drop into the beaker
    (9.40, 10.50),       # liquid gold
]
SLOW = 2.5               # 0.4x
# The loop's grade is BAKED IN, not done with CSS filters. Dimmed in the browser
# its near-white highlights went neutral grey and its yellows went olive - dark
# yellow simply IS olive - so the flame read as a grey-green blade. Firelight in
# the dark shifts toward orange as it darkens, so: multiply toward amber, then a
# gamma that crushes the mids and keeps the highlights. White lands on (199,
# 110,44)-ish amber, mid gold on deep brown. Chosen from a side-by-side sim of
# three strengths with the real wordmark composited over the four shots.
AMBER = (1.00, 0.72, 0.44)
GAMMA, GAIN = 1.8, 0.78
GRADE = "format=rgb24,lutrgb=" + ":".join(
    "%s='pow(val/255*%.2f,%.2f)*%.2f*255'" % (c, m, GAMMA, GAIN)
    for c, m in zip("rgb", AMBER)) + ",format=yuv420p"
XF = 0.6                # crossfade between shots


def run(args):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y"] + args)
    if r.returncode:
        raise SystemExit("ffmpeg failed")


X264 = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart"]

ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

# 1. the film
fo = FILM_END - 0.6
if ONLY in (None, "film"):
    run(["-i", SRC, "-t", str(FILM_END),
         "-vf", "%s,fade=t=out:st=%.2f:d=0.6" % (BAND, fo),
         "-af", "afade=t=out:st=%.2f:d=0.6" % fo,
         "-crf", "23"] + X264 + ["-c:a", "aac", "-b:a", "112k",
         os.path.join(OUT, "mandle-film.mp4")])
    # poster: the bottle on satin
    run(["-ss", "33.0", "-i", SRC, "-frames:v", "1", "-vf", BAND, "-quality", "82",
         os.path.join(OUT, "mandle-film.webp")])
if ONLY == "film":
    raise SystemExit

# 2. the loop
parts, durs = [], []
for i, (a, b) in enumerate(LOOP):
    parts.append("[0:v]trim=%.3f:%.3f,setpts=(PTS-STARTPTS)*%.2f,%s,"
                 "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
                 "settb=1/30[s%d]" % (a, b, SLOW, BAND, i))
    durs.append((b - a) * SLOW)
chain, prev, t = [], "s0", durs[0]
for i in range(1, len(LOOP)):
    t -= XF
    chain.append("[%s][s%d]xfade=transition=fade:duration=%.2f:offset=%.3f[x%d]"
                 % (prev, i, XF, t, i))
    prev, t = "x%d" % i, t + durs[i]
# through black at the loop point, so the jump back to the first shot is a fade
chain.append("[%s]%s,fade=t=in:st=0:d=0.5,fade=t=out:st=%.3f:d=0.5[v]" % (prev, GRADE, t - 0.5))
run(["-i", SRC, "-filter_complex", ";".join(parts + chain), "-map", "[v]", "-an",
     "-crf", "27"] + X264 + [os.path.join(OUT, "mandle-loop.mp4")])

# 3. loop poster: the flame, steady
run(["-ss", "1.0", "-i", os.path.join(OUT, "mandle-loop.mp4"), "-frames:v", "1",
     "-quality", "80", os.path.join(OUT, "mandle-loop.webp")])

for f in sorted(os.listdir(OUT)):
    print("%-18s %7.0f KB" % (f, os.path.getsize(os.path.join(OUT, f)) / 1024))
print("loop %.1fs" % t)
