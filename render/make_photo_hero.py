# -*- coding: utf-8 -*-
"""Build proto-photo.html: the hero rebuilt on the brand's own photography.

Everything is inlined as data URIs so the file behaves identically from disk,
from the dev server, and as a published Artifact.
"""
import base64, io, os, random
from PIL import Image

ROOT = r"C:\onedrive\Shm"
A = os.path.join(ROOT, "assets")


def durl(path, maxw=1600, q=82):
    im = Image.open(path).convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def pngurl(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


# Monochrome grain tile. Real grain is the cheapest thing that separates a
# photographic surface from a flat digital one, and it hides the banding heavy
# dark gradients produce on 8-bit displays.
random.seed(7)
g = Image.new("L", (128, 128))
g.putdata([int(max(0, min(255, random.gauss(128, 26)))) for _ in range(128 * 128)])
gb = io.BytesIO()
g.save(gb, "PNG", optimize=True)
GRAIN = "data:image/png;base64," + base64.b64encode(gb.getvalue()).decode()

# NOTE ON FRAMING: every source is ~711x891 portrait and the stage is
# landscape. `cover` therefore scales to WIDTH and crops vertically, which means
# the x half of object-position has NO EFFECT - the subject is always centred
# horizontally and always fills the width. Only the y value does anything, and
# it is the only framing control there is. Type placement has to work around
# that, not against it. Proper landscape crops from the photographer would
# remove the constraint entirely.
IMG = {n: durl(os.path.join(A, n + ".webp")) for n in
       ["ig-ritual", "ig-bukhoor", "ig-decanter", "ig-box-open", "ig-box-closed"]}
LOGO = pngurl(os.path.join(A, "logo-full.png"))

FRAMES = [
    ("ig-ritual", "", "", "", "", "58% 42%", "", 0.70, (34, 50, "center")),
    ("ig-box-closed", u"Chapter I \u00b7 The Tree", "",
     u"From a tree that keeps its own time",
     u"Agarwood gives nothing up quickly. The resin forms only where the tree "
     u"has been wounded, and only over years.",
     "42% 62%",
     u"Placeholder \u2014 the one photograph the house does not have", 0.74, (50, 33, "center")),
    ("ig-bukhoor", u"Chapter II \u00b7 The Mabkhara",
     u"\u0623\u062e\u0634\u0640\u0627\u0628 \u0627\u0644\u0639\u0640\u0648\u062f",
     u"The Bukhoor",
     u"Resin-dark heartwood over live coal \u2014 burned as it has been for "
     u"generations.", "52% 48%", "", 0.66, (33, 44, "left")),
    ("ig-decanter", u"Chapter III \u00b7 The Distillation",
     u"\u0623\u062f\u0647\u0640\u0627\u0646 \u0627\u0644\u0639\u0640\u0648\u062f",
     u"The Oil",
     u"One drop, drawn by patience. Pure dehn al oud, undiluted.",
     "50% 56%", "", 0.95, (50, 50, "center")),
    ("ig-box-open", u"Chapter IV \u00b7 The House",
     u"\u0627\u0644\u0628\u0640\u062e\u0640\u0627\u062e\u0640\u0627\u062a",
     u"The Perfume",
     u"Where the journey of the wood becomes a signature.", "50% 20%", "", 0.58, (50, 26, "center")),
]

plates, texts, dots = [], [], []
for i, (k, eb, ar, hd, sub, focal, note, expo, pos) in enumerate(FRAMES):
    plates.append('<div class="plate"><img src="%s" alt="" style="object-position:%s;'
                  'filter:brightness(%.2f) contrast(1.06) saturate(0.88)"></div>'
                  % (IMG[k], focal, expo))
    if i == 0:
        texts.append('<div class="ct" style="left:%d%%;top:%d%%;text-align:%s">'
                     '<img class="opening-logo" src="%s" alt="SHAMUM">'
                     '<span class="opening-tag">The Scent of an Authentic Perfume</span></div>'
                     % (pos[0], pos[1], pos[2], LOGO))
    else:
        bits = ['<div class="ct" style="left:%d%%;top:%d%%;text-align:%s">'
                % (pos[0], pos[1], pos[2])]
        if eb:
            bits.append('<span class="eb">%s</span>' % eb)
        if ar:
            bits.append('<span class="ar" lang="ar">%s</span>' % ar)
        if hd:
            bits.append('<h2 class="hd">%s</h2>' % hd)
        if sub:
            bits.append('<p class="sub">%s</p>' % sub)
        if note:
            bits.append('<span class="note">%s</span>' % note)
        bits.append('</div>')
        texts.append("".join(bits))
    dots.append('<span class="dot"></span>')

TPL = u"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shamum, Photographed</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Jost:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{
  --gold-400:#C2A368; --gold-300:#D4BC86; --sand-50:#FBF6EA;
}
*{box-sizing:border-box}
html{scroll-behavior:auto}
body{margin:0;background:#0B0705;color:var(--sand-50);
     font-family:'Jost',sans-serif;-webkit-font-smoothing:antialiased}

