# SHAMUM — session handoff

Current as of `6b361ae`. `main` is in sync with origin and everything here is
**live on shamum.vercel.app**.

---

## Read this first

1. **Ask for a reference photo before drawing any product, then MEASURE it.**
   The mabkhara was drawn wrong twice and the flacon three times, each corrected
   only when the user sent a photograph. Do not eyeball proportions.
2. **The user has strong visual judgement and is right.** Every "this looks off"
   has been a real defect with a findable cause. Don't defend — go measure.
3. **Look at it before claiming it is right.** The browser pane cannot
   screenshot (`computer{action:"screenshot"}` always fails; it never
   composites). Headless Chrome can, and `render/preview_chapter4.py` renders
   the real scene through the real `heroLoop`. Geometry and timing probes in the
   pane verify *animation*; the renderer verifies *appearance*. Several defects
   shipped purely because a state was unreachable in a still — see the preview
   flags in **Tooling**.
4. **When a fix doesn't converge in two passes, question the approach, not the
   numbers.** The axe head took three passes because each time the shape was
   adjusted when the *size* was wrong. The strip shrink was tuned by a careful
   sweep that optimised a technique which could never work.

---

## Deploy

Push to `github.com/HawariGit/Shamum` (main) → Vercel → shamum.vercel.app.
Commits **must** be authored `HawariGit / hawaridata@outlook.com`; the user's
other identity is blocked by Vercel.

Verify live with PowerShell `Invoke-WebRequest` or `curl`, not the browser pane.

---

## Environment traps

| Trap | Detail |
|---|---|
| **`<span>` inside SVG** | On the HTML parser's foreign-content breakout list. A `<span>` inside `<text>` **terminates the `<svg>`** — silently, no console error. This deleted the oil vial's cap and the whole perfume bottle. Use `<tspan>`. **Run `render/check_svg.py` before every commit.** |
| **Invalid colours vanish silently** | SVG drops a bad stop with no error. A `#0B negative` placeholder once shipped in a zero-opacity stroke. Validate: `grep -oE '(stroke\|fill\|stop-color)="#[^"]*"' index.html \| grep -vE '="#([0-9A-Fa-f]{3}\|[0-9A-Fa-f]{6})"'` |
| **Browser pane viewport = 0×0** | Always `resize_window` explicitly **and re-navigate** before measuring. |
| **The seed tab goes stale** | After `preview_start`, probes returned every beat frozen at its end state at every scroll position. It was an old page. Always `navigate` before measuring, and distrust a probe where nothing changes. |
| **rAF and IntersectionObserver are dead in the pane** | Step animation via `window.__heroTick(ms)`. `.reveal` never un-hides — its CSS fallback is behind the real `prefers-reduced-motion` query, which headless does not report however `heroStill` is set. |
| **`behavior:'smooth'` does nothing** | rAF-driven. Stub `window.scrollTo` and capture the args to verify targets. |
| **Never measure layout in an iframe** | It reported −1628px against a real −121px; its `scrollTo` does not drive the pinned layout. Navigate to each build directly. |
| **`#f4-bottle`'s bbox is useless** | Polluted by zero-opacity elements parked at default coordinates — reported a top of −1806 while the visible glass was at 493. Measure `#f4-bottle path[fill="url(#bottleGrad)"]` plus `#f4-cap`. |
| **PowerShell mangles quotes** | No heredocs; `<`, `>`, `"` break `-m`. Write commit messages to a file and use `git commit -F`. |
| **Coarse sampling straddles narrow beats** | The chapter IV press peaks across ~0.06vh. A 0.1vh sweep reports it never fires. |
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

**Gap heights** (the pacing dial — independent of timing, safe to tune):
desktop `400 / 210 / 320vh`, mobile `330 / 180 / 275vh`, coda `62 / 46vh`.
`400vh` means 4 viewports. The whole journey is ~14 viewports of scroll.

### Chapter bands (`p`)
`I 0.00–0.30 · II 0.24–0.62 · III 0.62–0.88 · IV 0.88–1.00`, pinned via
`STOPS = [0, 0.62, 0.88, 1]`. Each gap finishes its chapter one viewport early
(`tail`) so a strip never covers a running animation.

