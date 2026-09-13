# SHAMUM — session handoff

Current as of **2026-09-13**, the photographic cutter (`986138c` plus the
handoff commit that follows it). `main` is in sync with origin and everything
here is **live on shamum.vercel.app**.

⚠️ **This is a sketch.** The user, 2026-08-27: *"this is all still considered a
sketch, no way this is gonna be the final site, this isnt even the first
prototype."* And later: *"my boss will laugh at my face if i show him this."*
Both are true at once. Nothing shipped is precious and big structural swings are
welcome, but the bar the user is holding it to is **"looks like a real brand"**,
not "technically clever". What stays worth the rigour at any stage is the
**silent-failure** class in **Environment traps**: those cost hours whether the
thing is a sketch or finished.

Companion document: **`DESIGN.md`** (design language, measured values, known
asset gaps). This file is operational.

---

## Read this first

1. **Integrate, don't replace.** Asked for "a better looking website", a
   photo-only hero was built from scratch. The user: *"bro wtf is this i didnt
   say remove the svg, just integrate what u just did with what we previously
   had."* The drawn SVG journey is the site. New directions go **into** it.
2. **Use the user's material, and use it literally.** Photos are assigned by
   **what they show**, not by what texture fits: *"the bukhoor should be for the
   bukhoor, and so on."* When the user supplies a photo of a person, the person
   in the frame is **that photo's pixels** — *"i gave you an image of a person,
   use it."* Five drawn or traced cutters were rejected before that landed.
3. **Ask for a reference before drawing anything real, then MEASURE it.** The
   mabkhara was drawn wrong twice, the flacon three times, the cutter five.
   Each was only fixed from a photograph. Do not eyeball proportions or anatomy.
4. **The user has strong visual judgement and is right.** Every "this looks off"
   has been a real defect with a findable cause. Don't defend — go measure. And
   don't call something "working" because it renders: the silhouette cutter was
   described as a success and was *"wtf is that"* on sight.
5. **Look at it before claiming it is right.** The browser pane cannot
   screenshot. Headless Chrome can, and `render/preview_chapter4.py` renders the
   real scene through the real `heroLoop`. Pane probes verify *animation*; the
   renderer verifies *appearance*. For motion, render a gif and look at it.
6. **When a fix doesn't converge in two passes, question the approach, not the
   numbers.** The cutter went drawn → articulated → two-bone → shadow → traced
   silhouette, each a better-tuned version of an approach that could not carry
   "a real person". The answer was a different kind of asset, not better numbers.

---

## Deploy

Push to `github.com/HawariGit/Shamum` (main) → Vercel → shamum.vercel.app.
Commits **must** be authored `HawariGit / hawaridata@outlook.com`; the user's
other identity is blocked by Vercel.

Verify live with PowerShell `Invoke-WebRequest` or `curl`, not the browser pane.

**`.vercelignore` is the only thing between the repo and the public domain** —
Vercel serves the repo root as static files. Excluded today: old site drafts,
`HANDOFF.md`, `DESIGN.md`, `render/` (all tooling, `render/ref/` included),
`assets/originals/`, `.agents/`, `.claude/skills/`, `skills-lock.json`,
`_rmtest.html`. **Anything new at the root or under `assets/` is public the
moment it is committed** unless a rule is added.

---

## Environment traps

