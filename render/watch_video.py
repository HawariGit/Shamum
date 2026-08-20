"""Let Claude look at a video, by turning it into frames it can actually see.

Video does not reach the model as video - only images do. This decodes a file
with the ffmpeg that imageio-ffmpeg bundles (inside site-packages, not on the
system PATH) and writes frames that can be opened with the Read tool, plus a
contact sheet for a quick overview.

    python render/watch_video.py clip.mp4                 # 12 frames + sheet
    python render/watch_video.py clip.mp4 --n 24          # more frames
    python render/watch_video.py clip.mp4 --from 3 --to 7 # just 3s-7s
    python render/watch_video.py clip.mp4 --scan          # find sudden changes

Frames land in render/out/video/. That directory is inside render/out/, which is
already in .gitignore and .vercelignore, so nothing here can be committed or
published by accident.
"""

import os
import sys

import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "video")


def arg(name, cast=str, default=None):
    if name in sys.argv:
        return cast(sys.argv[sys.argv.index(name) + 1])
    return default


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("--")
             and not (sys.argv.index(a) > 0 and sys.argv[sys.argv.index(a) - 1].startswith("--"))]
    if not paths:
        print("usage: python render/watch_video.py <file> [--n 12] [--from s] [--to s] [--scan]")
        sys.exit(1)
    src = paths[0]
    if not os.path.exists(src):
        print("ABORT: no such file: %s" % src)
        sys.exit(1)

    meta = iio.immeta(src, plugin="FFMPEG")
    fps = float(meta.get("fps") or 25)
    dur = float(meta.get("duration") or 0)
    print("%s\n  %.2fs @ %.2f fps" % (src, dur, fps))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))

    t0 = arg("--from", float, 0.0)
    t1 = arg("--to", float, dur if dur else None)
    n = arg("--n", int, 12)

    # STREAM, do not accumulate. A 42s 1080x1920 phone clip is 7.8 GB of raw
    # RGB, so holding every frame in order to pick twelve of them exhausts
    # memory. The wanted indices are worked out from the duration up front, and
    # every other frame is measured for --scan and dropped on the same pass.
    lo = int(round(t0 * fps))
    hi = int(round((t1 if t1 is not None else dur) * fps))
    span = max(1, hi - lo)
    want = {lo + int(round(k * (span - 1) / float(max(1, n - 1)))) for k in range(n)}

    kept, lums = [], []
    for i, fr in enumerate(iio.imiter(src, plugin="FFMPEG")):
        if i > hi:
            break
        if i < lo:
            continue
        im = Image.fromarray(fr)
        if "--scan" in sys.argv:
            small = im.convert("L")
            small.thumbnail((160, 160), Image.NEAREST)
            lums.append((i / fps, ImageStat.Stat(small).mean[0]))
        if i in want:
            kept.append((i / fps, im.convert("RGB").copy()))
        del im
    if not kept:
        print("ABORT: decoded no frames in that range")
        sys.exit(1)
    print("  kept %d of ~%d frames in range, %dx%d"
          % (len(kept), span, kept[0][1].width, kept[0][1].height))

    if lums:
        # Where does the picture actually change? Finds the moment something
        # happens without stepping through everything.
        print("\n  biggest changes between consecutive frames:")
        d = sorted(((abs(lums[j + 1][1] - lums[j][1]), lums[j][0]) for j in range(len(lums) - 1)),
                   reverse=True)[:8]
        for v, t in d:
            print("    t=%6.2fs  delta %.1f" % (t, v))

    pick = kept
    thumbs = []
    for k, (t, im) in enumerate(pick):
        p = os.path.join(OUT, "f%02d_%06.2fs.png" % (k, t))
        im.save(p)
        th = im.copy()
        th.thumbnail((300, 300), Image.LANCZOS)
        d = ImageDraw.Draw(th)
        d.rectangle([0, 0, 62, 14], fill=(0, 0, 0))
        d.text((3, 3), "%.2fs" % t, fill=(240, 210, 140))
        thumbs.append(th)

    cols = min(4, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    w, h = thumbs[0].size
    sheet = Image.new("RGB", (w * cols + 4 * (cols - 1), h * rows + 4 * (rows - 1)), (14, 8, 5))
    for k, th in enumerate(thumbs):
        sheet.paste(th, ((k % cols) * (w + 4), (k // cols) * (h + 4)))
    sheet_path = os.path.join(OUT, "_contact.png")
    sheet.save(sheet_path)

    print("\n  wrote %d full frames + %s" % (len(pick), sheet_path))
    print("  open the contact sheet first, then any single frame by name.")


if __name__ == "__main__":
    main()
