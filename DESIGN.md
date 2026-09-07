# Design System — SHAMUM

> **This documents a system that already exists.** Every value here was read out of
> `index.html`, not chosen for this document. Where the code and this file disagree,
> **the code is right and this file is stale** — fix it here.
>
> Scope: `index.html` is a single ~314KB vanilla file. No framework, no build step,
> no CSS preprocessor. That is deliberate and is not a gap to be closed.

---

## 1. Visual theme and atmosphere

A dark, cinematic brand site for an Omani oud house. The register is **reverent and
slow**: near-black grounds, a single warm metal accent, generous emptiness, and one
long scroll-driven journey that behaves like a camera move rather than a page.

It is not a marketing landing page wearing a luxury skin. The first eleven viewports
are a four-chapter narrative — tree, mabkhara, still, perfumer's bench — with commerce
deliberately downstream of the story.

| Dial | Value | Reading |
|---|---|---|
| **Visual density** | **2** — art-gallery airy | Whole viewports carry one object and one line of type |
| **Design variance** | **6** — offset, not chaotic | Composition is largely centred *on purpose*; the variance is in scale and pacing, not in grid-breaking |
| **Motion intensity** | **8** — cinematic choreography | A bespoke scroll-driven engine, spring-damped, with a full reduced-motion replacement |

⚠️ **Centred composition is a decision, not an oversight.** Generic taste checklists
ban centred heroes. Here the subject is a single object on a stage — a censer, a still,
a flacon — and the camera frames it centrally the way a product photograph would.
Breaking that symmetry would fight the premise.

---

## 2. Colour palette and roles

One accent family. **Gold is the only live accent** (`--gold-400` appears 27 times);
everything else is ground, ink, or a tint of the same warm ramp. No second accent, no
cool/warm mixing.

### Ground
| Token | Hex | Role |
|---|---|---|
| `--ink` | `#15100A` | Page background. Warm near-black, never `#000000` |
| `--oud-900` | `#241810` | Raised surfaces, product plate depth |
| `--oud-800` | `#342517` | Highest ground tint |
| *(hero stage)* | `#0F0805` | `#hero-sticky` background — deeper than `--ink` so the scene reads as a lit stage |

### Metal — the accent ramp
| Token | Hex | Role |
|---|---|---|
| `--bronze` | `#6E5328` | Deepest metal, hairlines |
| `--gold-600` | `#8C6E3A` | Borders, dividers |
| `--gold-500` | `#AE8B4F` | Secondary metal, control strokes |
| `--gold-400` | `#C2A368` | **Primary accent.** Eyebrows, links, active state |
| `--gold-300` | `#D4BC86` | Brightest metal. Arabic display type, focus ring |

### Ink on dark
| Token | Hex | Role |
|---|---|---|
| `--sand-100` | `#F4EAD2` | Secondary text |
| `--sand-50` | `#FBF6EA` | Primary text and display type |

### Gold is the only colour
Two sage tokens were sampled from the boutique's velvet chairs and never landed:
`--teal` (`#8FB5AC`) had zero uses, and `--teal-deep` (`#2E4A43`) styled
`.product-badge.limited` — a class **no element on the page carries** (only `.sold`
exists, five times). Both the tokens and that rule were removed on 2026-09-07.

**The page now has exactly one colour family: the gold ramp, over warm neutrals.**
Do not reintroduce a second accent casually. If sage is ever wanted, it needs to appear
in more than one place and be documented here first.

### On the palette bans in generic checklists
Automated taste rules ban "warm cream + brass + espresso" as an AI default for premium
consumer briefs, and SHAMUM's `#FBF6EA` / `#C2A368` / `#15100A` sit squarely in those
banned families. **The override applies and is documented here so it is not re-litigated:**
this palette is sampled from the brand's own gold wordmark and its own warm photography.
Oud is resinous wood. The colours are the product.

---

## 3. Typography

Two faces, both loaded from Google Fonts.

| Role | Face | Notes |
|---|---|---|
| **Display** | `Cormorant Garamond`, serif | Weights 300–600, italic used for chapter headings. Light weight at large size — the scale carries it, not the weight |
| **Body / UI** | `Jost`, sans-serif | Weights 300–500. All labels, nav, product copy, prices |

