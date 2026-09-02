"""Screenshot the page at a list of scroll offsets, so it can be looked at.

Headless Chrome's --screenshot only captures the viewport at load, and this page
cannot simply be given a 12000px window because the hero is sized in vh. So each
shot is a temporary copy with a load handler that scrolls to the offset first,
and --virtual-time-budget lets it settle before the capture.

    python render/page_shots.py --at 3000,6000,9000
    python render/page_shots.py --sections          # every named section

Uses the reduced-motion build so the 1175vh hero collapses to one screen and the
rest of the page is reachable in a handful of shots. That is a fair view of
everything BELOW the hero; it is not how the hero itself looks.
"""

import io
import os
import re
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out", "page")
TMP = os.path.join(ROOT, "_rmtest.html")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FLAG = "var heroStill = window.matchMedia('(prefers-reduced-motion: reduce)').matches;"

W, H = 1440, 900


def browser():
    for b in (CHROME, EDGE):
        if os.path.exists(b):
            return b
    print("ABORT: no Chrome or Edge found")
    sys.exit(1)


def shot(dest, by_id):
    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if src.count(FLAG) != 1:
        print("ABORT: heroStill declaration moved")
        sys.exit(1)
    src = src.replace(FLAG, "var heroStill = true;", 1)
    # NO SCROLLING. window.scrollTo from an injected load handler never landed
    # here - every shot came back as the top of the page - and chasing the timing
    # against --virtual-time-budget is not worth it. Instead the target section is
    # made the only visible child of body, so it renders at the top of an
    # unscrolled viewport. No timing dependency at all.
    #
    # .reveal starts at opacity 0 and is un-hidden by IntersectionObserver, which
    # does not fire here; its CSS fallback sits behind the real
    # prefers-reduced-motion media query, which headless does not report however
    # heroStill is set. Without that override every shot is an empty dark frame.
    # Isolation used to be `body > *{display:none} body > #id{display:block}`,
    # which silently produced an empty frame for anything NOT a direct child of
    # body. The product strips live inside #hero-track, so shelf-bukhoor was in
    # SECTIONS returning a blank 5KB shot on every run. This walks up from the
    # target instead, hiding siblings at each level, so any depth works.
    inject = ("<style>"
              ".reveal,.reveal-scale{opacity:1!important;transform:none!important;"
              "filter:none!important;transition:none!important}"
              ".word{opacity:1!important;filter:none!important;transform:none!important}"
              "#veil,#nav,#menu-overlay,#scroll-cue,#ch-dots{display:none!important}"
              "</style>"
              "<script>(function(){"
              "var t=document.getElementById(%r);"
              "if(!t){document.title='ABSENT';return;}"
              "var n=t;"
              "while(n&&n!==document.body){"
              "  var pa=n.parentNode;"
              "  for(var i=0;i<pa.children.length;i++){"
              "    if(pa.children[i]!==n) pa.children[i].style.display='none';"
              "  }"
              "  n.style.display='block';"
              "  n.style.position='static';"   # a sticky ancestor would still offset it
              "  n.style.height='auto';"
              "  n=pa;"
              "}"
              "})();</script>") % by_id
    if "</body>" not in src:
        print("ABORT: no </body>")
        sys.exit(1)
    src = src.replace("</body>", inject + "</body>", 1)
    io.open(TMP, "w", encoding="utf-8", newline="").write(src)

    subprocess.run([
        browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H),
        "--virtual-time-budget=5000", "--screenshot=" + dest,
        "file:///" + TMP.replace("\\", "/"),
    ], capture_output=True)
    return os.path.exists(dest)


SECTIONS = ["shelf-bukhoor", "brand-statement", "ritual", "essence",
            "quote-section", "scent-life", "trust", "loyalty", "footer"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))

    jobs = []
    if "--sections" in sys.argv:
        jobs = [(None, s) for s in SECTIONS]
    elif "--at" in sys.argv:
        jobs = [(int(v), None) for v in sys.argv[sys.argv.index("--at") + 1].split(",")]
    else:
        jobs = [(None, s) for s in SECTIONS]

    made = []
    for i, (px, sid) in enumerate(jobs):
        name = sid or ("y%d" % px)
        d = os.path.join(OUT, "%02d_%s.png" % (i, name))
        if shot(d, sid):
            made.append((name, d))
            print("  %s" % name)
            sys.stdout.flush()
        else:
            print("  %s  FAILED" % name)

    if os.path.exists(TMP):
        os.remove(TMP)

    # contact sheet so the whole page can be taken in at once
    if made:
        th = []
        for name, d in made:
            im = Image.open(d).convert("RGB")
            im.thumbnail((430, 430), Image.LANCZOS)
            th.append(im)
        cols = 3
        rows = (len(th) + cols - 1) // cols
        w, h = th[0].size
        sheet = Image.new("RGB", (w * cols + 6 * (cols - 1), h * rows + 6 * (rows - 1)),
                          (14, 8, 5))
        for k, im in enumerate(th):
            sheet.paste(im, ((k % cols) * (w + 6), (k // cols) * (h + 6)))
        sheet.save(os.path.join(OUT, "_contact.png"))
        print("wrote %d shots + contact sheet" % len(made))


if __name__ == "__main__":
    main()
