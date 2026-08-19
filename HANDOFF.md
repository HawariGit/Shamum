# SHAMUM — session handoff

Everything below is current as of the reduced-motion commit. `main` is in sync
with origin and everything described here is **live on shamum.vercel.app**.

---

## Read this first

1. **Ask for a reference photo before drawing any product.** This cost the
   most time this session. The mabkhara was drawn wrong twice and the oud
   flacon twice, each corrected only when the user sent a photograph. When a
   photo exists, **measure it** — don't eyeball proportions. See
   `render/measure_*` approach below.
2. **The user has strong visual judgement and is right.** Every "this looks
   off" was a real defect with a findable cause. Don't defend, go measure.
3. **The browser pane cannot screenshot, but headless Chrome can.**
   `computer{action:"screenshot"}` still always fails — the pane never
   composites. But `chrome.exe --headless --screenshot` works, and
   `render/preview_flacon.py` uses it to lift the real scene SVG out of
   index.html, park the camera on a floor, set the state, and render a PNG you
   can actually look at. **Use it before claiming any drawing is right.** It
   caught three things reasoning had missed on the flacon: a collar that read
   as dark plastic, a fill with no headspace, and a label plate as wide as the
   bottle. Geometry and timing probes in the pane are still the way to verify
   *animation*; the renderer is for verifying *appearance*.

---

## Deploy

Push to `github.com/HawariGit/Shamum` (main) → Vercel → shamum.vercel.app.
Commits **must** be authored `HawariGit / hawaridata@outlook.com`; the user's
other identity is blocked by Vercel.

Verify live with PowerShell `Invoke-WebRequest`, not the browser pane — the
pane frequently refuses navigation and reports a 0×0 viewport.

---

## Environment traps (all cost real time)

| Trap | Detail |
|---|---|
| **`<span>` inside SVG** | It is on the HTML parser's foreign-content breakout list. A `<span>` inside `<text>` **terminates the `<svg>`** and everything after becomes inert HTML — silently, no console error. This deleted the oil vial's cap and the whole perfume bottle. Use `<tspan>`. `render/check_svg.py` now guards it — **run it before every commit.** |
| **Browser pane viewport = 0×0** | Reports `innerWidth/innerHeight` of 0, so every `vh`/`vw` computes to zero. Always `resize_window` explicitly and re-navigate before measuring. |
| **rAF and IntersectionObserver are dead in the pane** | CSS transitions never settle and IO callbacks never fire. Verified with a fresh observer on a visible element: zero callbacks. Step animation manually via `window.__heroTick(ms)`; inject `transition:none` to read target styles. |
| **`behavior:'smooth'` scrolls do nothing** | rAF-driven. `'auto'` works. To verify smooth-scroll targets, stub `window.scrollTo` and capture the args. |
| **PowerShell mangles quotes** | Heredocs don't exist; `<`, `>`, `"` in `-m` break parsing. **Always write commit messages to a file and use `git commit -F`.** Same for any Python with quotes — write a `.py` file, don't use `python -c`. |
| **`getBoundingClientRect` in probe loops** | Measure all positions up front from scroll 0. Measuring inside a loop that scrolls gives stale rects — this produced two false "mobile is broken" reports. |
| **Blender/Cycles** | `render.engine`'s enum only lists `BLENDER_EEVEE` but assigning `'CYCLES'` works. `transform_apply(scale=True)` also bakes location — pass `location=False, rotation=False`. `primitive_cylinder_add` returns a **capped solid**; hollow it before expecting an interior. CPU only. |
| **Cyrillic lookalikes** | Nearly shipped `#А5642A` with a Cyrillic А in an SVG gradient. SVG drops an invalid stop **silently**. Grep `[Ѐ-ӿ]` if a colour looks wrong. |

---

## Architecture — the hero

`#hero-track` holds a **pinned** `#hero-sticky` (one 1440×900 SVG world, four
900-tall floors) plus alternating scroll zones:

```
gap1 (chapters I–II) → shelf-bukhoor → gap2 (III) → shelf-oils
→ gap3 (IV) → shelf-fragrances → coda → shelf-limited
```

- **`.chapter-gap`** — transparent, advances the animation. `measureZones()`
  counts these.
- **`.chapter-coda`** — deliberately *not* a gap, so it adds scroll without
  advancing `p`. Used to separate the last two strips.
- **`.chapter-products`** — transparent strip, ~53% viewport desktop / 61%
  mobile, one horizontal row of glass cards. The scene stays visible above.

### Chapter bands (`p`)
```
I 0.00–0.30 · II 0.24–0.62 · III 0.62–0.88 · IV 0.88–1.00
```
Within chapter IV: camera reaches floor 4 at 0.918, the bottle settles by
0.925, the fill runs 0.925–0.948, the atomizer is pressed 0.952–0.976 and the
mist hangs 0.960–0.988. The camera used to arrive at 0.94 and the fill ran
0.90–0.948, so the whole fill played out during the pan and the flacon arrived
already full — measured on the page: camera at −1923 and empty, camera at −2695
and 99% full. `render/retime_chapter4.py` records that change.