#track{position:relative}
#stage{position:sticky;top:0;height:100vh;overflow:hidden;background:#0B0705}

/* ---- photographic plates -------------------------------------------- */
.plate{position:absolute;inset:0;opacity:0;will-change:opacity,transform}
.plate img{width:100%;height:100%;object-fit:cover;display:block}
/* Exposure is set PER PLATE, inline. These five photographs are not lit alike -
   the bukhoor is a bright smoke plume, the decanter is a dark panelled wall -
   and one shared brightness either crushed the dark ones to mud or blew out the
   bright ones. Graded individually the way a colourist would. */

#grade{position:absolute;inset:0;pointer-events:none;z-index:3;
  background:
    radial-gradient(ellipse 120% 88% at 50% 46%, transparent 46%, rgba(6,3,1,0.68) 100%),
    linear-gradient(to bottom, rgba(8,4,2,0.55) 0%, transparent 28%, transparent 64%, rgba(6,3,1,0.78) 100%),
    radial-gradient(ellipse 90% 70% at 50% 55%, rgba(150,104,42,0.13), transparent 70%)}

/* No blend mode on purpose: screen-blending over near-black is invisible, and
   a blended full-screen layer forces everything beneath it to recomposite
   every frame, which a scroll-driven page cannot spare. */
#grain{position:absolute;inset:0;pointer-events:none;z-index:4;opacity:0.16;
  background-image:url(GRAIN_URL);background-size:128px 128px}

/* ---- type ------------------------------------------------------------ */
.ct{position:absolute;transform:translate(-50%,-50%);
  width:min(86vw,560px);max-width:86vw;overflow-wrap:break-word;z-index:6;opacity:0;
  pointer-events:none;will-change:opacity,transform,filter}
/* Placement is set PER FRAME, inline. Centring every caption regardless of the
   photograph under it is the thing that makes a set of images look templated:
   the bukhoor's smoke fills the upper right and its left side is empty, the
   decanter is dead symmetrical and wants centre, the boxes sit low and want the
   type above them. Each block is placed against its own picture. */
.ct[style*="text-align:left"] .sub{margin-left:0}
.eb{font-size:10px;letter-spacing:0.34em;text-transform:uppercase;
  color:var(--gold-400);display:block;margin-bottom:14px}
.ar{font-family:'Cormorant Garamond',serif;font-size:clamp(28px,3.6vw,46px);
  color:var(--gold-300);direction:rtl;display:block;line-height:1.25}
.hd{font-family:'Cormorant Garamond',serif;font-weight:300;font-style:italic;
  font-size:clamp(34px,4.6vw,64px);line-height:1.08;margin:4px 0 0}
.sub{font-size:13px;font-weight:300;letter-spacing:0.05em;line-height:1.8;
  color:rgba(244,234,210,0.74);margin:18px auto 0;max-width:min(430px,100%)}
.note{display:inline-block;margin-top:24px;padding:6px 12px;font-size:9px;
  letter-spacing:0.2em;text-transform:uppercase;color:#E2B15C;
  border:1px solid rgba(226,177,92,0.42);border-radius:2px}
.opening-logo{width:clamp(230px,26vw,340px);display:block;margin:0 auto 20px;
  filter:invert(1) sepia(1) saturate(2.4) hue-rotate(-14deg) brightness(1.06)}
.opening-tag{font-size:10px;letter-spacing:0.42em;text-transform:uppercase;
  color:var(--gold-400)}

#dots{position:fixed;right:26px;top:50%;transform:translateY(-50%);z-index:20;
  display:flex;flex-direction:column;gap:11px}
.dot{width:5px;height:5px;border-radius:50%;background:rgba(244,234,210,0.26);
  transition:background .4s,transform .4s}
.dot.on{background:var(--gold-300);transform:scale(1.55)}
#cue{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);z-index:20;
  font-size:9px;letter-spacing:0.3em;text-transform:uppercase;
  color:rgba(244,234,210,0.5)}