| Trap | Detail |
|---|---|
| **`<span>` inside SVG** | On the HTML parser's foreign-content breakout list. A `<span>` inside `<text>` **terminates the `<svg>`** — silently, no console error. This deleted the oil vial's cap and the whole perfume bottle. Use `<tspan>`. **Run `render/check_svg.py` before every commit.** |
| **Invalid colours vanish silently** | SVG drops a bad stop with no error. A `#0B negative` placeholder once shipped in a zero-opacity stroke. Validate: `grep -oE '(stroke\|fill\|stop-color)="#[^"]*"' index.html \| grep -vE '="#([0-9A-Fa-f]{3}\|[0-9A-Fa-f]{6})"'` |
| **An unclosed brace blanks the whole hero** | Replacing a JS block by string splice once dropped the closing `}` of an `if`. The script failed to parse, `heroLoop` never ran, and the hero was an empty black frame with no visible error in the page. Count braces after any scripted JS edit. |
| **Browser pane viewport = 0×0** | Always `resize_window` explicitly **and re-navigate** before measuring — in that order. The pane is silently recreated whenever `preview_start` opens a new one (a taken port is enough to trigger it), which resets the viewport, so this recurs mid-session on a tab that was fine an hour earlier. ⚠️ **It presents identically to the stale-tab trap below**: every beat frozen at its end state at every scroll position. `400vh` of a zero-height viewport is 0, so the gaps collapse, `measureZones()` totals zero and `p` saturates instantly. The discriminator is `innerHeight` — check it before concluding anything, and check `.chapter-gap` heights are non-zero. |
| **The seed tab goes stale** | After `preview_start`, probes returned every beat frozen at its end state at every scroll position. It was an old page. Always `navigate` before measuring, and distrust a probe where nothing changes. |
| **rAF and IntersectionObserver are dead in the pane** | Step animation via `window.__heroTick(ms)`. `.reveal` never un-hides — its CSS fallback is behind the real `prefers-reduced-motion` query, which headless does not report however `heroStill` is set. |
| **A hidden pane freezes transitions** | The Browser pane reports `document.visibilityState: "hidden"` when it is not on screen, and browsers do not run CSS transitions in a hidden document — `getComputedStyle` keeps returning the PRE-transition value forever. A skip link that reveals on focus read as broken for three probes because of this. Re-test with `transition: none !important` injected. Also: synthetic `Tab` via `computer{action:"key"}` does NOT move focus — `activeElement` stays `BODY` — so keyboard traversal cannot be tested that way at all. |
| **`behavior:'smooth'` does nothing** | rAF-driven. Stub `window.scrollTo` and capture the args to verify targets. |
| **Never measure layout in an iframe** | It reported −1628px against a real −121px; its `scrollTo` does not drive the pinned layout. Navigate to each build directly. |
| **`#f4-bottle`'s bbox is useless** | Polluted by zero-opacity elements parked at default coordinates — reported a top of −1806 while the visible glass was at 493. Measure `#f4-bottle path[fill="url(#bottleGrad)"]` plus `#f4-cap`. |
| **The renderer hides the moving parts** | `preview_chapter4.py` renders through the reduced-motion branch, and `.reduced-hero` sets `display:none` on `#hp-open`, `#f1-chips`, `#f1-dust`, `#f1-birds`. A whole strike was tuned against renders that were drawing none of it — the DOM said opacity 1 while `getBoundingClientRect` returned all zeros, which is what `display:none` looks like from JS. Its `CLEAN` block force-shows them; **keep that list current.** |
| **`#veil` misfires in sequence renders** | The entry veil occasionally paints over a frame mid-sequence and reads as a flash in the gif. `CLEAN` sets `#veil{display:none}`, and hides `#nav`, `#menu-overlay`, `#scroll-cue`, `#ch-dots`. |
| **Headless ignores narrow `--window-size`** | On Windows, Chrome clamps the window to about **500px** and lays out there however small a width you ask for — but it still writes a screenshot at the width you asked for. A `--window-size=390` capture therefore shows a 500px layout cropped to 390, which looks exactly like text overflowing its container. Several passes went into "fixing" that phantom. Confirm the real viewport with `--dump-dom` before believing any narrow-screen bug. |
| **Coarse sampling straddles narrow beats** | The chapter IV press peaks across ~0.06vh. A 0.1vh sweep reports it never fires. |
| **PowerShell mangles quotes** | No heredocs; `<`, `>`, `"` break `-m`. Write commit messages to a file and use `git commit -F`. |
| **Bash heredocs break on mixed quotes too** | Python with both quote styles and `$` inside a bash heredoc got mangled more than once. Write scripts to the scratchpad with the Write tool and run them. |
| **cp1252 on Windows** | Python reading `index.html` or printing box-drawing / Arabic characters dies with `UnicodeDecodeError` / `UnicodeEncodeError`. Open with `encoding="utf-8"` (and `newline=""` when writing back) and run with `PYTHONIOENCODING=utf-8`. |
| **Cyrillic lookalikes** | Nearly shipped `#А5642A` with a Cyrillic А. Grep `[Ѐ-ӿ]` if a colour looks wrong. |

---

## Architecture — the hero

`#hero-track` holds a **pinned** `#hero-sticky` (one 1440×900 SVG world, four
900-tall floors) plus alternating scroll zones:

```
gap1 (chapters I–II) → shelf-bukhoor → gap2 (III) → shelf-oils
→ gap3 (IV) → shelf-fragrances → coda → shelf-limited
```

- **`.chapter-gap`** — transparent, advances the animation. `measureZones()`
  counts **only these**.
- **`.chapter-coda`** — deliberately *not* a gap: adds scroll without advancing
  `p`. Use this pattern if you ever need room after `p` saturates.
- **`.chapter-products`** — transparent strip, one horizontal row of glass cards.

**Stacking inside `#hero-sticky`**, bottom to top:

| z | layer |
|---|---|
| 0 | `#hero-photo` — the photographic ground (below) |
| 1 | `#hero-svg-scene` — the drawn world |
| 2 | `#hero-canvas` — dust, smoke, nozzle mist |
| 4 | `#hero-grain` — film grain, 0.13, no blend mode |
| 5 | the sticky's `::after` vignette |

**Gap heights** (the pacing dial): desktop `300 / 190 / 300vh`, mobile
`285 / 180 / 275vh`, coda `40 / 36vh`. The journey is **11.4 viewports**
desktop, 11.3 mobile, and the first product strip is 4.0 viewports down.

