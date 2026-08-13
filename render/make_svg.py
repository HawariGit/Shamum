"""Emit the finished <svg> block for one Arabic headline."""
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc.transform import Transform

FONT = r"C:\Windows\Fonts\arabtype.ttf"
UPM_TARGET = 100.0
PAD = 6.0


def shape(text):
    with open(FONT, "rb") as f:
        data = f.read()
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.direction = "rtl"
    buf.script = "Arab"
    buf.language = "ar"
    hb.shape(font, buf)
    return buf.glyph_infos, buf.glyph_positions, face.upem


def build(text):
    infos, positions, upem = shape(text)
    tt = TTFont(FONT)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = UPM_TARGET / upem

    x = y = 0.0
    items = []
    for info, pos in zip(infos, positions):
        gname = order[info.codepoint]
        t = Transform(scale, 0, 0, -scale,
                      (x + pos.x_offset) * scale,
                      (y + pos.y_offset) * -scale)
        bp = BoundsPen(gs)
        gs[gname].draw(TransformPen(bp, t))
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}")
        gs[gname].draw(TransformPen(pen, t))
        d = pen.getCommands().strip()
        if d and bp.bounds:
            items.append({"d": d, "b": bp.bounds, "x": (x + pos.x_offset) * scale})
        x += pos.x_advance
        y += pos.y_advance

    xs0 = min(i["b"][0] for i in items); ys0 = min(i["b"][1] for i in items)
    xs1 = max(i["b"][2] for i in items); ys1 = max(i["b"][3] for i in items)
    vb = (xs0 - PAD, ys0 - PAD, (xs1 - xs0) + 2 * PAD, (ys1 - ys0) + 2 * PAD)

    # writing order: rightmost glyph first
    for i, it in enumerate(sorted(items, key=lambda k: -k["x"])):
        it["i"] = i

    lines = []
    for it in items:
        # pathLength normalises every glyph so a dot and a long sweep draw at
        # the same rate; without it the short contours snap instantly.
        lines.append(
            f'    <path class="ac-g" pathLength="100" style="--i:{it["i"]}" d="{it["d"]}"/>'
        )
    return vb, len(items), "\n".join(lines)


if __name__ == "__main__":
    text = sys.argv[1]
    cls = sys.argv[2]
    vb, n, paths = build(text)
    print(f'<svg class="arabic-calli {cls}" viewBox="{vb[0]:.1f} {vb[1]:.1f} '
          f'{vb[2]:.1f} {vb[3]:.1f}" style="--n:{n}" '
          f'preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">')
    print(paths)
    print("</svg>")
