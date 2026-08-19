"""Render the chapter IV flacon to a PNG so it can actually be looked at.

The browser pane in this environment never composites, so screenshots of the
live page always fail and every check has had to be geometry and content
probes. This lifts the real <svg id="hero-svg-scene"> out of index.html with
its real gradients, parks the camera on floor 4, sets the floor-4 elements to
the state heroLoop puts them in at p just before the atomizer press, and
screenshots it with headless Chrome.

    python render/preview_flacon.py            # -> render/out/flacon.png
    python render/preview_flacon.py --fill 0.5 # half full

Nothing here is served or committed; the harness is written to render/out/,
which .vercelignore already excludes.
"""

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Floor 4 spans y 2700-3600 in the world; the camera sits at -2700 there.
CAM = 2700
FILL_FLOOR = 3328.0
FILL_RANGE = 290.0


def main():
    fill = 1.0
    if "--fill" in sys.argv:
        fill = float(sys.argv[sys.argv.index("--fill") + 1])

    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

    m = re.search(r'<svg id="hero-svg-scene".*?</svg>', src, re.S)
    if not m:
        print("ABORT: could not find the hero scene svg")
        sys.exit(1)
    svg = m.group(0)
    # The harness lives in render/out/, so the page-relative asset paths would
    # resolve under that directory and the logo mark would render as a broken
    # image glyph. Point them back at the repo root.
    svg = svg.replace('href="assets/', 'href="file:///%s/assets/'
                      % ROOT.replace("\\", "/"))

    level = FILL_FLOOR - fill * FILL_RANGE

    # The state heroLoop leaves floor 4 in once the bottle has settled
    # (f4in = 1) and the fill has completed, just before the press at 0.952.
    state = """
<script>
  var S = function(id){ return document.getElementById(id); };
  S('world').setAttribute('transform', 'translate(0,-%d)');
  [['f4-glow',1],['f4-rays',0.6],['f4-halo',0.85]].forEach(function(p){
    if (S(p[0])) S(p[0]).setAttribute('opacity', p[1]);
  });
  S('f4-liquid').setAttribute('y', %.1f);
  S('f4-liquid').setAttribute('height', %.1f);
  S('f4-surface').setAttribute('cy', %.1f);
  S('f4-surface').setAttribute('opacity', %s);
  S('f4-shimmer').setAttribute('opacity', 0.9);
  S('f4-shimmer').setAttribute('x', 700);
</script>""" % (CAM, level, max(0.0, 3330.0 - level), level,
                "0.72" if fill > 0.02 else "0")

    html = ("""<!doctype html><meta charset="utf-8">
<style>
  html,body{margin:0;background:#0F0805;}
  #frame{position:relative;width:1440px;height:900px;overflow:hidden;background:#0F0805;}
  #frame svg{position:absolute;inset:0;width:100%;height:100%;}
  #frame::after{content:'';position:absolute;inset:0;pointer-events:none;
    background:radial-gradient(ellipse 115% 90% at 50% 44%,transparent 52%,rgba(4,2,0,0.62) 100%);}
</style>
<div id="frame">""" + svg + "</div>" + state)

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    harness = os.path.join(OUT, "flacon.html")
    io.open(harness, "w", encoding="utf-8", newline="").write(html)

    png = os.path.join(OUT, "flacon.png")
    if os.path.exists(png):
        os.remove(png)

    browser = CHROME if os.path.exists(CHROME) else EDGE
    cmd = [browser, "--headless", "--disable-gpu", "--hide-scrollbars",
           "--force-device-scale-factor=1",
           "--screenshot=" + png, "--window-size=1440,900",
           "--virtual-time-budget=4000",
           "file:///" + harness.replace("\\", "/")]
    subprocess.run(cmd, capture_output=True, timeout=120)

    if os.path.exists(png):
        print("wrote %s (%d bytes), fill=%.2f level=%.1f"
              % (png, os.path.getsize(png), fill, level))
    else:
        print("ABORT: chrome produced no screenshot")
        sys.exit(1)


if __name__ == "__main__":
    main()
