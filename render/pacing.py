# -*- coding: utf-8 -*-
"""How many pixels of scroll each hero beat gets, for a given set of gap heights.

Shortening the journey compresses every beat inside the gap you shorten. The
narrow ones in chapter IV are the constraint: the cap seats over dp 0.008, so a
gap3 that looks generous in viewports can still starve it. This reproduces
measureZones/scrollToP exactly so the numbers are the page's, not an estimate.
"""
import sys

VH = 900.0
STOPS = [0, 0.62, 0.88, 1.0]

# beats worth protecting: (label, p_from, p_to, band index)
BEATS = [
    ("I   push-in",        0.182, 0.214, 0),
    ("I   bloom",          0.206, 0.268, 0),
    ("I   release",        0.258, 0.292, 0),
    ("II  mabkhara in",    0.280, 0.380, 0),
    ("II  oud falls",      0.255, 0.370, 0),
    ("III descent",        0.630, 0.710, 1),
    ("III vapour",         0.740, 0.790, 1),
    ("IV  cap lifts",      0.894, 0.921, 2),
    ("IV  drop falls",     0.930, 0.948, 2),
    ("IV  oud climbs",     0.936, 0.949, 2),
    ("IV  maceration",     0.968, 0.980, 2),
    ("IV  cap seats",      0.980, 0.988, 2),   # tightest beat on the page
    ("IV  press + mist",   0.988, 1.000, 2),
]


def px_per_p(gap1, gap2, gap3):
    """Usable pixels per unit p, per band. Mirrors measureZones()."""
    # band 0 = pinned hero (one viewport) + gap1 ; bands 1,2 = gap2, gap3.
    # Each band's LAST zone reserves one viewport of tail that advances nothing.
    bands = [
        (VH + gap1 * VH / 100.0, STOPS[1] - STOPS[0]),
        (gap2 * VH / 100.0,      STOPS[2] - STOPS[1]),
        (gap3 * VH / 100.0,      STOPS[3] - STOPS[2]),
    ]
    out = []
    for total, dp in bands:
        usable = max(1.0, total - VH)     # the tail
        out.append(usable / dp)
    return out


def report(name, gap1, gap2, gap3, coda):
    pp = px_per_p(gap1, gap2, gap3)
    track = (VH + gap1 * VH / 100.0 + 479 + gap2 * VH / 100.0 + 479
             + gap3 * VH / 100.0 + 479 + coda * VH / 100.0 + 479)
    print("\n%s  gaps %g/%g/%g coda %g" % (name, gap1, gap2, gap3, coda))
    print("  journey %.0fpx = %.1f viewports;  first product strip at %.1f viewports"
          % (track, track / VH, (VH + gap1 * VH / 100.0) / VH))
    worst = None
    for label, a, b, band in BEATS:
        px = (b - a) * pp[band]
        flag = ""
        if px < 90:
            flag = "  <-- TOO FAST"
        elif px < 120:
            flag = "  <-- tight"
        if worst is None or px < worst[1]:
            worst = (label, px)
        print("    %-18s dp %.3f  %6.0f px%s" % (label, b - a, px, flag))
    print("  tightest: %s at %.0fpx" % worst)
    return worst[1]


if __name__ == "__main__":
    report("CURRENT ", 400, 210, 320, 62)
    for g1, g2, g3, cd in [(300, 190, 280, 44), (280, 190, 300, 40), (260, 175, 300, 36)]:
        report("proposed", g1, g2, g3, cd)
