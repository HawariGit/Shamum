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

from PIL import Image, ImageDraw, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
TMP = os.path.join(ROOT, "_rmtest.html")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FLAG = "var heroStill = window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
STILL_P = re.compile(r"var HERO_STILL_P = [\d.]+;")
STILL_T = re.compile(r"var HERO_STILL_T = [^;]+;")
MAC = re.compile(r"var CH4_MAC = [\d.]+;")
MAC_VAL = None
ZOOM_ON = False
COVER_VAL = None


# Injected for sequence renders only. The nav is page chrome, not part of the
# chapter, and in a tall crop it lands right across the raised cap. The particle
# canvas is hidden by the reduced-motion branch but wanted here, and it is safe
# because heroTime advances per frame in this mode.
CLEAN = """<style>
  #nav, #menu-overlay, #scroll-cue, #ch-dots { display: none !important; }
  .reduced-hero #hero-canvas { display: block !important; }
</style>
</head>"""


def browser():
    for b in (CHROME, EDGE):
        if os.path.exists(b):
            return b
    print("ABORT: no Chrome or Edge found")
    sys.exit(1)


def shot(p, dest, t=None):
    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if src.count(FLAG) != 1:
        print("ABORT: heroStill declaration moved; update FLAG")
        sys.exit(1)
    src = src.replace(FLAG, "var heroStill = true;", 1)
    if not STILL_P.search(src):
        print("ABORT: HERO_STILL_P not found")
        sys.exit(1)
    src = STILL_P.sub("var HERO_STILL_P = %s;" % p, src, count=1)
    # A still pins heroTime, so without this every frame of a sequence would
    # share one instant and anything time-driven - the mist drifting, the light
    # band crossing the glass, the surface wobble - would sit perfectly still
    # while only the scroll-driven beats moved. Advancing it per frame is what
    # makes the recording look like the page rather than a slideshow.
    if t is not None:
        if not STILL_T.search(src):
            print("ABORT: HERO_STILL_T not found")
            sys.exit(1)
        src = STILL_T.sub("var HERO_STILL_T = %.4f;" % t, src, count=1)
        if "</head>" not in src:
            print("ABORT: no </head> to inject the recording styles into")
            sys.exit(1)
        src = src.replace("</head>", CLEAN, 1)
    # The camera push-in is switched off in the still on purpose, so the
    # reduced-motion frame stays the composed one that was approved. That also
    # hides it from every preview render, hence this: --zoom neutralises the
    # guard so the beat can actually be looked at.
    if ZOOM_ON:
        g = "var zoomT = heroStill ? 0"
        if g not in src:
            print("ABORT: zoom guard not found"); sys.exit(1)
        src = src.replace(g, "var zoomT = false ? 0", 1)
    # shelfCover is damped from live getBoundingClientRect calls on the strips,
    # so a still can never reach the state where a product strip is covering the
    # scene. --cover pins it, which is the only way to look at that transition.
    if COVER_VAL is not None:
        hook = "  shelfCover += (coverTarget - shelfCover) * Math.min(1, dt * 7.5);"
        if hook not in src:
            print("ABORT: shelfCover hook not found"); sys.exit(1)
        src = src.replace(hook, "  shelfCover = %s;" % COVER_VAL, 1)
    if MAC_VAL is not None:
        if not MAC.search(src):
            print("ABORT: CH4_MAC not found"); sys.exit(1)
        src = MAC.sub("var CH4_MAC = %s;" % MAC_VAL, src, count=1)
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


def shot_guarded(p, dest, t, prev_lum, crop):
    """A capture that fires before the page paints comes back near-black.

    It is not the scene: the same p and heroTime re-render correctly and
    deterministically. It happens roughly once in seventy and it has twice
    nearly been read as a bug in the animation, so every capture is checked.
    Adjacent frames of this chapter move about 4 luminance, so 10 catches the
    misfire without tripping on real motion; after three tries the frame is
    accepted regardless, which is what the one genuine large step - the camera
    arriving - needs.
    """
    im = lum = None
    for _ in range(3):
        shot(p, dest, t)
        im = Image.open(dest).convert("RGB").crop(crop)
        lum = ImageStat.Stat(im.convert("L")).mean[0]
        os.remove(dest)
        if prev_lum is None or abs(lum - prev_lum) <= 10:
            break
        print("    re-shot p=%s: lum %.1f vs %.1f" % (p, lum, prev_lum))
        sys.stdout.flush()
    return im, lum