**Arabic** sets in the same faces and must be wrapped `lang="ar"`. Inside SVG it must be
`<tspan lang="ar">` — **never `<span>`**, which silently terminates the `<svg>`.

### Scale
Everything fluid via `clamp(min, vw, max)`. The live range runs from
`clamp(18px, 2vw, 24px)` up to `clamp(30px, 4.4vw, 58px)`. Never set a fixed display size.

### Conventions
- **Uppercase eyebrows** carry `letter-spacing: 0.34em` and sit at 10px. This is the
  house label convention.
- **Display type is never uppercase.** Sentence case, often italic.
- Prices and counters use `font-variant-numeric: tabular-nums` so digits align down a
  row of cards.
- Display faces carry `text-wrap: balance` to prevent one-word last lines.

### On the serif
Generic checklists ban Garamond by name. **Cormorant Garamond is correct here** and the
justification is the narrow one those rules allow: a heritage luxury house where the
brand is the typography. It is not reached for because "creative brief = serif."

---

## 4. Components

- **Buttons / links** — flat, no glow. Gold hairline border, gold text, background
  lifts on hover. No filled primary buttons anywhere on the page.
- **Product cards** — ⚠️ **the card plate cannot be dark.** Product photos are lifestyle
  shots with their own light backgrounds, composited `mix-blend-mode: multiply`, which
  requires a light ground. Darken the plate and every photo becomes a bright rectangle
  in a dark frame. The plate's *edges* are blended into the card instead
  (`.product-image-wrap::after`), turning each from a pale sticker into a lit alcove.
- **Focus** — `:focus-visible` only, so a mouse click never draws it: a 2px `--gold-300`
  ring at 3px offset, with a `rgba(8,4,2,0.72)` outer halo so it reads on both the dark
  hero and the light product plate.
- **Skip link** — first child of `<body>`, `z-index: 6000` so it clears the entry veil.

### Z-index scale
Layers are grouped, not arbitrary. Within the hero stage: photographic ground `0`,
SVG scene `1`, particle canvas `2`, grade `3`, grain `4`, vignette `5`, logo `10`,
chapter type `11`. Page chrome: nav `1000`, sticky bar `1400–1601`, menu `3000`,
entry veil `5000`, skip link `6000`.

---

## 5. Layout

- **Breakpoints** — `900px`, `768px`, `640px`, plus narrow fixes at `560/470/380px`.
  `640px` is the main one (12 rules).
- **The hero is pinned, not stacked.** `#hero-track` holds a sticky `#hero-sticky`
  alternating with transparent scroll zones. `height: 100vh` is intentional:
  a `dvh` sticky resizes as mobile browser chrome hides, which reflows the pinned
  scene mid-scroll — worse than the bug it fixes.
- **Overlap is used deliberately.** The product strip's heading overlaps its subject by
  roughly 49px on every chapter. That is the point: the scene has dimmed to 45% and is
  tonally subordinate.

---

## 6. Motion

- **House easing: `cubic-bezier(0.16, 1, 0.3, 1)`** — used 41 times. A fast, decelerating
  ease-out. This is the site's signature; do not introduce a second general-purpose curve.
- **Scroll spring** — critically damped, `acc = (raw - sPos) * 80 - sVel * 18`, integrated
  per frame. The scene eases toward the scroll position rather than tracking the wheel.
- **Scene clearing** — `shelfCover` damped at `dt * 7.5`, eased `sstep`.
- **Reveal** — `opacity` + `translateY(40px)` over `0.9s` on the house curve.
- **Chapter stops** — `STOPS = [0, 0.62, 0.88, 1]`.
- Animate **`transform` and `opacity` only.** Scroll handlers are rAF-coalesced: reading
  layout per scroll event thrashes on a page whose premise is smooth scrolling.