⚠️ **They are not "safe to tune".** Gap height divided by a chapter's p-band is
how many PIXELS each beat gets, so shortening a gap compresses every beat inside
it. Run **`render/pacing.py`** before touching these. Two binding constraints:

- **Chapter IV's cap seating** is the narrowest beat on the site at `dp 0.008`.
  Desktop gives it 120px; **mobile gives it 95px**, which is why mobile `gap3`
  was left uncut. At `260vh` mobile it drops to 87px and stops registering.
- **Chapter I's push-in** spans only `dp 0.032`, and `gap1` is all that protects
  it. Below ~`280vh` desktop it reads as a jolt rather than a camera move.

Phones scroll by flicks, so a short beat there is skipped outright — **mobile
wants more room per beat than desktop, not less**. Always confirm `camY` still
reaches 2700 after a change; if it does not, chapter IV no longer completes.

### Chapter bands (`p`)
`I 0.00–0.30 · II 0.24–0.62 · III 0.62–0.88 · IV 0.88–1.00`, pinned via
`STOPS = [0, 0.62, 0.88, 1]`. Each gap finishes its chapter one viewport early
(`tail`) so a strip never covers a running animation. The spring is critically
damped: `acc = (raw − sPos)·80 − sVel·18`.

⚠️ **Chapter IV has no headroom left** — its tail runs to exactly `p = 1.000`.
Any new beat must be paid for by compressing an existing one. Appending is what
silently deleted the press and mist once. **Check any retime with
`seg(1.0, a, b) == 1` for every tail window.**

### The landing frame
`p = 0` shows the wordmark over the **opening plate** (`#hp-open`,
`ig-box-closed`). Two faults were fixed here and both looked like "nothing":

- the logo's opacity was driven so it was **blank at `p = 0`** — the first thing
  anyone saw was black. It is now `1 − eIn(seg(p, 0.095, 0.15))`, full on
  arrival, with a 5% scale-down on the way out;
- there was nothing behind it. `#hp-open` sits at `0.62·(1 − eIn(seg(p, 0.07,
  0.13)))` and is forced to 0 past `p 0.22`. It is **gated on `p`, not on the
  camera** — see the `[data-ch]` trap in the next section.

`ig-box-closed` was chosen because it is warm, dark and carries no competing
mark: `ig-decanter` would put the monogram wall behind the monogram logo, and
`ig-ritual` has a person in it, who survives blurring.

### The photographic ground
The house's own photography sits **under** the drawn scene, one plate per floor.
The SVG floors carry no opaque backdrop, so this shows through everywhere the
drawing is not. The illustration is still the subject; the plates are the room.

| floor | plate | brightness | saturate | blur |
|---|---|---|---|---|
| open | `ig-box-closed.webp` | 0.58 | 0.60 | 15px |
| I | `agarwood.webp` | **0.17** | 0.34 | **26px** |
| II | `ig-bukhoor.webp` | 0.34 | 0.55 | 9px |
| III | `oud-oil.webp` | **0.82** | 0.55 | 18px |
| IV | `ig-box-open.webp` | 0.40 | 0.55 | 9px |

- **Keyed to the camera, not the chapter text.** Each `.hp[data-ch]` peaks when
  `camY` reaches its floor (`(ch−1)·900`) and is gone one floor either side:
  `po = sstep(1 − |camY − floor|/900) · 0.55`, plus a tiny scale drift.
- **Exposure is per plate, inline.** 0.34 is right for the bukhoor's bright smoke
  and turns the oud bottle into a black rectangle; the agarwood is a product shot
  on **cream** (mean luminance 168) and needs the deepest grade in the set.
- ⚠️ **The selector must be `#hero-photo .hp[data-ch]`.** The opening plate is a
  `.hp` in the same container. Without the attribute filter it was picked up,
  computed a `camY` of −900 from a missing `data-ch`, and had its opacity
  overwritten to 0 one block after being set — so it never appeared.
- Floor 1 shares `camY 0` with the opening plate, so its ramp is additionally
  gated `po *= sstep(seg(p, 0.10, 0.21))` — it arrives with the tree.
- **No legible people.** The ritual shot behind chapter II was the one
  arrangement that genuinely failed: a figure reads as a person at any blur.
- `oud-oil.webp` is **the house's own photo** and the one the user asked for by
  name for chapter III. It is upscaled from a 204×289 screenshot, which the 18px
  blur hides. Ask for the original before using it anywhere sharp.

### Scene clearing — the scene DIMS, it never scales
`shelfCover` = fraction of a strip inside the frame, ramping **both** ways.
Damped `dt * 7.5`, eased `sstep`. Drives `titleMute`, a `translate3d` lift of
**0.10·vh**, and **opacity down to 0.45**.

