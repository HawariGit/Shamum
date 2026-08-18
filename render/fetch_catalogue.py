"""
Pull the full catalogue from the Zid store into render/out/catalogue.json.

The store's /products page carries a schema.org ItemList naming every product
and its URL; each product page then carries a Product block with price,
image and description. Both are server-rendered, so this needs no browser.

Usage: python render/fetch_catalogue.py
"""

import json, re, os, time, urllib.request, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (compatible; shamum-site-build/1.0)"}
OUT = "render/out/catalogue.json"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def ld_blocks(html):
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                         html, re.S):
        try:
            yield json.loads(m.group(1).strip())
        except Exception:
            pass


def walk(node):
    """Yield every dict in a nested JSON structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


print("fetching index …")
index_html = get("https://shamum.com/products")

items = []
for blk in ld_blocks(index_html):
    for d in walk(blk):
        if d.get("@type") == "ItemList":
            for el in d.get("itemListElement", []):
                if el.get("url"):
                    items.append({"name": el.get("name", "").strip(),
                                  "url": el["url"]})
print("products listed: %d" % len(items))

catalogue = []
for i, it in enumerate(items, 1):
    safe = urllib.parse.quote(it["url"], safe=":/")
    try:
        page = get(safe)
    except Exception as e:
        print("  [%2d] FAILED %s (%s)" % (i, it["name"][:22], e))
        continue

    rec = {"name_ar": it["name"], "url": it["url"],
           "price": None, "currency": None, "image": None,
           "sku": None, "description": None, "availability": None}

    for blk in ld_blocks(page):
        for d in walk(blk):
            if d.get("@type") != "Product":
                continue
            rec["name_ar"] = (d.get("name") or rec["name_ar"]).strip()
            desc = d.get("description")
            if desc:
                rec["description"] = re.sub(r"\s+", " ", desc).strip()
            img = d.get("image")
            if isinstance(img, list):
                img = img[0] if img else None
            if isinstance(img, dict):
                img = img.get("url")
            if img:
                rec["image"] = img
            rec["sku"] = d.get("sku") or rec["sku"]
            offers = d.get("offers")
            for o in walk(offers) if offers else []:
                if o.get("price") is not None:
                    rec["price"] = str(o["price"])
                    rec["currency"] = o.get("priceCurrency")
                    rec["availability"] = (o.get("availability") or "").split("/")[-1]
                    break

    catalogue.append(rec)
    print("  [%2d] %-28s %-10s %s" % (
        i, rec["name_ar"][:28],
        (rec["price"] or "?") + " " + (rec["currency"] or ""),
        "img" if rec["image"] else "NO IMAGE"))
    time.sleep(0.3)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(catalogue, f, ensure_ascii=False, indent=2)

print("\nwrote %s  (%d products)" % (OUT, len(catalogue)))
missing = [c["name_ar"] for c in catalogue if not c["price"] or not c["image"]]
if missing:
    print("incomplete records: %s" % ", ".join(m[:18] for m in missing))
