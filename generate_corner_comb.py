#!/usr/bin/env python3
"""
Fatif Adapter — Corner Radius Test Comb (SendCutSend-ready)

Generates a DXF of connected "combs" for verifying the actual corner radii of
the Fatif DS 20x25 casting before committing to finished re-fabrication.

Each comb is a spine bar with a row of teeth; every tooth is one convex rounded
corner (a candidate radius) with two 90-degree registration flats. Drop a tooth
corner into the matching casting corner, register the flats against the casting
flats, and find the radius that seats flush -- no diagonal tip interference and
no corner gap. Then measure the winning flat length to back-check.

Two combs:
  OUTER (front + middle, 171.5 profile): R52.0..54.0  (calc R53.36)
  REAR  (160 profile):                   R46.5..48.0  (calc R47.41)

The 45-degree corner setback is s = R*(sqrt(2)-1), so a measured diagonal
interference dd maps to dR = 2.414*dd -- that amplification plus the laser
tolerance (~0.13mm) is why we bracket in 0.5mm steps rather than trust one blank.

SendCutSend setup (verified against their current guidelines):
  * Upload this DXF, NOT a PDF. Instant-price 2D formats are dxf/dwg/eps/ai;
    PDF is custom-quote only.
  * Each comb is ONE connected part (teeth on a spine), so the order is 2 parts
    pre-nested in one file -- far cheaper than 9 loose gauges (per-part minimums)
    and easier to handle. Both parts must be the same material/thickness.
  * Radius values are cut clean THROUGH the teeth as 7-segment numerals (SCS
    does not do solid/raster engraving; single-line etch would need SCS_SLE +
    a checkout note + eligible material). 7-seg slots have no font islands to
    drop out and no fragile thin strokes.
  * All geometry is closed contours on a single layer ("0"). No text entities,
    no open paths.
  * Suggested material: bare 5052 aluminum, .040"-.063", no finish -- cheap,
    dimensionally accurate, metal-in-metal like the real board.
"""

import argparse
import math
import os

import ezdxf

# --- Radius brackets (mm), 0.5mm steps around the computed targets ---
OUTER_RADII = [52.0, 52.5, 53.0, 53.5, 54.0]   # front+middle: calc 53.36
REAR_RADII = [46.5, 47.0, 47.5, 48.0]          # rear:         calc 47.41

# --- Tooth / comb geometry (mm) ---
FLAT_LEN = 20.0      # registration flat length beyond each corner tangent
SPINE_H = 12.0       # spine bar height (connects the teeth into one part)
TOOTH_GAP = 16.0     # clear gap between teeth (corner access)
END_MARGIN = 12.0    # spine overhang past the end teeth
COMB_GAP = 30.0      # vertical gap between the two combs

# --- 7-segment numeral (cut-through) ---
DIGIT_H = 12.0       # glyph height
DIGIT_W = 7.0        # glyph width
SEG_T = 1.3          # segment (slot) thickness
SEG_GAP = 0.4        # gap so adjacent segments stay disjoint
GLYPH_ADV = DIGIT_W + 2.6   # digit-to-digit advance
DOT_ADV = SEG_T + 2.6       # advance for a decimal point

CUT_LAYER = "0"      # SendCutSend: all cut geometry on one layer

# 90-degree arc, CCW (convex toward the corner) for the reversed top traversal.
_ARC_BULGE = math.tan(math.radians(90.0) / 4.0)   # +0.41421...