### Reduced motion is a replacement, not a softening
`prefers-reduced-motion: reduce` sets `heroStill` in JS and `.reduced-hero` on `<html>`.
The journey does not slow down — it becomes **one composed still frame** at
`HERO_STILL_P = 0.23`. Scroll gaps collapse to zero, the spring is bypassed, the push-in
and bloom are switched off, and chips, bark dust and birds are `display: none` because
frozen debris hanging in mid-air is worse than no debris. **Any new moving part must be
added to that hide list.**

---

## 7. The photographic ground

The house's own photography sits **under** the drawn SVG scene at `z-index: 0`, one plate
per chapter, cross-fading with the **camera** (keyed to each floor's `camY`), not with the
chapter text.

Rules learned by getting them wrong:

- **Exposure is per plate, set inline** — never shared. One brightness cannot serve a
  bright smoke plume and a dark bottle. Current: bukhoor `0.34`, oud bottle `0.82`,
  gift chest `0.40`.
- **Held far back** — 0.55 peak opacity, `saturate(0.55)`, 9px blur (18px on the bottle,
  which is the only plate carrying legible text). At these values a photograph reads as
  depth and material rather than as a picture, which is what lets the real mabkhara sit
  behind the drawn one without reading as a second censer.
- **No legible human figures.** A person survives blurring and reads as a person however
  far back you push them.
- **Chapter I is agarwood** (`assets/agarwood.webp`), cropped from the bottom third of
  Jawhar's product poster, which is a real photograph of resinous heartwood. It is the
  tree's own material, so it is the most literally correct ground the story could carry.
  Being a product shot on **cream** it takes by far the deepest grade in the set
  (brightness `0.17`, blur `26px`) — at moderate blur the pale ground reads as a bright
  band behind a dark forest, which is tonally backwards. It also ramps in with the tree
  (`seg(p, 0.10, 0.21)`) because floor 1 shares `camY 0` with the opening plate.
- **Film grain** over the whole frame at `0.13` gives flat vector and photograph the same
  noise floor so they read as one surface. No `mix-blend-mode` — blending over near-black
  is invisible and forces a full-page recomposite every frame.

---

## 8. Anti-patterns — banned in this project

- **`<span>` inside SVG.** Terminates the `<svg>` silently. Use `<tspan>`.
  Run `render/check_svg.py` before every commit.
- **A second accent colour.** Gold is the accent. See the dead teal tokens above.
- **Pure `#000000`.** Grounds are warm near-black.
- **Scaling the scene for the product strips.** A scaled full-bleed element cannot cover
  the frame, and the vignette does not scale with it. The scene **dims**, never shrinks.
- **An opaque panel over the animation.** Cream and full-dark were both tried and failed
  identically; the fault is the panel, not its colour.
- **`100dvh` on the pinned hero.** See §5.
- **Dark product-card plates.** See §4.
- **Reintroducing removed figures.** The woodcutters were cut; the strike is carried by
  the trunk's ring, bark dust and chips.
- **AI copy clichés** — "Elevate", "Seamless", "Unleash", "Next-Gen". The copy voice is
  plain and largely drawn from SHAMUM's own film.

---

## 9. Known gaps

These are asset and content gaps, not design decisions. None is fixable in CSS.

1. ~~No photograph of agarwood.~~ **Closed 2026-09-07.** One existed all along, inside
   Jawhar's poster. A photograph of the standing *tree* or a forest would still be a
   better opening image than a crop of chips on paper.
2. **`assets/oud-oil.webp` is upscaled from a 204×289 screenshot,** not the original
   photograph. Invisible under 18px of blur; useless for anything sharp.
3. **`Jawhar`'s card image is a poster,** with body copy and the price printed into the
   pixels. If the price changes the card is silently wrong. The store has no alternative
   image. Left as-is by explicit instruction.
4. **Product photography generally.** The lifestyle shots have no isolated product to key,
   so they cannot be cut out. The light plate is structural, not a workaround.
5. **No analytics.** `/_vercel/insights/script.js` returns 404 — Web Analytics is not
   enabled on the Vercel project.

---

## 10. Where the real documentation lives

`HANDOFF.md` is the operational document: architecture, the environment traps that cost
hours, the tooling in `render/`, and the record of what was tried and did not land.
**Read it before changing the hero.** This file describes the design language; that one
describes the machine.