def main():
    global MAC_VAL, ZOOM_ON
    global COVER_VAL
    if "--cover" in sys.argv:
        COVER_VAL = sys.argv[sys.argv.index("--cover") + 1]
    if "--zoom" in sys.argv:
        ZOOM_ON = True
    if "--mac" in sys.argv:
        MAC_VAL = sys.argv[sys.argv.index("--mac") + 1]
    if "--out" in sys.argv:
        globals()["GIF_NAME"] = sys.argv[sys.argv.index("--out") + 1]
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    if "--strip" in sys.argv:
        ps = [s.strip() for s in sys.argv[sys.argv.index("--strip") + 1].split(",")]
        tiles = []
        prev = None
        for p in ps:
            d = os.path.join(OUT, "p_%s.png" % p.replace(".", "_"))
            im, prev = shot_guarded(p, d, 3.4091, prev, (330, 60, 1110, 830))
            dr = ImageDraw.Draw(im)
            dr.rectangle([0, 0, 96, 26], fill=(0, 0, 0))
            dr.text((8, 8), "p " + p, fill=(240, 210, 140))
            tiles.append(im)
        w, h = tiles[0].size
        strip = Image.new("RGB", (w * len(tiles) + 8 * (len(tiles) - 1), h), (14, 8, 5))
        for i, t in enumerate(tiles):
            strip.paste(t, (i * (w + 8), 0))
        dest = os.path.join(OUT, "chapter4_beats.png")
        strip.save(dest)
        print("wrote %s  (%d frames)" % (dest, len(tiles)))
    elif "--gif" in sys.argv:
        n = int(sys.argv[sys.argv.index("--frames") + 1]) if "--frames" in sys.argv else 72
        p0, p1 = 0.882, 0.999
        fps = 18.0
        crop = (395, 60, 1045, 830)
        scale = 0.64
        frames = []
        prev_lum = None
        for i in range(n):
            p = p0 + (p1 - p0) * i / float(n - 1)
            # heroTime advances at real playback rate, offset from the still's
            # own base so floor 4 is not caught on the axe-swing zero.
            t = 3.4091 + i / fps
            d = os.path.join(OUT, "_gif_%03d.png" % i)
            # One screenshot in ~70 fires before the page has painted and comes
            # back near-black. It is not a bug in the scene - the same p and
            # heroTime re-render correctly and deterministically - so the frame
            # is simply taken again. Adjacent frames of this animation never
            # move more than about 4 luminance, so 10 catches the misfire
            # without ever tripping on real motion.
            im, lum = shot_guarded("%.5f" % p, d, t, prev_lum, crop)
            prev_lum = lum
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
            frames.append(im)
            # flush: stdout is a pipe when this runs in the background, so
            # without it 4 minutes of progress buffers and the run looks dead
            print("  frame %2d/%d  p=%.4f  lum=%.1f" % (i + 1, n, p, lum))
            sys.stdout.flush()

        # One palette for the whole sequence. Quantising each frame on its own
        # gives every frame a slightly different set of browns, and the scene is
        # almost entirely browns - the result flickers.
        step = max(1, len(frames) // 8)
        sample = frames[::step]
        mont = Image.new("RGB", (frames[0].width * len(sample), frames[0].height))
        for i, f in enumerate(sample):
            mont.paste(f, (i * frames[0].width, 0))
        master = mont.quantize(colors=255, method=Image.MEDIANCUT)
        out = [f.quantize(palette=master, dither=Image.FLOYDSTEINBERG) for f in frames]
        durs = [int(1000 / fps)] * len(out)
        durs[-1] = 1100          # hold on the finished bottle before looping
        durs[0] = 700
        dest = os.path.join(OUT, globals().get("GIF_NAME", "chapter4.gif"))
        out[0].save(dest, save_all=True, append_images=out[1:], loop=0,
                    duration=durs, optimize=True, disposal=1)
        print("wrote %s  (%d frames, %.1f MB)"
              % (dest, len(out), os.path.getsize(dest) / 1048576.0))

    else:
        p = sys.argv[sys.argv.index("--p") + 1] if "--p" in sys.argv else "0.95"
        dest = os.path.join(OUT, "chapter4.png")
        shot(p, dest, 3.4091)
        print("wrote %s at p=%s" % (dest, p))

    if os.path.exists(TMP):
        os.remove(TMP)


if __name__ == "__main__":
    main()
