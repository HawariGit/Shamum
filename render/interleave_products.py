"""
Interleave the collection with the hero chapters.

Before: one 800vh hero playing all four chapters, then a single #products
section holding every group.
After:  #hero-track holds the pinned hero plus three .chapter-gap scroll
        zones, each followed by a .chapter-products panel carrying the
        groups that belong to the chapter just watched.

  gap 1  chapters I–II, the tree and the mabkhara   -> The Bukhoor
  gap 2  chapter III, the distillation              -> The Oils
  gap 3  chapter IV, the perfume                    -> The Fragrances
                                                       Limited Editions

Usage: python render/interleave_products.py [--apply]
"""

import re, sys, io

APPLY = "--apply" in sys.argv
SRC = "index.html"
html = open(SRC, encoding="utf-8").read()


def block(src, start_idx):
    """Return the full <div>…</div> beginning at start_idx."""
    depth, k = 0, start_idx
    while True:
        o = src.find("<div", k)
        c = src.find("</div>", k)
        if c == -1:
            raise ValueError("unbalanced")
        if o != -1 and o < c:
            depth += 1
            k = o + 4
        else:
            depth -= 1
            k = c + 6
            if depth == 0:
                return src[start_idx:k]


# ── pull the four groups out of the current products section ──
groups = {}
for gid in ("bukhoor", "oils", "fragrances", "limited"):
    m = re.search(r'<div class="product-group" id="group-%s">' % gid, html)
    if not m:
        sys.exit("group-%s not found" % gid)
    groups[gid] = block(html, m.start())
    print("group-%-11s %6d bytes" % (gid, len(groups[gid])))

# ── the whole old <section id="products"> … </section> ──
ps = html.index('<section id="products"')
pe = html.index("</section>", html.index("view-all-btn", ps)) + len("</section>")
old_products = html[ps:pe]
print("\nold products section: %d bytes" % len(old_products))

# keep its header (eyebrow + title + ornament) for the first panel
hm = re.search(r'<div id="products-header">', old_products)
header = block(old_products, hm.start()) if hm else ""
print("header kept: %d bytes" % len(header))

# ── where does #hero-sticky close? ──
hs = html.index('<div id="hero-sticky">')
hero_sticky = block(html, hs)
hero_end = hs + len(hero_sticky)
print("hero-sticky: %d bytes" % len(hero_sticky))

PANELS = [
    (1, "bukhoor", ["bukhoor"], True),
    (2, "oils", ["oils"], False),
    (3, "fragrances", ["fragrances", "limited"], False),
]

parts = []
for n, pid, gids, with_header in PANELS:
    parts.append('\n\n  <div class="chapter-gap" data-chapter="%d" aria-hidden="true"></div>\n' % n)
    parts.append('  <section class="chapter-products" id="shelf-%s">\n' % pid)
    if with_header:
        parts.append(re.sub(r"^", "    ", header, flags=re.M) + "\n")
    for g in gids:
        parts.append(re.sub(r"^", "    ", groups[g], flags=re.M) + "\n")
    parts.append("  </section>")

insert = "".join(parts) + "\n"

# ── rebuild ──
new = html[:hero_end] + insert + html[hero_end:]
# rename the container
new = new.replace('<div id="hero-spacer">', '<div id="hero-track">', 1)
# drop the old products section (offsets shifted by the insert)
ps2 = new.index('<section id="products"')
pe2 = new.index("</section>", new.index("view-all-btn", ps2)) + len("</section>")
removed = new[ps2:pe2]
# strip trailing blank line left behind
line_start = new.rindex("\n", 0, ps2) + 1
new = new[:line_start] + new[pe2:].lstrip("\n")

print("\nremoved old section: %d bytes" % len(removed))
print("bytes %d -> %d" % (len(html), len(new)))

# sanity
for gid in groups:
    if new.count('id="group-%s"' % gid) != 1:
        sys.exit("group-%s appears %d times after rebuild" % (gid, new.count('id="group-%s"' % gid)))
if new.count('class="product-card') != 15:
    sys.exit("expected 15 cards, found %d" % new.count('class="product-card'))
if 'id="hero-spacer"' in new:
    sys.exit("hero-spacer id still present")
print("checks passed: 15 cards, 4 groups, 3 panels, container renamed")

if APPLY:
    with io.open(SRC, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print("WRITTEN")
else:
    print("dry run — pass --apply")
