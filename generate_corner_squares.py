#!/usr/bin/env python3
"""
Fatif Adapter — Corner Radius Test Squares (SendCutSend-ready)

Generates a DXF of two square frames for verifying the actual corner radii of
the Fatif DS 20x25 casting before committing to finished re-fabrication.

Each square is a frame (band) whose FOUR corners each carry a DIFFERENT
candidate radius. Push one corner of the square into the matching casting
corner, register the two adjacent flats against the casting flats, and judge
the fit (flush = right radius; diagonal tip gap or interference = wrong).
Rotate/reposition to test each of the four corners in turn.

Two squares:
  FRONT (front + middle sheets, 171.5 profile): corners R52.5/53.0/53.5/54.0
    (calc R53.36)
  REAR  (rear sheet, 160 profile):              corners R46.5/47.0/47.5/48.0
    (calc R47.41)

The 45-degree corner setback is s = R*(sqrt(2)-1), so a measured diagonal
interference dd maps to dR = 2.414*dd -- that amplification plus laser
tolerance (~0.13mm) is why we bracket in 0.5mm steps around each target.

SendCutSend setup (per their current guidelines):
  * Upload each DXF, NOT a PDF. Instant-price 2D formats are dxf/dwg/eps/ai.
  * Written as TWO separate files (one square each) -- Ponoko treats each
    uploaded DXF as a single part. Each square is a closed band (outer +
    inner contour). Units are stamped as mm ($INSUNITS=4) so no vendor
    misreads the file as inches.
  * Radius values are cut clean THROUGH the band as 7-segment numerals, on the
    corner arc adjacent to each corner (SCS does no solid/raster engraving;
    single-line etch would need SCS_SLE + a checkout note + eligible material).
  * All geometry is closed contours on a single layer ("0"). No text entities.
  * Suggested material: bare 5052 aluminum, .040"-.063", no finish.
"""

import argparse
import math
import os

import ezdxf

# --- Candidate radii per corner, order = [BL, BR, TR, TL] (CCW from lower-left)
FRONT_RADII = [52.5, 53.0, 53.5, 54.0]   # front + middle sheets: calc 53.36
REAR_RADII = [46.5, 47.0, 47.5, 48.0]    # rear sheet:            calc 47.41

# --- Frame geometry (mm) ---
FRAME_W = 24.0       # band width (outer edge to inner edge); holds corner label
FLAT_MIN = 50.0      # shortest straight flat (registration length)

# --- 7-segment numeral (cut-through) ---
# Kept small and horizontal so each label sits inside the thick corner band
# (rotated 7-seg digits are hard to read; the band is ~FRAME_W wide, so a
# compact horizontal numeral fits at the corner's diagonal midpoint).
DIGIT_H = 7.0        # glyph height
DIGIT_W = 5.0        # glyph width
SEG_T = 1.0          # segment (slot) thickness
SEG_GAP = 0.35       # gap so adjacent segments stay disjoint
GLYPH_ADV = DIGIT_W + 2.0   # digit-to-digit advance
DOT_ADV = SEG_T + 2.0       # advance for a decimal point

CUT_LAYER = "0"      # SendCutSend: all cut geometry on one layer

# 90-degree convex corner arc, CCW traversal: bulge = +tan(90/4 deg).
_BULGE = math.tan(math.radians(90.0) / 4.0)   # +0.41421...
_SQRT2 = math.sqrt(2.0)