# Which of segments a..g are lit per digit.
_SEG = {
    "0": "abcdef", "1": "bc",   "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg",  "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}


def _rect(msp, x0, y0, x1, y1):
    """Cut a closed rectangular slot (as a hole on the cut layer)."""
    msp.add_lwpolyline(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        close=True, dxfattribs={"layer": CUT_LAYER},
    )


def _seg_rects(x, y):
    """Return {seg: (x0,y0,x1,y1)} for a glyph cell with lower-left at (x,y)."""
    W, H, T, g = DIGIT_W, DIGIT_H, SEG_T, SEG_GAP
    half = H / 2.0
    return {
        "a": (x + T + g, y + H - T, x + W - T - g, y + H),
        "g": (x + T + g, y + half - T / 2, x + W - T - g, y + half + T / 2),
        "d": (x + T + g, y, x + W - T - g, y + T),
        "f": (x, y + half + g, x + T, y + H - T - g),
        "b": (x + W - T, y + half + g, x + W, y + H - T - g),
        "e": (x, y + T + g, x + T, y + half - g),
        "c": (x + W - T, y + T + g, x + W, y + half - g),
    }


def seven_seg_width(s):
    w = 0.0
    for ch in s:
        w += DOT_ADV if ch == "." else GLYPH_ADV
    return w - (GLYPH_ADV - DIGIT_W)   # trim trailing advance to last glyph width


def seven_seg(msp, s, x_center, y_center):
    """Cut string s (digits and '.') centered on (x_center, y_center)."""
    total = seven_seg_width(s)
    x = x_center - total / 2.0
    y = y_center - DIGIT_H / 2.0
    for ch in s:
        if ch == ".":
            _rect(msp, x, y, x + SEG_T, y + SEG_T)   # decimal point
            x += DOT_ADV
            continue
        segs = _seg_rects(x, y)
        for name in _SEG[ch]:
            _rect(msp, *segs[name])
        x += GLYPH_ADV


def add_comb(msp, radii, y_base):
    """Build one connected comb (spine + up-teeth) with cut-through labels.

    Spine bottom sits at y_base; teeth point up. Each tooth's rounded top-right
    corner is the candidate radius; the top and right edges are the registration
    flats. Returns (width, top_y) for layout.
    """
    max_r = max(radii)
    tooth_w = max_r + FLAT_LEN          # top flat >= FLAT_LEN for every tooth
    tooth_h = max_r + FLAT_LEN          # right flat >= FLAT_LEN for every tooth
    y_spine_top = y_base + SPINE_H
    y_top = y_spine_top + tooth_h

    # Lay out teeth left to right.
    teeth = []
    x = END_MARGIN
    for r in radii:
        teeth.append((x, x + tooth_w, r))
        x += tooth_w + TOOTH_GAP
    x_spine0 = 0.0
    x_spine1 = teeth[-1][1] + END_MARGIN

    # Single closed outline: spine bottom, right edge, top (teeth, R->L), left edge.
    pts = [
        (x_spine0, y_base, 0.0),
        (x_spine1, y_base, 0.0),
        (x_spine1, y_spine_top, 0.0),
    ]
    for (xL, xR, r) in reversed(teeth):
        pts.append((xR, y_spine_top, 0.0))          # spine top up to tooth base
        pts.append((xR, y_top - r, _ARC_BULGE))     # right flat; arc -> top tangent
        pts.append((xR - r, y_top, 0.0))            # top tangent
        pts.append((xL, y_top, 0.0))                # top flat
        pts.append((xL, y_spine_top, 0.0))          # left edge down to spine
    pts.append((x_spine0, y_spine_top, 0.0))
    msp.add_lwpolyline(pts, format="xyb", close=True,
                       dxfattribs={"layer": CUT_LAYER})

    # Cut-through R value centered in each tooth's solid band.
    for (xL, xR, r) in teeth:
        seven_seg(msp, "%.1f" % r, (xL + xR) / 2.0, y_spine_top + FLAT_LEN / 2.0)

    return x_spine1, y_top


def build(output_dir):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # REAR comb on the bottom, OUTER comb above it.
    _, rear_top = add_comb(msp, REAR_RADII, 0.0)
    add_comb(msp, OUTER_RADII, rear_top + COMB_GAP)

    path = os.path.join(output_dir, "fatif_corner_comb.dxf")
    doc.saveas(path)
    print("  Corner comb: OUTER %d + REAR %d teeth, 2 connected parts -> %s"
          % (len(OUTER_RADII), len(REAR_RADII), path))
    print("  Upload the DXF (not PDF); bare 5052 aluminum .040-.063, no finish.")


def main():
    ap = argparse.ArgumentParser(description="Generate Fatif corner-radius test comb DXF")
    ap.add_argument("--output-dir", default=".", help="Output directory (default: .)")
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    build(args.output_dir)


if __name__ == "__main__":
    main()