⚠️ **Do not reintroduce a scale here.** Shrinking a full-bleed element exposes
its own bounding box — a hard-edged rectangle of scene on the page, with the
sticky's `::after` vignette (which does *not* shrink) aligned to nothing. You
cannot scale an element down and still cover the frame, and enlarging it to
compensate only zooms the world, because `#hero-svg-scene` is
`preserveAspectRatio="slice"`.

### The push-in — chapter I
It pushes in once on **the wound at (720,790)**.

| p | |
|---|---|
| 0.182–0.214 | push in, 1.0 → **2.6** about the wound |
| 0.206–0.268 | `#f1-bloom` — the resin catches and floods the notch |
| 0.262–0.345 | release, **folded into the descent** to chapter II |

`zoomT = sstep(seg(p,0.182,0.214)) · (1 − sstep(seg(p,0.262,0.345)))`,
`zoom = 1 + 1.6·zoomT`, `zoomY = −310·zoomT` (lifts the wound toward frame
centre; without it the push reads as a crop). The near layer goes to **2.84**.

⚠️ The release used to be its own beat at 0.258–0.292, finishing before the
descent got going: push in, pull back out, *then* travel. The user: *"after he
cuts, dont zoom out again thats just weird."* It now unwinds entirely inside the
camera's move down, and `zoomY` returning to 0 adds its 310px to the descent
rather than fighting it. **Do not split them apart again.**

### Chapter IV — the perfumer's bench
Chapter III's own vial stands on the bench; a pipette draws from *that* and
doses the flacon, and `f4-vialfill` drops as `f4-pipfill` rises so the oil is
**moved, not created**. The story is the brand's own, from SHAMUM's film:
*"Natural oud… refuses to share the stage… saffron, rose, and iris are the
finest companions… time itself is the key ingredient."*

**The oud must fill and sit ALONE before anything joins it.**

| p | beat |
|---|---|
| 0.885–0.925 | bench, organ, blotters, vial and companion vials fade in |
| 0.894–0.921 | the flacon's cap lifts, then is set down on the counter |
| 0.898–0.923 | pipette into the vial; **the vial's level falls** |
| 0.921–0.933 | it carries across |
| 0.930–0.948 | the drop leaves its tip and falls |
| 0.936–0.949 | the oud climbs — **alone** |
| 0.948–0.970 | saffron, rose, iris arc in, staggered |
| 0.968–0.980 | maceration — *"time itself"* |
| 0.974–0.986 | `f4-oud` fades → oud-dark lightens to gold |
| 0.980–0.988 | the cap returns and seats |
| 0.988–1.000 | the press, then the mist |

- The colour change is a **second rect** (`f4-oud`) tracking `f4-liquid` with
  only its opacity animated. SVG will not interpolate gradient stops without SMIL.
- The cap comes off in **two moves**. One diagonal drags it through the shoulder.
- **Mobile decided the layout.** At 375px the scene slices to world x 512–928,
  so vial, flacon, pipette travel and resting cap all live inside it.
- `#f4` carries `translate(0,115) translate(720,3334) scale(0.76)
  translate(-720,-3334)`. ⚠️ **The canvas is outside that group** — `drawFx`
  paints the nozzle on `#hero-canvas`, so `F4_SCALE`/`F4_DROP`/`F4_ORIGIN` and
  `f4y()` mirror it by hand. **The group's transform is the truth.**

### Screen-space overlays
Both live outside `#world` so the camera does not carry them.

- **`#pan-veil`** — the mabkhara's smoke, passed *through* on the descent to the
  still. Peaks 0.45 on `sin(fallT·π)`. A first pass at 0.9 white-outed the frame.
- **`#chapter-tint`** — cool forest, warm majlis, smoky still, gold bench, lerped
  between chapter centres. ⚠️ **A vignette, not a flat wash** — a mid-tone over
  near-black lifts the frame and flattens its contrast.

---

## The drawn objects

### The tree — generated, not hand-placed
The old canopy was three stacked ellipses ~500px across with a hard elliptical
"saucer" under it and two diagonals for branches. The user: *"the tree is still
terrible, very very bad."* It read as broccoli on a stick.

It is now the output of **`render/make_tree.py`** (seed `20260909`,
deterministic): recursive limbs from the trunk top at y 558 — **78 branch
paths** — and foliage as ~260 small ellipses clustered on the branch tips, split
into `can-back` (30), `can-mid` (87) and `can-front` (141). Those three ids are
kept because the wind sway in `heroLoop` drives them. The crown is ~360 wide,
narrower and taller than before, because Aquilaria is a tall straight-boled
evergreen, not a lollipop. It is **backlit** (the sun sits behind it): foliage
fills are near-black greens `#0A1206`–`#17240E` with rim tones
`#233110`–`#35471F`, limbs `#241505` thinning to `#130A02`. In frame it reads
as a dark mid-green. (The generator's docstring still says "warm darks" — the
fills above are what shipped.) `#f1-rays` apex moved to `720,322` to match.