⚠️ **Chapter IV has no headroom left** — its tail runs to exactly `p = 1.000`.
Any new beat must be paid for by compressing an existing one. Appending is what
silently deleted the press and mist once: offsetting everything after the
maceration by +0.012 put the press at 1.002–1.008 and the mist at an inverted
1.003–1.000, so neither ever fired and the cap seated only 80%. **Check any
retime with `seg(1.0, a, b) == 1` for every tail window.**

### Scene clearing — the scene DIMS, it never scales
`shelfCover` = fraction of a strip inside the frame, ramping **both** ways.
Damped `dt * 7.5`, eased `sstep`. Drives `titleMute`, a `translate3d` lift of
**0.10·vh**, and **opacity down to 0.45**.

⚠️ **Do not reintroduce a scale here.** Shrinking a full-bleed element exposes
its own bounding box — a hard-edged rectangle of scene on the page, with the
sticky's `::after` vignette (which does *not* shrink) no longer aligned to
anything. There is no version that works: you cannot scale an element down and
still cover the frame, and enlarging it to compensate only zooms the world,
because `#hero-svg-scene` is `preserveAspectRatio="slice"`.

The strip heading still overlaps its subject ~49px on all three chapters. That
is fine and is the point — at 45% the scene is tonally subordinate.

### The push-in — chapter I
The camera panned the whole journey at **one scale**, which is why it read as
competent rather than big. It now pushes in once on **the wound at (720,790)**.

| p | |
|---|---|
| 0.182–0.214 | push in, 1.0 → **2.6** about the wound |
| 0.206–0.268 | `#f1-bloom` — the resin catches and floods the notch |
| 0.258–0.292 | release, as the camera starts down |

`zoomY` lifts the wound toward frame centre (without it the push reads as a
crop). The near layer goes to **2.84** — pushing in should open the parallax up.
The bloom uses `sin(t·π)` so it rises *and* falls on one term.
Spans ~0.6vh of scroll; slowing it means lengthening gap1, which also slows
chapters I and II.

### Chapter IV — the perfumer's bench
Chapter III's own vial stands on the bench; a pipette draws from *that* and
doses the flacon, and `f4-vialfill` drops as `f4-pipfill` rises so the oil is
**moved, not created**. The story is the brand's own, from SHAMUM's film:
*"Natural oud… refuses to share the stage… saffron, rose, and iris are the
finest companions… time itself is the key ingredient."*

**The oud must fill and sit ALONE before anything joins it.** That ordering is
the point.

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

- The colour change is done with a **second rect** (`f4-oud`) tracking
  `f4-liquid` with only its opacity animated. SVG will not interpolate gradient
  stops without SMIL.
- The cap comes off in **two moves** (up, then across and down onto the
  counter). One diagonal drags it through the bottle's shoulder.
- **Mobile decided the layout.** At 375px the scene slices to world x 512–928,
  so vial (530–598), flacon (616–824), pipette travel (566→720) and resting cap
  (826–914) all live inside it. The organ and blotters sit outside on purpose.
- `#f4` carries a layout transform:
  `translate(0,115) translate(720,3334) scale(0.76) translate(-720,-3334)`.
  ⚠️ **The canvas is outside that group** — `drawFx` paints the nozzle on
  `#hero-canvas`, so `F4_SCALE`/`F4_DROP`/`F4_ORIGIN` and `f4y()` mirror the
  transform by hand. **Keep them in step; the group's transform is the truth.**

### Screen-space overlays
Both live outside `#world` so the camera does not carry them, and under the
chapter type (HTML alongside the svg) so neither tints the words.

- **`#pan-veil`** — the mabkhara's smoke, passed *through* on the descent to the
  still. Peaks 0.45 on `sin(fallT·π)`. A first pass at 0.9 white-outed the frame.
- **`#chapter-tint`** — cool green forest, warm majlis, smoky blue still, gold
  bench, lerped between chapter centres. ⚠️ **A vignette, not a flat wash.**
  Compositing a mid-tone over near-black lifts the whole frame and flattens the
  contrast the scene depends on.

---

## The drawn objects

### The mabkhara
Olive wood in emerald resin, blackened cup, black foot. **The pieces carry the
surface; the resin is the vein between them** — about a quarter of the face.
11 chunks tiling 656–784 × 1436–1548 exactly, two small fillers so the veins
don't read as a grid. Every piece needs a **dark bark edge** (`#33210C`) or it
looks like paper laid on green. Grain is the whole character of olive wood:
cubic S-curves, 2–3 per chunk, 24 total. Tonal range matters as much as shape —
`#E8DCB4` down to `#9E7534`. The emerald was overshot **both ways** before
landing on `resinGreen`; judge it against a photo, not in isolation.

