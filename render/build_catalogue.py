"""
Rebuild the collection section from the store's own data.

Sources, both fetched, neither hand-typed:
  render/out/catalogue.json   — 15 products: Arabic name, price, image, stock
  render/out/categories.json  — which products the store puts in which category

Only the English display names are supplied here, since the store carries no
Latin names. The six that were already on the site keep their existing
spellings so nothing renames itself.

Usage: python render/build_catalogue.py [--apply]
"""

import json, re, sys, io

APPLY = "--apply" in sys.argv
SRC = "index.html"

cat = json.load(open("render/out/catalogue.json", encoding="utf-8"))
cats = json.load(open("render/out/categories.json", encoding="utf-8"))

# Latin names. The first six match what the site already showed.
EN = {
    "منــــــدلـي": "Mindali",
    "جوهــــر": "Jawhar",
    "رازي الثـانـي": "Razi II",
    "منــدل": "Mandle",
    "زاهيـــة": "Zahiya",
    "سُــــرى": "Surra",
    "غانـــدي": "Ghandi",
    "بيـــرون الرابـع": "Bayrun IV",
    "فـراهيــــــد": "Farahid",
    "سينـــا الرابـع": "Sina IV",
    "حدائــق الأزهــــار": "Flower Gardens",
    "المــروى الثاني": "Al-Marwa II",
    "المـــــروى": "Al-Marwa",
    "مجمـوعـة سـرمــد": "Sarmad Collection",
    "إصـدار خـاص": "Special Edition",
}

# What each category's cards say under the name.
SIZE = {"wood": "Oud Wood", "oils": "Oud Oil · 3ml",
        "sprays": "Eau de Parfum", "ltd": "Limited Edition"}

GROUPS = [
    ("bukhoor", "wood", "The Bukhoor", "البخــور",
     "Wood cut for the mabkhara — what the majlis actually burns."),
    ("oils", "oils", "The Oils", "أدهــان العــود",
     "Dehn al oud, drawn a drop at a time and left undiluted."),
    ("fragrances", "sprays", "The Fragrances", "العطــور",
     "Eau de parfum composed on that oil."),
    ("limited", "ltd", "Limited Editions", "إصـدار محـدود",
     "Released once, in small number, and not repeated."),
]

by_ar = {p["name_ar"]: p for p in cat}
missing = []


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def card(p, size_label):
    ar = p["name_ar"]
    en = EN.get(ar)
    if not en:
        missing.append(ar)
        en = ar
    price = ("%.3f" % float(p["price"])) if p["price"] else ""
    sold_out = (p.get("availability") or "").lower() == "outofstock"
    badge = ('\n          <div class="product-badge sold">Sold out</div>'
             if sold_out else "")
    tags = esc(size_label)
    return (
        '        <div class="product-card%s">%s\n'
        '          <div class="product-image-wrap" data-cursor-image>\n'
        '            <img src="%s" alt="%s — %s" loading="lazy">\n'
        '          </div>\n'
        '          <div class="product-info">\n'
        '            <div class="product-meta"><span class="product-size">%s</span></div>\n'
        '            <span class="product-name">%s</span>\n'
        '            <span class="product-arabic"><span lang="ar">%s</span></span>\n'
        '            <span class="product-price">%s <span lang="ar">ر.ع</span></span>\n'
        '            <a class="add-to-bag magnetic" href="%s" target="_blank" rel="noopener">'
        'View Product · <span lang="ar">اكتشف</span></a>\n'
        '          </div>\n'
        '        </div>'
        % (" is-sold-out" if sold_out else "", badge,
           p["image"], esc(en), esc(ar), tags, esc(en), esc(ar), price, p["url"])
    )


out, used = [], set()
for gid, ckey, en_title, ar_title, blurb in GROUPS:
    c = cats[ckey]
    members = []
    for entry in c["products"]:
        p = by_ar.get(entry["name"])
        if p:
            members.append(p)
            used.add(entry["name"])
    print("%-11s %-16s %d card(s)" % (gid, c["label"], len(members)))
    out.append('      <div class="product-group" id="group-%s">' % gid)
    out.append('        <div class="pg-head reveal">')
    out.append('          <span class="pg-ar" lang="ar">%s</span>' % ar_title)
    out.append('          <h3 class="pg-en">%s</h3>' % en_title)
    out.append('          <p class="pg-blurb">%s</p>' % blurb)
    out.append('        </div>')
    out.append('        <div class="products-grid">')
    for p in members:
        out.append(card(p, SIZE[ckey]))
        print("              %-16s %-16s %s" % (EN.get(p["name_ar"], "?"),
              p["price"], p.get("availability")))
    out.append('        </div>')
    out.append('        <a class="pg-more" href="%s" target="_blank" rel="noopener">All %s →</a>'
               % (c["url"], c["label"]))
    out.append('      </div>')

print("\nplaced %d of %d products" % (len(used), len(cat)))
unplaced = [p["name_ar"] for p in cat if p["name_ar"] not in used]
if unplaced:
    sys.exit("NOT PLACED: %s" % ", ".join(unplaced))
if missing:
    sys.exit("no English name for: %s" % ", ".join(missing))

html = open(SRC, encoding="utf-8").read()
start = html.index('<div class="product-group" id="group-bukhoor">')
start = html.rindex("\n", 0, start) + 1
end = html.index("view-all-btn", start)
end = html.rindex("\n", start, end) + 1

result = html[:start] + "\n".join(out) + "\n" + html[end:]
print("bytes %d -> %d" % (len(html), len(result)))

if APPLY:
    with io.open(SRC, "w", encoding="utf-8", newline="") as f:
        f.write(result)
    print("WRITTEN")
else:
    print("dry run — pass --apply")