To change the tree, change the generator and re-splice its output; don't
hand-edit 300 ellipses.

### The cutter — a photograph, not a drawing
`#f1-cutter`, one man in a dishdasha at the trunk's left face, striking the
notch. **He is the reference image's own pixels**, cut out and graded.

Why, in the order it was learned:

1. The strike first had **no visible cause** — notch, ring, dust, chips, birds.
   *"the cutting process is weird asf it just cuts itself."*
2. A drawn figure: *"the entire body is trash, it looks terrible with robotic
   movement, i want it as if there is a real person cutting."*
3. An articulated body, then a two-bone arm with an elbow: *"bro the body"*,
   *"it doesnt even look like a human bro."*
4. A flat shadow silhouette, then an outline **traced** from a reference the
   user supplied: *"wtf is that"* — a dark blob on a dark scene, missing its head.
5. *"i gave you an image of a person, use it."* The pixels. This is live.

**Pipeline — `render/make_cutter.py`** (reproduces the live PNGs byte for byte;
it says `MATCHES` when it does):

- **Source:** `render/ref/cutter-reference.png`, 1024×1536. ⚠️ **It is an
  AI-generated image** the user supplied, not a photograph of a real person or
  of the house's own. Fine for a sketch; replace with a real shoot before
  anything final.
- **Mask:** robe first — `val > 0.55 & sat < 0.35` in an ROI, median filter,
  15px opening, largest component. Brightness separates robe from foliage;
  saturation does not (it was discarding the robe). Then an **explicit head box**
  `375,200–585,458` minus green (the heuristic kept shipping a headless robe).
  Then **forearm skin** in `430–660 × 620–840`, `r>g>b & r−b>12`, because dark
  skin never survives a brightness mask and left a hole through his middle.
  Closing 41, erode 11 / dilate 9 to sever the bright leaf spurs on his right
  edge, fill holes.
- **Split:** the arm is everything forward of a slanted line through the
  shoulder at source `(452,470)`, within y 380–812. **The body layer keeps the
  whole mask** — cutting the arm out left a hole the moment it rotated.
- **Grade:** `g·0.20 + lum·0.06`, then warm `×[1.06, 0.94, 0.78]`. At 0.42 he was
  blazing white on a near-black forest and read as pasted on.
- **Export:** one shared box so the layers stay in register, 1.6px feathered
  alpha, 420 tall (he is 390px at the push-in; more is dead weight), 128-colour
  PNG, inlined as data URIs. Body 20 KB, arm 8 KB.
- `--install` swaps only the two `href` payloads; placement and rig are in
  `index.html` and are left alone.

**Placement and rig** (in `index.html`, not the script):

- both `<image>`s at `x 566 y 666 w 80.3 h 150`, feet on the ground line,
  contact shadow ellipse at `(600, 818)`. 150 tall: the trunk is the subject.
- the **axe is drawn**, inside the arm group: haft `M636.6 744 L703 788`
  (`#2A1B08`, 4.4), highlight, dark head, pale edge. It is brown wood and dark
  steel, so it never survived the mask, and a rigid object draws cleanly.
- `cutIn = eOut(seg(p,0.135,0.20)) · (1 − eIn(seg(p,0.44,0.54)))`.
- `lift = sin(beat·π)^0.7`, `drive = (1 − sin(beat·π))^1.5`, on the **same
  `beat`** as the ring, dust and chips, so the blade is in the notch at the
  instant the trunk is knocked.
- arm: `rotate(−12·lift, 611.2, 707.5)` — the shoulder, i.e. the source pivot
  mapped through the box (`566 + 0.5633·80.3`, `666 + 0.2769·150`). **If the box
  or the source changes, recompute this.**
- body: `translate(0, 6·drive) rotate(11·drive, 602.1, 765)` — the lean and dip
  carry most of the motion.

⚠️ **The stroke is 12° on purpose.** The arm is one rigid piece of photograph.
Rotated further, the blade sweeps past the trunk and the sleeve seam opens where
the arm leaves the body. A real overhead swing needs **a second pose image**
(arms raised) cross-faded or swapped at the top of the beat — that is the next
step if the motion is ever called out, not a bigger angle.

Known flaws, visible at the push-in: the seam at the top of the stroke, faint
bright fringe on his right edge, and the stroke reads as close notch work rather
than a felling blow.

⚠️ **Do not try "an axe swings in from off-frame".** At full push-in the visible
world is x 443–997, y 605–951, with the trunk dead centre. A world px is about a
centimetre; reaching the notch from the nearest frame edge needs a **2.6 metre
axe**. The arithmetic was done before anything was drawn — redo it before
overriding.

**The strike itself:**

| beat | |
|---|---|
| ring | `sin(beat·2π·2.4)·e^(−7·beat)` × 7.0 × `chopEnv` — a knock, then still |
| dust | `#f1-dust` expands 0.5→2.4 about (706,789), peak opacity 0.70 |
| chips | 8 pieces off the notch together, biased right |

