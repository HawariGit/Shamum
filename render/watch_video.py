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

    # Read the whole thing once; these clips are short and seeking per frame is
    # far slower than a single linear decode.
    frames = []
    for i, fr in enumerate(iio.imiter(src, plugin="FFMPEG")):
        t = i / fps
        if t1 is not None and t > t1:
            break
        if t >= t0:
            frames.append((t, fr))
    if not frames:
        print("ABORT: decoded no frames in that range")
        sys.exit(1)
    print("  decoded %d frames, %dx%d" % (len(frames), frames[0][1].shape[1], frames[0][1].shape[0]))

    if "--scan" in sys.argv:
        # Where does the picture actually change? Useful for finding the moment
        # something happens without eyeballing every frame.
        print("\n  biggest changes between consecutive frames:")
        lums = [(t, ImageStat.Stat(Image.fromarray(f).convert("L")).mean[0]) for t, f in frames]
        d = sorted(((abs(lums[i + 1][1] - lums[i][1]), lums[i][0]) for i in range(len(lums) - 1)),
                   reverse=True)[:8]
        for v, t in d:
            print("    t=%6.2fs  delta %.1f" % (t, v))

    pick = [frames[round(i * (len(frames) - 1) / float(max(1, n - 1)))] for i in range(n)]
    thumbs = []
    for k, (t, fr) in enumerate(pick):
        im = Image.fromarray(fr).convert("RGB")
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