Zone boundaries are pinned to these via `STOPS = [0, 0.62, 0.88, 1]`. Each
gap finishes its chapter **one viewport early** (`tail`) so the strip never
covers a running animation. If you retime a chapter, use
`render/retime_chapters.py` — it refuses to run unless every threshold
matches exactly once.

### Scene clearing
`shelfCover` = fraction of a strip inside the frame (ramps **both** ways —
an earlier `1 - top/vh` pinned at 1 then dropped to 0 in one frame, which was
a visible cut). Damped at `dt * 7.5`, eased with `sstep`. Drives:
- `titleMute` — chapter title fades out by 40% cover
- scene `translate3d` lift 0.15·vh + `scale` 1 − 0.30

Those two numbers came from sweeping lift × shrink over all three chapters and
scoring worst-overlap + worst-clipping. **0.15/0.30 is the only pair that
clears every heading with nothing running off the top.** More lift clips the
flacon; less shrink leaves the mabkhara in the heading.

### The chapter IV flacon
Clear glass with a light gold eau de parfum that fills as the chapter plays —
`f4-liquid` is a rect clipped to `flaconClip` whose top edge is driven up, with
`f4-surface` riding it as a meniscus. Exactly the mechanism floor 3 uses for
the oil, and deliberately so.

Colours were measured off the store's product shot, not chosen: lit liquid
`#C6A66A`, saturated body `#8B5000`, pool at the base `#521F03`. `flaconLiquid`
runs pale at the surface to deep at the base because that is what absorption
through more liquid does. The body was `#1A1006 → #0A0502`, near-black, which
is what prompted the change.

The label is a solid plate again. It was a thin gold outline, which read
cleanly on a black bottle and is gold-on-gold over a light fill; the product
shot shows a plate anyway. Its width was measured too — the real plate is 126
of a 245-wide body, 51%. Ours is 106 of 208, the same 51%, once the body was
widened enough to carry it.

It reads **منــدل / *mandle*** — the actual bottle, at the user's request, not
the house name. Lowercase italic Cormorant Garamond for the Latin because that
is what is on the glass; the product *card* still says "Mandle" capitalised,
which is correct — that is a product name, this is a photograph of a label.
The Arabic is 18 to the Latin's 17, giving it the primacy it has on the bottle.
Both must stay in `<tspan lang="ar">`, never `<span>` — see the breakout trap.

**Proportion.** The body is 208 × 334, an aspect of 0.62. It was 144 × 334
(0.43) and read far slimmer than the real bottle; measured off the product shot
with the base in frame, the real body is about 273 × 310. 0.62 is deliberately
conservative against that, because the photograph is a tilted 3/4 view that
foreshortens the height.

**Only the width changed.** The scene-clearing tune (lift 0.15, shrink 0.30)
was chosen against a 584px-tall flacon and clips it if anything grows upward,
so every height is exactly as it was and that tuning still holds. The cap and
collar also kept their width: on the real bottle they sit on a narrow neck and
the shoulder flares hard to a much wider body, and that flare is most of what
makes it read as *this* bottle. The shoulder is a cubic so the flare from an
84-wide neck to a 208-wide body is a curve, not a corner.

Widening it moved four things that are easy to forget: `bottleClip`, the spark
positions (they sat where the glass now is), the base shadow ellipse and floor
glow, and the shimmer sweep range. The meniscus `rx` is now driven too — the
bottle is not a tube, so a fixed `rx` poked through the glass once the level
climbed into the shoulder. Checked on mobile: at 375px the slice shows world x
512–928 and the bottle spans 616–824, so it still fits with margin.

### Reduced motion
`prefers-reduced-motion: reduce` does not soften the journey, it replaces it.
A scrub either drives the camera or it does not, so under reduce the whole
apparatus is off:

- JS reads the query once into **`heroStill`** and puts **`.reduced-hero`** on
  `<html>`. CSS and JS branch off the same flag deliberately — a media query
  on one side and matchMedia on the other could disagree about which layout is
  on screen.
- `heroStill` gates three things in `heroLoop`: rAF is never re-armed, `p` is
  pinned to `HERO_STILL_P` instead of read from scroll, and the spring is
  bypassed (one frame of a spring stops short of the frame you chose).
- The still is **chapter I at p 0.23** — tree complete, wound open, roots just
  showing, camera still on floor 1 (`camY` is 0 below 0.24) and the title at
  full opacity, since it starts fading at 0.235. `heroTime` is pinned to
  `HERO_STILL_T` = 15/4.4, a zero of `sin(heroTime · 2.2 · 2π)`, which is the
  beat the axe swing and trunk shudder run on — so the woodcutters are caught
  between strikes rather than frozen mid-swing. Camera breathing is skipped for
  the same reason; left on it parked the still 2.3px off the floor.