- **The ring is an impulse, not a wave.** `max(0,sin)` was a symmetric hump — a
  tree *swaying*. Now it peaks ~47ms after the beat and is dead by half a beat.
- **Chips had to be rebuilt to be visible at all:** their fills were the trunk
  gradient's own values (now `#8A6134 / #B98A4C / #5E4020`), their speed kept
  them inside the resin glow (now `spd 70–140`, `dx 0.25 ± 0.95`), and their
  opacity is **held** through ~58% of flight, `min(1, (1−life)·2.4)`.
- They share the beat with a few percent of launch stagger, not a per-chip phase
  (which read as a tree steadily shedding).
- The notch is in the trunk's **left** face (701–727 of 700–740): the blow comes
  from the left, chips fly right, into the backlight.

### The mabkhara
Olive wood in emerald resin, blackened cup, black foot. **The pieces carry the
surface; the resin is the vein between them** — about a quarter of the face.
11 chunks tiling 656–784 × 1436–1548 exactly, two small fillers so the veins
don't read as a grid. Every piece needs a **dark bark edge** (`#33210C`) or it
looks like paper laid on green. Grain: cubic S-curves, 2–3 per chunk, 24 total.
Tonal range `#E8DCB4` down to `#9E7534`. Judge the emerald against a photo.

`f2-wood` carries **no JS** — only the group's opacity is animated — so its
interior is free to redraw. The cup mouth is held at y 1428 because falling oud
is aimed at 1412–1424.

### The flacon
188 × 334, aspect **0.56**, and that number is **the user's eye, not a
measurement**. The reference is backlit gold on gold silk and its glass edges
cannot be found. **Do not claim to have measured it.** The label plate is
measurable: 70% of body width, matching.

- **The cap is polished metal, not gold** — near-black to blown-out, with an
  *abrupt* jump (`capMirror`). A gentle ramp reads as anodised plastic.
- **A slab of clear glass under the liquid** — fill floor **3300, not 3328**.
- **The atomiser's dip tube** runs neck to base, behind the label plate.
- `capGold` got the same treatment in gold.
- The label reads **منــدل / *mandle*** — the actual bottle. Arabic in
  `<tspan lang="ar">`, never `<span>`.

---

## Reduced motion

`prefers-reduced-motion: reduce` does not soften the journey, it **replaces** it.
JS reads the query once into **`heroStill`** and puts **`.reduced-hero`** on
`<html>`.

`heroStill` gates: rAF is never re-armed, `p` is pinned to `HERO_STILL_P`
(0.23 — chapter I, tree complete, camera on floor 1), the spring is bypassed,
and **the push-in and bloom are switched off**. `heroTime` is pinned to
`HERO_STILL_T = 15/4.4`, beat 0.5 — the ring has decayed to ~0.2px and the
cutter's arm is at the top of its stroke. ⚠️ **Keep that exact value**; the
wind, leaves and fireflies were composed at it.

**The still cuts the moving parts entirely**: `#hp-open`, `#f1-chips`,
`#f1-dust`, `#f1-birds` are `display:none` under `.reduced-hero`. Plates don't
drift (`.hp { transform: none }`).

Gaps and coda collapse to 0. `staticChapters()` re-homes ht2/ht3/ht4 above their
shelves. `shmScrollTo` jumps instead of smooth-scrolling, and is **assigned to
`window` on purpose** — the nav's inline `onclick` resolves against global scope.

---

## Below the hero

Sections in order: `#brand-statement` → `#ritual` → `#essence` → **`#painted`**
→ `#quote-section` → `#scent-life` → `#trust` → `#loyalty`.

