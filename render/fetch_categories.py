"""
Ask the store which products are in which category, rather than guessing from
descriptions. Writes render/out/categories.json.
"""

import json, re, os, urllib.request, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (compatible; shamum-site-build/1.0)"}

CATS = [
    ("wood",   "1005686", "أخشـاب-العـود",  "Oud Wood"),
    ("oils",   "1006197", "أدهـان-العـود",  "Oud Oils"),
    ("sprays", "1006199", "البـخـاخـات",    "Sprays"),
    ("ltd",    "1333233", "إصـدار-محـدود",  "Limited Edition"),
]


def get(url):
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&"), headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def ld(html):
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                         html, re.S):
        try:
            yield json.loads(m.group(1).strip())
        except Exception:
            pass


def walk(n):
    if isinstance(n, dict):
        yield n
        for v in n.values():
            yield from walk(v)
    elif isinstance(n, list):
        for v in n:
            yield from walk(v)


out = {}
for key, cid, slug, label in CATS:
    url = "https://shamum.com/categories/%s/%s" % (cid, slug)
    try:
        html = get(url)
    except Exception as e:
        print("%-7s FAILED (%s)" % (key, e))
        continue
    urls = []
    for blk in ld(html):
        for d in walk(blk):
            if d.get("@type") == "ItemList":
                for el in d.get("itemListElement", []):
                    if el.get("url"):
                        urls.append({"name": el.get("name", "").strip(), "url": el["url"]})
    out[key] = {"id": cid, "label": label, "url": url, "products": urls}
    print("%-7s %-16s %2d product(s)" % (key, label, len(urls)))
    for u in urls:
        print("            %s" % u["name"])

os.makedirs("render/out", exist_ok=True)
with open("render/out/categories.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\nwrote render/out/categories.json")
