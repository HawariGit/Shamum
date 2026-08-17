"""
Build the social preview card: assets/og-image.jpg, 1200x630.

Why this exists: og:image pointed at a Zid CDN URL the house does not
control. If that path rotates or the product is delisted, every shared link
silently loses its preview — WhatsApp, Instagram DM, X, Slack. This renders
a card from assets we own.

Arabic note: Pillow reports raqm=False on this machine, so its text layout
cannot shape Arabic — it would draw isolated, unjoined letters left to
right. So the Arabic line is shaped with harfbuzz (same path as
make_svg.py), the glyph outlines are pulled with fontTools, the curves are
flattened to polygons here, and Pillow fills those directly. Latin text goes
through the normal text engine, which handles it fine.

Run: python render/make_og.py
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

W, H = 1200, 630
OUT = "assets/og-image.jpg"
PHOTO = "assets/ig-bukhoor.webp"
MARK = "assets/logo-mark.png"
AR_FONT = r"C:\Windows\Fonts\arabtype.ttf"
SERIF = r"C:\Windows\Fonts\georgia.ttf"
SANS = r"C:\Windows\Fonts\segoeui.ttf"

INK = (21, 16, 10)
OUD = (36, 24, 16)
GOLD_400 = (194, 163, 104)
GOLD_500 = (174, 139, 79)
SAND_50 = (251, 246, 234)


# ─────────────────── Arabic: shape, outline, flatten ───────────────────
class PolyPen(BasePen):
    """Collects contours as flat point lists, subdividing curves."""

    def __init__(self, glyphSet, steps=12):
        super().__init__(glyphSet)
        self.steps = steps
        self.contours = []
        self._cur = []

    def _moveTo(self, pt):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self._cur.append((
                u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
                u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self._cur.append((
                u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
                u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))

    def _closePath(self):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = []

    def done(self):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        return self.contours


def arabic_contours(text, px):
    """Shaped, outlined, y-down contours for one Arabic line at px height."""
    with open(AR_FONT, "rb") as f:
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

    tt = TTFont(AR_FONT)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = px / face.upem

    out, x, y = [], 0.0, 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gname = order[info.codepoint]
        t = Transform(scale, 0, 0, -scale,
                      (x + pos.x_offset) * scale,
                      (y + pos.y_offset) * -scale)
        pen = PolyPen(gs)
        gs[gname].draw(TransformPen(pen, t))
        out.extend(pen.done())
        x += pos.x_advance
        y += pos.y_advance
    return out


def draw_arabic(img, text, px, cy, fill):
    """Centre a shaped Arabic line horizontally at vertical centre cy."""
    contours = arabic_contours(text, px)
    if not contours:
        return
    xs = [p[0] for c in contours for p in c]
    ys = [p[1] for c in contours for p in c]
    ox = (W - (max(xs) - min(xs))) / 2 - min(xs)
    oy = cy - (min(ys) + max(ys)) / 2

    # Supersample so the flattened outlines get clean edges.
    S = 4
    layer = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(layer)
    for c in contours:
        d.polygon([((p[0] + ox) * S, (p[1] + oy) * S) for p in c], fill=255)
    mask = layer.resize((W, H), Image.LANCZOS)
    img.paste(Image.new("RGB", (W, H), fill), (0, 0), mask)


# ─────────────────────────── compose ───────────────────────────
def main():
    card = Image.new("RGB", (W, H), INK)

    # vertical wash INK -> OUD -> INK
    grad = Image.new("RGB", (1, H))
    gp = grad.load()
    for y in range(H):
        t = abs((y / H) - 0.5) * 2          # 0 centre, 1 edges
        gp[0, y] = tuple(int(OUD[i] + (INK[i] - OUD[i]) * t) for i in range(3))
    card = grad.resize((W, H), Image.BILINEAR)

    # the bukhoor photo as atmosphere: blurred hard, held right, faded back
    if os.path.exists(PHOTO):
        ph = Image.open(PHOTO).convert("RGB")
        s = max(W / ph.width, H / ph.height) * 1.25
        ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
        ph = ph.crop((ph.width - W, max(0, (ph.height - H) // 2),
                      ph.width, max(0, (ph.height - H) // 2) + H))
        ph = ph.filter(ImageFilter.GaussianBlur(26))
        # fade it out toward the left so type sits on clean ground
        fade = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(fade)
        for x in range(W):
            fd.line([(x, 0), (x, H)], fill=int(150 * max(0.0, (x / W - 0.22) / 0.78) ** 1.4))
        card = Image.composite(ph, card, fade)

    # vignette
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-W * 0.35, -H * 0.5, W * 1.35, H * 1.5), fill=190)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    card = Image.composite(card, Image.new("RGB", (W, H), INK), vig)

    d = ImageDraw.Draw(card)

    # logo mark
    if os.path.exists(MARK):
        m = Image.open(MARK).convert("RGBA")
        mh = 74
        m = m.resize((int(m.width * mh / m.height), mh), Image.LANCZOS)
        card.paste(m, ((W - m.width) // 2, 96), m)

    f_name = ImageFont.truetype(SERIF, 78)
    f_sub = ImageFont.truetype(SANS, 21)
    f_foot = ImageFont.truetype(SANS, 17)

    def centred(text, font, y, fill, tracking=0):
        widths = [d.textlength(ch, font=font) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=font, fill=fill)
            x += w + tracking

    centred("SHAMUM", f_name, 196, SAND_50, tracking=13)
    centred("MAISON D'OUD", f_sub, 300, GOLD_400, tracking=7)

    # gold rule
    d.line([(W / 2 - 150, 348), (W / 2 + 150, 348)], fill=GOLD_500, width=1)

    # Arabic tagline — shaped, not laid out by Pillow
    draw_arabic(card, "عبـقُ العطــر الأصيــل", 62, 412, GOLD_400)

    d.line([(W / 2 - 150, 470), (W / 2 + 150, 470)], fill=GOLD_500, width=1)
    centred("SULTANATE OF OMAN  ·  EST. 2010", f_foot, 500, (150, 128, 92), tracking=6)

    os.makedirs("assets", exist_ok=True)
    card.save(OUT, "JPEG", quality=88, optimize=True, progressive=True)
    kb = os.path.getsize(OUT) / 1024
    print("wrote %s  %dx%d  %.1f KB" % (OUT, W, H, kb))


main()