@media (max-width:900px){
  /* No room to art-direct placement on a phone - everything returns to centre
     and the photographs are framed on their subject instead. */
  .ct{left:50% !important;top:48% !important;text-align:center !important;
      width:88vw}
  .sub{margin-left:auto !important}
}
@media (max-width:640px){ #dots{right:12px} .sub{font-size:12px} }
@media (prefers-reduced-motion:reduce){ .plate{transform:none !important} }
</style>

<div id="track">
  <div id="stage">
    PLATES
    <div id="grade"></div>
    <div id="grain"></div>
    TEXTS
  </div>
</div>
<div id="dots">DOTS</div>
<div id="cue">Scroll</div>

<script>
(function(){
  var N = NFRAMES;
  var track  = document.getElementById('track');
  var plates = [].slice.call(document.querySelectorAll('.plate'));
  var texts  = [].slice.call(document.querySelectorAll('.ct'));
  var dots   = [].slice.call(document.querySelectorAll('.dot'));
  var cue    = document.getElementById('cue');
  var still  = matchMedia('(prefers-reduced-motion: reduce)').matches;

  track.style.height = (N * 118 + 40) + 'vh';

  function clamp(v,a,b){ return v<a?a:(v>b?b:v); }
  function sstep(t){ t=clamp(t,0,1); return t*t*(3-2*t); }

  var sp=0, sv=0, raw=0, ticking=false;

  function progress(){
    var r = track.getBoundingClientRect();
    var total = track.offsetHeight - window.innerHeight;
    return total > 0 ? clamp(-r.top/total, 0, 1) : 0;
  }

  function paint(p){
    var f = p * (N - 1);
    for (var i = 0; i < N; i++){
      var d = Math.abs(f - i);
      // Frames overlap across one full step, so one is always arriving as
      // another leaves and the stage is never empty.
      plates[i].style.opacity = sstep(clamp(1 - d, 0, 1));
      // Ken Burns across each plate's own dwell. Small and slow: the moment it
      // is noticeable it reads as a slideshow effect rather than a camera.
      var local = clamp(f - i + 0.5, 0, 1);
      plates[i].style.transform = still ? '' :
        'scale(' + (1.045 + local*0.075).toFixed(4) + ') translate3d(0,'
        + ((0.5 - local)*1.6).toFixed(2) + '%,0)';

      // Type arrives after its plate and leaves before it, so the words are
      // never themselves being cross-faded - that is what makes a dissolve
      // look cheap.
      var a = sstep(clamp((f - i + 0.62)/0.34, 0, 1))
            * (1 - sstep(clamp((f - i - 0.30)/0.32, 0, 1)));
      var t = texts[i];
      t.style.opacity = a;
      t.style.filter = 'blur(' + ((1-a)*7).toFixed(2) + 'px)';
      t.style.transform = 'translate(-50%,-50%) translateY(' + ((1-a)*20).toFixed(1) + 'px)';
      dots[i].className = 'dot' + (Math.round(f) === i ? ' on' : '');
    }
    cue.style.opacity = 1 - clamp(p*14, 0, 1);
  }

  function loop(){
    if (still){ paint(raw); ticking=false; return; }
    // Critically damped spring, so plates ease rather than tracking the wheel
    // one to one. Same idea as the production hero.
    sv += ((raw - sp)*62 - sv*16) * 0.016;
    sp += sv * 0.016;
    if (!isFinite(sp)){ sp = raw; sv = 0; }
    paint(clamp(sp,0,1));
    if (Math.abs(raw-sp) > 0.0002 || Math.abs(sv) > 0.0002) requestAnimationFrame(loop);
    else ticking = false;
  }

  function onScroll(){
    raw = progress();
    if (!ticking){ ticking = true; requestAnimationFrame(loop); }
  }

  addEventListener('scroll', onScroll, {passive:true});
  addEventListener('resize', onScroll);
  raw = sp = progress();
  paint(sp);
  // Manual stepping, for headless stills - rAF does not run in some harnesses.
  window.__protoPaint = function(p){ raw = sp = p; sv = 0; paint(p); };
})();
</script>
"""

HTML = (TPL.replace("PLATES", "\n    ".join(plates))
           .replace("TEXTS", "\n    ".join(texts))
           .replace("DOTS", "".join(dots))
           .replace("GRAIN_URL", GRAIN)
           .replace("NFRAMES", str(len(FRAMES))))

dest = os.path.join(ROOT, "proto-photo.html")
io.open(dest, "w", encoding="utf-8", newline="").write(HTML)
print("wrote %s  (%.0f KB)" % (dest, os.path.getsize(dest) / 1024.0))
