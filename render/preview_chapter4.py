"""Render chapter IV's beats by driving the real heroLoop.

preview_flacon.py hardcodes one floor-4 state, which is fine for looking at the
bottle but useless for checking a sequence: it cannot tell you whether the drop
is on screen when it lands, or whether the camera has finished arriving before
the story starts. This instead reuses the reduced-motion still: heroStill pins
p to a constant and renders exactly one frame through the real animation code,
so what comes out is what the page does at that p, not a reimplementation.

    python render/preview_chapter4.py --p 0.93
    python render/preview_chapter4.py --strip 0.885,0.91,0.93,0.95,0.97,0.99

Writes to render/out/. The temporary page is _rmtest.html at the repo root -
the same name preview_reduced.py uses, so it is already in .gitignore and
.vercelignore and cannot be committed or published by accident.
"""

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
TMP = os.path.join(ROOT, "_rmtest.html")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FLAG = "var heroStill = window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
STILL_P = re.compile(r"var HERO_STILL_P = [\d.]+;")


def browser():
    for b in (CHROME, EDGE):
        if os.path.exists(b):
            return b
    print("ABORT: no Chrome or Edge found")
    sys.exit(1)


def shot(p, dest):
    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if src.count(FLAG) != 1:
        print("ABORT: heroStill declaration moved; update FLAG")
        sys.exit(1)
    src = src.replace(FLAG, "var heroStill = true;", 1)
    if not STILL_P.search(src):
        print("ABORT: HERO_STILL_P not found")
        sys.exit(1)
    src = STILL_P.sub("var HERO_STILL_P = %s;" % p, src, count=1)
    io.open(TMP, "w", encoding="utf-8", newline="").write(src)

    subprocess.run([
        browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--window-size=1440,900",
        "--virtual-time-budget=4000",
        "--screenshot=" + dest, "file:///" + TMP.replace("\\", "/"),
    ], capture_output=True)
    if not os.path.exists(dest):
        print("ABORT: no screenshot produced at p=%s" % p)
        sys.exit(1)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    if "--strip" in sys.argv:
        ps = [s.strip() for s in sys.argv[sys.argv.index("--strip") + 1].split(",")]
        from PIL import Image, ImageDraw
        tiles = []
        for p in ps:
            d = os.path.join(OUT, "p_%s.png" % p.replace(".", "_"))
            shot(p, d)
            im = Image.open(d).convert("RGB").crop((450, 90, 990, 810))
            dr = ImageDraw.Draw(im)
            dr.rectangle([0, 0, 96, 26], fill=(0, 0, 0))
            dr.text((8, 8), "p " + p, fill=(240, 210, 140))
            tiles.append(im)
            os.remove(d)
        w, h = tiles[0].size
        strip = Image.new("RGB", (w * len(tiles) + 8 * (len(tiles) - 1), h), (14, 8, 5))
        for i, t in enumerate(tiles):
            strip.paste(t, (i * (w + 8), 0))
        dest = os.path.join(OUT, "chapter4_beats.png")
        strip.save(dest)
        print("wrote %s  (%d frames)" % (dest, len(tiles)))
    else:
        p = sys.argv[sys.argv.index("--p") + 1] if "--p" in sys.argv else "0.95"
        dest = os.path.join(OUT, "chapter4.png")
        shot(p, dest)
        print("wrote %s at p=%s" % (dest, p))

    if os.path.exists(TMP):
        os.remove(TMP)


if __name__ == "__main__":
    main()
