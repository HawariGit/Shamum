"""
Guard against the bug that deleted the hero's cap and perfume bottle.

Certain HTML tags, when they appear inside SVG content, make the HTML parser
break out of foreign content: the <svg> is closed at that point and every
following node is re-parsed as inert HTML. It fails silently — no console
error, no layout break, the nodes are simply HTMLUnknownElements with no
geometry.

This scans every <svg> region in index.html for those tags. <tspan> is the
correct wrapper for text inside SVG; <span> is not.

Usage: python render/check_svg.py     (exit 1 if anything is found)
"""

import re, sys

# HTML spec, "any other start tag" exceptions in foreign content.
BREAKOUT = {
    "b", "big", "blockquote", "body", "br", "center", "code", "dd", "div",
    "dl", "dt", "em", "embed", "h1", "h2", "h3", "h4", "h5", "h6", "head",
    "hr", "i", "img", "li", "listing", "menu", "meta", "nobr", "ol", "p",
    "pre", "ruby", "s", "small", "span", "strong", "strike", "sub", "sup",
    "table", "tt", "u", "ul", "var", "font",
}

SRC = "index.html"
html = open(SRC, encoding="utf-8").read()

regions = [m.span() for m in re.finditer(r"<svg\b.*?</svg>", html, flags=re.S | re.I)]
print("svg regions found: %d" % len(regions))

problems = []
for start, end in regions:
    seg = html[start:end]
    for m in re.finditer(r"<\s*([a-zA-Z][a-zA-Z0-9]*)\b", seg):
        tag = m.group(1).lower()
        if tag in BREAKOUT:
            line = html.count("\n", 0, start + m.start()) + 1
            ctx = seg[max(0, m.start() - 60):m.start() + 60].replace("\n", " ")
            problems.append((line, tag, ctx))

if problems:
    print("\nFOUND %d breakout tag(s) inside SVG — these silently kill "
          "everything after them:" % len(problems))
    for line, tag, ctx in problems:
        print("  line %d: <%s>" % (line, tag))
        print("      ...%s..." % ctx.strip())
    sys.exit(1)

print("clean — no HTML breakout tags inside any <svg>")

# Sanity: the wrappers we do want inside SVG
tspans = len(re.findall(r'<tspan lang="ar">', html))
spans = len(re.findall(r'<span lang="ar">', html))
print("arabic wrappers: %d tspan (inside svg), %d span (html)" % (tspans, spans))
