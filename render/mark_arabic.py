"""
Wrap every run of Arabic text in index.html with <span lang="ar">.

Why lang but NOT dir: the bug is that <html lang="en"> makes screen readers
voice Arabic with an English voice, which is unintelligible. lang="ar" fixes
pronunciation and changes nothing visually. dir="rtl" WOULD change layout —
on a price like "107.000 ر.ع" it flips the currency to the other side of the
number — and the bidi algorithm is already laying these out correctly. So
lang only.

Only text between > and < is touched, so attribute values (hrefs carrying
Arabic slugs, alt text, aria-labels) are never rewritten. Script, style and
title regions are excluded outright.

Idempotent: a run already inside a lang="ar" span is skipped.

Usage: python render/mark_arabic.py [--apply]
"""

import re, sys, io

SRC = "index.html"
APPLY = "--apply" in sys.argv

AR_RANGES = (
    (0x0600, 0x06FF), (0x0750, 0x077F),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
)
# punctuation allowed to sit *between* Arabic characters without breaking a run
JOINERS = set(" \t .،؛؟—–-·:()[]«»/‏‎")


def is_ar(ch):
    o = ord(ch)
    return any(a <= o <= b for a, b in AR_RANGES)


def runs(text):
    """Maximal [start, end) spans of Arabic, joined across neutral punctuation."""
    idx = [i for i, c in enumerate(text) if is_ar(c)]
    if not idx:
        return []
    out, s, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        gap = text[prev + 1:i]
        if all(c in JOINERS for c in gap):
            prev = i
            continue
        out.append((s, prev + 1))
        s = prev = i
    out.append((s, prev + 1))
    return out


def protected_spans(html):
    """Regions we must not rewrite: script, style, title, existing ar spans."""
    spans = []
    for m in re.finditer(r"<script\b.*?</script>|<style\b.*?</style>|<title\b.*?</title>",
                         html, flags=re.S | re.I):
        spans.append(m.span())
    for m in re.finditer(r'<span lang="ar">.*?</span>', html, flags=re.S):
        spans.append(m.span())
    return spans


def main():
    html = open(SRC, encoding="utf-8").read()
    prot = protected_spans(html)

    def guarded(pos):
        return any(a <= pos < b for a, b in prot)

    edits = []           # (start, end, replacement)
    for m in re.finditer(r">([^<>]+)<", html):
        text = m.group(1)
        base = m.start(1)
        if guarded(base) or not any(is_ar(c) for c in text):
            continue
        for s, e in runs(text):
            frag = text[s:e]
            edits.append((base + s, base + e,
                          '<span lang="ar">%s</span>' % frag))

    edits.sort(key=lambda t: t[0], reverse=True)
    out = html
    for s, e, rep in edits:
        out = out[:s] + rep + out[e:]

    print("Arabic runs found : %d" % len(edits))
    print("bytes %d -> %d" % (len(html), len(out)))
    samples = [rep for _, _, rep in sorted(edits, key=lambda t: t[0])][:8]
    for s in samples:
        print("   ", s[:64])

    if APPLY:
        with io.open(SRC, "w", encoding="utf-8", newline="") as f:
            f.write(out)
        print("\nWRITTEN to %s" % SRC)
    else:
        print("\ndry run — pass --apply to write")


main()