- Chips and birds are hidden. Held still they are debris in the air.
- Gaps and the coda collapse to 0. `measureZones` returns no zones.
- `staticChapters()` re-homes **ht2/ht3/ht4** in the document above the shelf
  each introduces (II→bukhoor, III→oils, IV→fragrances) and clears the inline
  styles the one rendered frame left on them — which for II–IV is opacity 0.
  Chapter I stays put as the title over the still.
- The strip's own `.pg-en` is hidden **only** where a chapter precedes it
  (`.ch-static + .chapter-products .pg-en`), because otherwise the two headings
  stack — "The Bukhoor" twice, 364px apart. That is the same collision
  `titleMute` exists to prevent in the animated version. Limited Editions has
  no chapter above it and keeps its heading.
- `shmScrollTo(y)` jumps instead of smooth-scrolling under reduce. **It is
  assigned to `window` on purpose** — the whole script is one IIFE, so the
  nav's inline `onclick` cannot see a bare declaration and would throw.

Verify it with `render/preview_reduced.py`, not by trusting the pane's media
query — the pane reports no preference. rAF being dead in the pane does not
matter here: the still is drawn by a direct `heroLoop(0)` call.

---

## Tooling in `render/` (in git, excluded from deploy by `.vercelignore`)

| Script | Purpose |
|---|---|
| `check_svg.py` | **Run before every commit.** Scans SVG regions for HTML breakout tags. Exits 1 on a hit. |
| `fetch_catalogue.py` | Pulls all 15 products from the store's schema.org data → `render/out/catalogue.json` |
| `fetch_categories.py` | Asks the store which products are in which category. **Use this, don't infer from descriptions** — Ghandi is Oud Wood, and Mandle is a spray despite its description leading with dehn al oud. |
| `build_catalogue.py` | Rebuilds the product cards from those two JSONs |
| `interleave_products.py` | Restructured the hero into gaps + strips |
| `retime_chapters.py` | Chapter threshold retiming, all-or-nothing |
| `mark_arabic.py` | Wraps Arabic in `lang="ar"` (`tspan` inside SVG) |
| `make_svg.py` | Arabic calligraphy → SVG paths via harfbuzz |
| `make_og.py` | Regenerates `assets/og-image.jpg` |
| `preview_flacon.py` | Renders the hero scene to a real PNG via headless Chrome. `--fill 0.5` for a part-filled flacon. **The only way to actually see the artwork here.** |
| `retime_chapter4.py` | Record of the chapter IV retiming that made the fill visible |
| `preview_reduced.py` | Writes `_rmtest.html` — index with the reduced-motion branch forced on. The only way to see that build without toggling the OS setting. `--rm` deletes it. |
| `mabkhara.py` | Blender/Cycles still — **not used on the site** |

---

## Products

All 15 pulled from the store, in four groups matching the store's own
categories. Prices/images/links/Arabic all come from the store — only the
**Latin names are hand-supplied** (the store carries none).

Five are out of stock, badged and dimmed. **Al-Marwa and Al-Marwa II are
back on the page** — the user said Marwa was discontinued, the store agrees
(both out of stock) but still lists them. Flagged, not resolved.

---

## Open items

1. ~~**"Mindal" vs "mandle"**~~ — **resolved.** The bottle photo was measured:
   the label reads *mandle* under مندل, so the EDP is now **Mandle**, in both
   `index.html` and `build_catalogue.py`. **Left open:** the 3ml oil مندلي is
   still "Mindali". Its bottle carries only SHAMUM — no Latin name at all — so
   there is no evidence for any spelling and none was invented. If the house
   romanises مندل as *mandle*, مندلي is probably *Mandli*; ask before changing.
2. ~~**Marwa**~~ — **decided: leave as-is.** Both stay listed, badged and
   dimmed with the other three sold-out items.
3. **Product photo backgrounds** — 8 of 15 are JPEGs with white baked in, so
   cards keep a lit plate. If the user wants bottles floating directly on the
   dark, those 8 need re-exporting with transparency (a photo job).
4. **Analytics** — still none. The user is "showing the boss"; worth one line
   of Vercel Analytics.
5. **Pacing dial** — gap heights are 400/210/**260**vh desktop, 330/180/**225**vh
   mobile. Independent of timing, safe to tune. Note `400vh` here means 400% of
   the viewport, i.e. **4 viewports**, not 400 of them — the whole hero journey
   is about 12.4 viewports of scroll, not 1175.
6. ~~**`prefers-reduced-motion`**~~ — **done**, hero included. See the
   Reduced motion section above.
7. Marwa 3D files (~3 MB, untracked) can be binned.

---

## Rejected — do not retry without new information

- EEVEE 3D of the flacon — "looks like a Jimmy Neutron animation"
- Synthesising an empty bottle from a product photo — "looks fake"
- The Cycles mabkhara still — the SVG version was preferred
- A cream product panel over the animation — "a whole different page"
- A full-dark product panel — same problem, still covered the scene