`f2-wood` carries **no JS** — only the group's opacity is animated — so its
interior is free to redraw. The bounds are not: the cup mouth is held at y 1428
because falling oud is aimed at 1412–1424.

### The flacon
188 × 334, aspect **0.56**, and that number is **the user's eye, not a
measurement**. It has been corrected in both directions. The reference is
backlit gold on gold silk and the glass edges cannot be found in it — a gradient
scan returns scanline widths of 93, 354, 51, 43, 140, 180 and 410 down the same
bottle. **Do not claim to have measured it.**

The **label plate is** measurable (dark borders against bright glass): 295 × 410
in frame, aspect 0.72. Ours is 132 × 183 — **70% of body width**, matching.

- **The cap is polished metal, not gold.** Near-black where it reflects the
  room, blown out where it reflects the light, and the jump is *abrupt*.
  `capMirror` has the hard stops. A gentle ramp reads as anodised plastic.
- **A slab of clear glass under the liquid** — the fill floor is **3300, not
  3328**. Most of why it reads as heavy glass.
- **The atomiser's dip tube** runs neck to base, behind the label plate.
- `capGold` (floor 3's oil vial and its twin on the bench) got the same
  treatment in gold: a flat plateau at `#E5B852` falling to `#433117` within a
  few pixels.
- The label reads **منــدل / *mandle*** — the actual bottle. The product *card*
  says "Mandle" capitalised, which is correct: that's a product name, this is a
  photograph of a label. Arabic in `<tspan lang="ar">`, never `<span>`.

### The woodcutters
Backlit silhouettes — dishdasha in two tones, masar with its tail, rim light on
the +x side. **No interior detail**; against the light it only muddies them.
They were stacked rectangles until the push-in zoomed 2.6× at them.

Four lessons, all **size or tone, never shape**: the robe at 56 wide on a 158
height read as a bell (42 now); the arm must be a step lighter than the robe or
the haft appears to come out of the chest; the rim light must be broken or it
reads as a pole; the axe head at 23×22 was simply enormous — a real one is about
an eighth of a person's height and narrow (15×10 now).

Arm pivots at the **shoulder (4,−124)**. ⚠️ `HERO_STILL_T` is a zero of the
swing sine, so previews always catch the arms at rest.

**Still the weakest thing in the scene** — flat cut-outs, axes never touch the
trunk, two exact mirrors. If it comes up again the better move is structural:
drop the figures and let an axe swing in from off-frame. The cutting is already
carried by the notch, the chips, the shudder and the fleeing birds.

---

## Reduced motion

`prefers-reduced-motion: reduce` does not soften the journey, it **replaces** it.
JS reads the query once into **`heroStill`** and puts **`.reduced-hero`** on
`<html>` — CSS and JS branch off the same flag deliberately.

`heroStill` gates: rAF is never re-armed, `p` is pinned to `HERO_STILL_P`
(0.23 — chapter I, tree complete, camera still on floor 1), the spring is
bypassed, and **the push-in and bloom are switched off** (0.23 sits inside the
bloom window; without the guard the still is a glowing blob on an un-zoomed
tree). `heroTime` is pinned to `HERO_STILL_T = 15/4.4`, a zero of the axe-swing
sine, so the woodcutters are caught between strikes.

Gaps and coda collapse to 0. `staticChapters()` re-homes ht2/ht3/ht4 above the
shelf each introduces and clears the inline styles the one rendered frame left
on them. The strip's `.pg-en` is hidden **only** where a chapter precedes it.

`shmScrollTo` jumps instead of smooth-scrolling. ⚠️ **Assigned to `window` on
purpose** — the whole script is one IIFE and the nav's inline `onclick` resolves
against global scope. As a bare declaration it threw on every click.

---

## Cards and page atmosphere

**The card plate cannot be dark.** The photos are lifestyle shots with their own
light backgrounds, composited `mix-blend-mode: multiply`, which needs a light
ground. Darken it and every photo becomes a bright rectangle in a dark frame.
The plate's *edges* are blended into the card instead
(`.product-image-wrap::after`), turning each from a pale sticker into a lit
alcove. The ground is warmed toward the house palette — and because it
multiplies, that warmth reaches all fifteen photos identically.

**`#page-ambient`** — one fixed layer of three faint warm radials over the whole
page, z-index 4 (above sections, under the nav at 1000), `pointer-events: none`,
transform-only drift, still under reduced motion. ⚠️ **No `mix-blend-mode` on
purpose:** screen-blending is indistinguishable over near-black, but a blended
fixed layer forces the whole page beneath it to recomposite every frame — which
a scroll-driven page cannot spare — and it washes the photographs out.

---

## Tooling in `render/` (in git, excluded from deploy by `.vercelignore`)

| Script | Purpose |
|---|---|
| `check_svg.py` | **Run before every commit.** Scans SVG regions for HTML breakout tags. |
| `preview_chapter4.py` | Renders the scene through the **real** `heroLoop`. `--p 0.95`, `--strip a,b,c`, `--gif`. **Flags exist because these states are unreachable in a still:** `--zoom` (push-in, off when `heroStill`), `--cover 0.53` (strip transition, damped from live rects). |
| `preview_reduced.py` | Writes `_rmtest.html` with the reduced-motion branch forced on. `--rm` deletes it. |
| `preview_flacon.py` | Single flacon still, `--fill 0.5`. |
| `page_shots.py` | Screenshots every section below the hero. Isolates one section per shot — injected `scrollTo` never lands here. |
| `watch_video.py` | Turns a video into frames. Streams; do not accumulate (a 42s 1080×1920 clip is 7.8GB raw). Use `plugin="FFMPEG"` — `pyav` is a different backend and is not installed. |
| `fetch_catalogue.py` / `fetch_categories.py` / `build_catalogue.py` | Pull the 15 products from the store and rebuild the cards. **Use `fetch_categories`, don't infer from descriptions.** |
| `retime_chapters.py` / `retime_chapter4.py` | Threshold retiming, all-or-nothing. |
| `mark_arabic.py`, `make_svg.py`, `make_og.py`, `group_products.py`, `interleave_products.py` | One-shot / asset tooling. |

`imageio` + `imageio-ffmpeg` are installed. The ffmpeg binary lives **inside
site-packages, not on PATH** — plain `ffmpeg` on the command line does not exist.

**Preview render trap:** roughly one capture in seventy fires before the page
paints and returns near-black. It is not the scene — the same `p` re-renders
correctly. `shot_guarded` re-shoots any frame jumping >10 luminance from the
previous. This twice looked like an animation bug.

---

## Products

All 15 pulled from the store, in four groups matching the store's own
categories. Prices, images, links and Arabic come from the store; the **Latin
names are hand-supplied**. Five are out of stock, badged and dimmed.

---

## Open items

1. **The 3ml oil مندلي is still "Mindali".** Its bottle carries only SHAMUM —
   no Latin name — so there is no evidence for any spelling and none was
   invented. If the house romanises مندل as *mandle*, مندلي is probably
   *Mandli*. **Ask before changing.**
2. **`Jawhar`'s card image is a poster, not a photo** — Arabic body copy *and
   the price* (`١٥٠ ريال عماني`) printed into it. If the price changes the card
   is silently wrong. **Flagged at the user's instruction, deliberately
   unchanged.** Needs a different asset from the store.
3. **Product photography.** The 8 JPEGs are lifestyle shots with no isolated
   product to key — they cannot be cut out, and the plate is structural, not a
   workaround. Consistent product photography would fix this properly; nothing
   in CSS will.
4. **Analytics** — still none. Worth one line of Vercel Analytics.
5. **A pre-existing ~126px top overhang** as the scene steps aside at chapter
   IV's end. It predates all recent work and got smaller, not larger. The old
   claim that the lift tuning "clears everything" was never quite true.
6. **The woodcutters** — see above. Structural change, not a fifth redraw.
7. Marwa 3D files (~3 MB, untracked) can be binned.

---

## Rejected — do not retry without new information

- **The finale pull-back** — the camera retreating to show all four floors as
  one column. Built and reverted: *"that zoomout wasnt good i didnt like it."*
- **Scaling the scene for the product strips** — see Scene clearing.
- EEVEE 3D of the flacon — "looks like a Jimmy Neutron animation"
- Synthesising an empty bottle from a product photo — "looks fake"
- The Cycles mabkhara still — the SVG version was preferred
- A cream product panel over the animation — "a whole different page"
- A full-dark product panel — same problem, still covered the scene
