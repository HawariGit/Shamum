"""
Split the single product grid into per-category groups, in the same order the
hero tells the story: the wood that is burned, then the oil drawn from it,
then the fragrances built on that oil.

Card markup is moved verbatim — only the wrappers around it change.

Usage: python render/group_products.py [--apply]
"""

import re, sys, io

SRC = "index.html"
APPLY = "--apply" in sys.argv
html = open(SRC, encoding="utf-8").read()

start = html.index('<div class="products-grid">')
# Search AFTER the grid opens: 'view-all-btn' also appears in the stylesheet
# far earlier in the file, which produced end < start and an empty slice.
end = html.index('view-all-btn', start)
end = html.rindex('\n', start, end)
grid = html[start:end]
print("grid slice: %d bytes" % len(grid))

# pull the cards out whole
cards = []
i = 0
while True:
    j = grid.find('<div class="product-card"', i)
    if j == -1:
        break
    depth, k = 0, j
    while True:
        nxt_open = grid.find('<div', k)
        nxt_close = grid.find('</div>', k)
        if nxt_close == -1:
            break
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            k = nxt_open + 4
        else:
            depth -= 1
            k = nxt_close + 6
            if depth == 0:
                break
    # keep the preceding comment line if there is one
    cstart = j
    pc = grid.rfind('<!--', 0, j)
    if pc != -1 and grid.find('-->', pc) < j and j - grid.find('-->', pc) < 12:
        cstart = pc
    cards.append(grid[cstart:k])
    i = k

print("cards found: %d" % len(cards))
for c in cards:
    n = re.search(r'class="product-name">([^<]*)<', c)
    s = re.search(r'class="product-size">([^<]*)<', c)
    print("   %-12s %s" % (n.group(1) if n else "?", s.group(1) if s else "?"))

if len(cards) != 6:
    sys.exit("expected 6 cards, aborting")


def by_size(*needles):
    out = []
    for c in cards:
        s = re.search(r'class="product-size">([^<]*)<', c)
        if s and any(n.lower() in s.group(1).lower() for n in needles):
            out.append(c)
    return out


groups = [
    ("bukhoor", "The Bukhoor", "البخــور",
     "Wood cut for the mabkhara — what the majlis actually burns.",
     "https://shamum.com/categories/1005686/أخشـاب-العـود",
     "All Oud Wood · أخشـاب العـود",
     by_size("oud wood")),
    ("oils", "The Oils", "أدهــان العــود",
     "Dehn al oud, drawn a drop at a time and left undiluted.",
     "https://shamum.com/categories/1006197/أدهـان-العـود",
     "All Oud Oils · أدهـان العـود",
     by_size("oud oil")),
    ("fragrances", "The Fragrances", "العطــور",
     "Eau de parfum composed on that oil, and the limited releases.",
     "https://shamum.com/categories/1006199/البـخـاخـات",
     "All Sprays · البـخـاخـات",
     by_size("eau de parfum", "limited")),
]

total = sum(len(g[6]) for g in groups)
print("\ngrouped: %d of %d" % (total, len(cards)))
if total != len(cards):
    sys.exit("some cards were not classified, aborting")

out = []
for gid, en, ar, blurb, href, linktext, gcards in groups:
    print("  %-11s %d card(s)" % (gid, len(gcards)))
    out.append('        <div class="product-group" id="group-%s">' % gid)
    out.append('          <div class="pg-head reveal">')
    out.append('            <span class="pg-ar" lang="ar">%s</span>' % ar)
    out.append('            <h3 class="pg-en">%s</h3>' % en)
    out.append('            <p class="pg-blurb">%s</p>' % blurb)
    out.append('          </div>')
    out.append('          <div class="products-grid">')
    for c in gcards:
        out.append(re.sub(r"^", "  ", c.rstrip(), flags=re.M))
    out.append('          </div>')
    out.append('          <a class="pg-more" href="%s" target="_blank" rel="noopener">%s →</a>'
               % (href, linktext))
    out.append('        </div>')

new = "\n".join(out) + "\n"
result = html[:start] + new + html[end:]

print("\nbytes %d -> %d" % (len(html), len(result)))
if APPLY:
    with io.open(SRC, "w", encoding="utf-8", newline="") as f:
        f.write(result)
    print("WRITTEN")
else:
    print("dry run — pass --apply")