# Which of segments a..g are lit per digit.
_SEG = {
    "0": "abcdef", "1": "bc",   "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg",  "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}


# ---------------------------------------------------------------- 7-seg labels

def _seg_rects_local(gx, gy):
    """{seg: (x0,y0,x1,y1)} for a glyph with lower-left at local (gx,gy)."""
    W, H, T, g = DIGIT_W, DIGIT_H, SEG_T, SEG_GAP
    half = H / 2.0
    return {
        "a": (gx + T + g, gy + H - T, gx + W - T - g, gy + H),
        "g": (gx + T + g, gy + half - T / 2, gx + W - T - g, gy + half + T / 2),
        "d": (gx + T + g, gy, gx + W - T - g, gy + T),
        "f": (gx, gy + half + g, gx + T, gy + H - T - g),
        "b": (gx + W - T, gy + half + g, gx + W, gy + H - T - g),
        "e": (gx, gy + T + g, gx + T, gy + half - g),
        "c": (gx + W - T, gy + T + g, gx + W, gy + half - g),
    }


def _label_width(s):
    w = 0.0
    for ch in s:
        w += DOT_ADV if ch == "." else GLYPH_ADV
    return w - (GLYPH_ADV - DIGIT_W)   # trim trailing advance to last glyph width


def _emit_rect(msp, x0, y0, x1, y1, cx, cy, cos_t, sin_t):
    """Rotate a local rect about the origin by theta, translate to (cx,cy)."""
    pts = []
    for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        pts.append((cx + x * cos_t - y * sin_t, cy + x * sin_t + y * cos_t))
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": CUT_LAYER})


def add_label(msp, s, cx, cy, theta_deg):
    """Cut string s (digits and '.') centered on (cx,cy), rotated theta_deg."""
    cos_t = math.cos(math.radians(theta_deg))
    sin_t = math.sin(math.radians(theta_deg))
    penx = -_label_width(s) / 2.0
    gy = -DIGIT_H / 2.0
    for ch in s:
        if ch == ".":
            _emit_rect(msp, penx, gy, penx + SEG_T, gy + SEG_T, cx, cy, cos_t, sin_t)
            penx += DOT_ADV
            continue
        rects = _seg_rects_local(penx, gy)
        for name in _SEG[ch]:
            _emit_rect(msp, *rects[name], cx, cy, cos_t, sin_t)
        penx += GLYPH_ADV


# ---------------------------------------------------------------- square frame

def _square_size(radii):
    """Bounding-box size B so every straight flat is >= FLAT_MIN.

    Flat on the edge between adjacent corners i,j is B - R_i - R_j; the tightest
    edge is the largest adjacent-radius sum around the 4-cycle BL-BR-TR-TL.
    """
    pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return max(radii[i] + radii[j] for (i, j) in pairs) + FLAT_MIN


def _ring(radii, x0, y0, inset):
    """One closed rounded-square contour (CCW) for the given corner radii.

    inset > 0 builds the inner contour (band hole): edges pull in by `inset`
    and corner radii shrink by `inset`, keeping a constant band width.
    Corners are [BL, BR, TR, TL]; box spans (x0,y0)..(x0+B, y0+B) at inset 0.
    """
    B = _square_size(radii)
    rBL, rBR, rTR, rTL = (r - inset for r in radii)
    # Corner arc centers are fixed (independent of inset) at radius R in.
    cBL = (x0 + radii[0], y0 + radii[0])
    cBR = (x0 + B - radii[1], y0 + radii[1])
    cTR = (x0 + B - radii[2], y0 + B - radii[2])
    cTL = (x0 + radii[3], y0 + B - radii[3])
    lo, hi = x0 + inset, x0 + B - inset
    ylo, yhi = y0 + inset, y0 + B - inset
    pts = [
        (cBL[0], ylo, 0.0),                 # bottom flat, left tangent
        (cBR[0], ylo, _BULGE),              # -> BR bottom tangent, arc up
        (hi, cBR[1], 0.0),                  # right flat
        (hi, cTR[1], _BULGE),               # -> TR right tangent, arc left
        (cTR[0], yhi, 0.0),                 # top flat
        (cTL[0], yhi, _BULGE),              # -> TL top tangent, arc down
        (lo, cTL[1], 0.0),                  # left flat
        (lo, cBL[1], _BULGE),               # -> BL left tangent, arc to start
    ]
    return B, pts, (cBL, cBR, cTR, cTL)


def add_square(msp, radii, x0, y0):
    """Build one square frame with cut-through corner labels. Returns (B, top)."""
    B, outer, centers = _ring(radii, x0, y0, 0.0)
    msp.add_lwpolyline(outer, format="xyb", close=True,
                       dxfattribs={"layer": CUT_LAYER})
    # Inner contour (band hole). Kept same CCW winding as the outer: reversing
    # a bulge polyline flips its arcs concave. SCS detects the hole by
    # containment, not winding, so nesting two CCW closed contours is fine.
    _, inner, _ = _ring(radii, x0, y0, FRAME_W)
    msp.add_lwpolyline(inner, format="xyb", close=True,
                       dxfattribs={"layer": CUT_LAYER})

    # Label each corner with a small HORIZONTAL numeral centered on the middle
    # of that corner's band, along the outward diagonal. The band is thick
    # enough (FRAME_W) that a compact horizontal label clears both contours.
    diag = [(-1, -1), (1, -1), (1, 1), (-1, 1)]     # BL, BR, TR, TL
    for i, (cx, cy) in enumerate(centers):
        dx, dy = diag[i]
        rmid = radii[i] - FRAME_W / 2.0             # middle of the band
        lx = cx + dx / _SQRT2 * rmid
        ly = cy + dy / _SQRT2 * rmid
        add_label(msp, "%.1f" % radii[i], lx, ly, 0.0)

    return B, y0 + B


def _write_square(radii, output_dir, name):
    """Write one square gauge to its own DXF (one Ponoko/SCS part per file)."""
    doc = ezdxf.new("R2010")
    # Declare millimeters so vendors don't misread the units. Without an
    # explicit mm flag ($INSUNITS=4), Ponoko assumes the coordinates are
    # inches and scales the part by 25.4 (157.5mm -> 4000mm).
    doc.units = ezdxf.units.MM          # sets $INSUNITS = 4
    doc.header["$MEASUREMENT"] = 1       # metric
    B, _ = add_square(doc.modelspace(), radii, 0.0, 0.0)
    path = os.path.join(output_dir, name)
    doc.saveas(path)
    print("  %-5s square: %.1fx%.1fmm, corners %s -> %s"
          % (name.split("_")[-1].split(".")[0].upper(), B, B,
             "/".join("%.1f" % r for r in radii), path))
    return path


def build(output_dir):
    # Two separate files -- Ponoko treats each uploaded DXF as one part.
    _write_square(FRONT_RADII, output_dir, "fatif_corner_squares_front.dxf")
    _write_square(REAR_RADII, output_dir, "fatif_corner_squares_rear.dxf")
    print("  Upload each DXF (not PDF); bare 5052 aluminum .040-.063, no finish.")


def main():
    ap = argparse.ArgumentParser(description="Generate Fatif corner-radius test squares DXF")
    ap.add_argument("--output-dir", default=".", help="Output directory (default: .)")
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    build(args.output_dir)


if __name__ == "__main__":
    main()