- **`#essence`** panel I uses `assets/oud-coal.webp` (the house's photo).
- **`#painted`** — *"The House Paints Its Scents"*. Three square plates, each a
  bottle photographed against its own painting: **zahyah** (`prod-zahyah-2`),
  **mandle** (`prod-mandle`), **Flower Gardens** (`prod-flower-gardens`),
  captions inset over the image, notes paraphrased from the store descriptions.
  Images at `brightness 0.72 saturate 0.86`, lifted to 0.92/1 on hover. 3 columns,
  1 below 900px. Deliberately not the `.ess-grid` layout, so the two sections
  don't read as the same thing twice. The user asked for these photos to be
  used *"think of a way to use them"*; the painting-behind-the-bottle pairing is
  the idea, which is why the tighter store thumbnails were not swapped in.
- **The name is `zahyah`**, lower-case, the user's spelling. Not "Zahiya".
- **Heritage counter** is `data-since="2010"` and computes `year − 2010` at load.
  "16 Years" was hardcoded and would have gone wrong on 1 January.
- **Accessibility pass:** `:focus-visible` gold outline with a dark halo on
  `a, button, input, [tabindex]`; a skip link (`#skip-link` → `#brand-statement`)
  as the first element in `<body>`; `tabular-nums` on prices and counters;
  `text-wrap: balance` on headings.
- **Scroll handlers are rAF-coalesced** (`navTick`, `brandTick`) — they were
  running layout reads on every scroll event.
- **Gold is the only accent.** `--teal`, `--teal-deep` and the limited badge
  that used them are gone. Section eyebrows no longer count themselves ("01 —").

### Cards and page atmosphere
**The card plate cannot be dark.** The photos are lifestyle shots with light
backgrounds, composited `mix-blend-mode: multiply`, which needs a light ground.
The plate's *edges* are blended into the card (`.product-image-wrap::after`)
instead, turning each into a lit alcove.

**`#page-ambient`** — one fixed layer of three faint warm radials, z-index 4,
transform-only drift. ⚠️ **No `mix-blend-mode` on purpose:** a blended fixed
layer forces a full recomposite every frame and washes out the photographs.

---

## Assets

| file | used for | note |
|---|---|---|
| `agarwood.webp` | ch I plate | cropped from Jawhar's poster — real heartwood |
| `ig-box-closed.webp` | opening plate | |
| `ig-bukhoor.webp` | ch II plate | |
| `oud-oil.webp` | ch III plate | house photo, upscaled from 204×289 |
| `ig-box-open.webp` | ch IV plate | |
| `ig-ritual.webp` | `#ritual` | |
| `ig-decanter.webp` | `#essence` panel II | |
| `oud-coal.webp` | essence panel I | |
| `prod-zahyah-2`, `prod-mandle`, `prod-flower-gardens` | `#painted` | |
| `prod-zahyah`, `prod-mandle-2`, `prod-flower-gardens-2`, `mabkhara-table` | **nothing** | deployed but unreferenced (~720 KB) |
| `originals/` | 3000px sources | vercelignored; regenerate web copies from here |

Cutter reference: `render/ref/cutter-reference.png` (vercelignored with `render/`).

---

## Tooling in `render/` (in git, excluded from deploy)

| Script | Purpose |
|---|---|
| `check_svg.py` | **Run before every commit.** Scans SVG regions for HTML breakout tags. |
| `preview_chapter4.py` | Renders the scene through the **real** `heroLoop`. `--p 0.95`, `--strip a,b,c`, `--gif`, `--zoom` (push-in, off when `heroStill`), `--cover 0.53` (strip transition). ⚠️ Renders through the **reduced-motion branch**; its `CLEAN` block force-shows `#hero-canvas`, `#hp-open`, `#f1-chips`, `#f1-dust`, `#f1-birds` and hides `#veil`, `#nav`, `#menu-overlay`, `#scroll-cue`, `#ch-dots`. **Add any new moving part to that list.** `shot_guarded` re-shoots any frame jumping >10 luminance from the previous (about one capture in seventy fires before paint and returns near-black). `--p` injects `CLEAN`, so it is *not* a faithful still — use `preview_reduced.py` for that. |
| `make_cutter.py` | Rebuilds the cutter from `render/ref/cutter-reference.png`. Prints `MATCHES` / `DIFFERS` against `index.html`; `--install` swaps the two PNGs in. Previews in `render/out/cutter_*.png`. |
| `make_tree.py` | Generates chapter I's branches and foliage (fixed seed). |
| `preview_reduced.py` | Writes `_rmtest.html` with the reduced-motion branch forced on. `--rm` deletes it. |
| `preview_flacon.py` | Single flacon still, `--fill 0.5`. |
| `page_shots.py` | Screenshots every section below the hero, one isolated section per shot (`painted` included). |
| `pacing.py` | **Run before changing any gap height.** Pixels-per-beat for desktop and mobile. |
| `watch_video.py` | Video → frames. Streams; do not accumulate. `plugin="FFMPEG"`. |
| `fetch_catalogue.py` / `fetch_categories.py` / `build_catalogue.py` | Pull the 15 products and rebuild the cards. **Use `fetch_categories`, don't infer.** |
| `retime_chapters.py` / `retime_chapter4.py` | Threshold retiming, all-or-nothing. |
| `mark_arabic.py`, `make_svg.py`, `make_og.py`, `group_products.py`, `interleave_products.py` | One-shot / asset tooling. |

`render/mabkhara.py` is **untracked and not ours** — it was in the working tree
at the start of the session. Leave it alone unless the user says otherwise. Same
for the screenshot and `.mp4` at the repo root.

`imageio` + `imageio-ffmpeg` are installed; the ffmpeg binary lives **inside
site-packages, not on PATH**. `numpy`, `scipy`, `PIL` are installed; `skimage`
and `cv2` are **not**.

**For motion, make a gif.** A still cannot show whether a swing reads as a
person. The cutter gifs were built by stepping `p` across 0.155–0.355 in 68
frames at 18 fps through `preview_chapter4.shot_guarded` with `ZOOM_ON`; that
loop lived in the scratchpad and is not in `render/` — rebuild it from those
numbers if needed.

### Agent skills
`npx skills add Leonxlnx/taste-skill` (2026-09-03) installed 13 design skills
into `.agents/skills/`, symlinked at `.claude/skills/`, with `skills-lock.json`.
They are **untracked** and vercelignored. `redesign-existing-projects` and
`design-taste-frontend` were run against the site; their output became
`DESIGN.md` and the accessibility / accent / eyebrow fixes above. Treat their
generic rules (e.g. "no centred heroes") as prompts, not law — `DESIGN.md`
records where this site deliberately departs from them.

---

## Products

All 15 pulled from the store, in four groups matching the store's own
categories. Prices, images, links and Arabic come from the store; the **Latin
names are hand-supplied**. Five are out of stock, badged and dimmed.

---

## Open items

1. **The cutter's swing.** 12° close work, a seam at the top of the stroke,
   fringe on the right edge. The fix is a **second pose image** of the same man
   with the axe raised, not a larger rotation. Also: the source is AI-generated.
2. **Product photography.** Only zahyah, mandle and Flower Gardens have house
   photos. The other 12 cards use store lifestyle shots that cannot be cut out.
3. **The full-resolution oud bottle.** `oud-oil.webp` is a screenshot upscale.
4. **`Jawhar`'s card image is a poster** with the price printed in it. If the
   price changes the card is silently wrong. **Unchanged at the user's
   instruction.**
5. **The 3ml oil مندلي is still "Mindali".** No evidence for any spelling on the
   bottle. If مندل is *mandle*, مندلي is probably *Mandli*. **Ask first.**
6. **Analytics.** None. `/_vercel/insights/script.js` is 404 and `index.html`
   has no script tag. The user has to enable Web Analytics in the Vercel
   dashboard first; then add the one tag.
7. **Four unreferenced assets** deployed (see **Assets**). Delete or use.
8. **A ~126px top overhang** was once reported as the scene steps aside at
   chapter IV's end. It could **not be reproduced** in the last session; treat
   it as unconfirmed until seen.

---

## Tried and didn't land

⚠️ **This is not a ban list.** Almost everything below is a verdict on **one
execution**, not on the idea. Where a diagnosis is inferred rather than said by
the user, it says so.

### Structural — these genuinely cannot work

- **Scaling the scene for the product strips.** Geometry, not taste. See
  **Scene clearing**.
- **An axe swung in from off-frame in chapter I.** Needs a 2.6 metre haft. See
  **The cutter**.
- **An opaque panel of any colour over the animation.** Cream (*"a whole
  different page"*) and full-dark (*"same problem, still covered the scene"*)
  failed the same way, so the fault is the **panel**. Transparent strips over a
  dimmed scene came out of that and carry the whole strip system.
- **A rigid photographic arm rotated through a full swing.** One cut-out arm
  cannot become a raised arm; past ~15° it shows the seam and the sleeve turns
  over. Needs a second pose.

### Taste calls on one execution — a better attempt is open

- **Drawing a person.** Five drawn or traced versions (flat figure, articulated,
  two-bone arm, shadow silhouette, traced outline) were rejected for not reading
  as human. *(Inferred:)* the fault was information, not skill — a silhouette
  has no face, cloth or light. That is why the photograph worked. A drawn figure
  in a different style is still an open idea; another silhouette is not.
- **A strike with no visible cause.** A real device; *"it just cuts itself."* An
  unseen cause needs a consequence far louder than a shuddering trunk.
- **The zoom releasing as its own beat.** *"dont zoom out again thats just
  weird."* Folding it into the descent fixed it.
- **A photo-only hero** replacing the SVG. *"i didnt say remove the svg."* The
  photographs work as the ground **under** the drawing.
- **Assigning photos by texture.** Bukhoor behind the oils because it looked
  right tonally. *"the bukhoor should be for the bukhoor."*
- **The finale pull-back** to four floors in one column. *"that zoomout wasnt good
  i didnt like it."* *(Inferred:)* it makes the product small at the moment it
  should be closest, and a column of floors reveals the page's scaffolding.
- **EEVEE 3D of the flacon** — *"looks like a Jimmy Neutron animation."* A verdict
  on the **renderer and lighting**. Cycles with real glass IOR, caustics and an
  HDRI is untested.
- **The Cycles mabkhara still** — the SVG was preferred. ⚠️ That is evidence
  about an **opaque matte** object; glass with liquid in it is the opposite case.
- **Synthesising an empty bottle from a product photo** — *"looks fake."*
  Probably a real dead end: erasing the liquid leaves refraction belonging to a
  full bottle. Needs a photograph of an actually empty one.
- ~~Marwa 3D files~~ — deleted 2026-08-27. `.vercelignore` keeps the
  `assets/marwaframes/` rule as a guard.
