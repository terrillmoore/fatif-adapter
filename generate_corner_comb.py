#!/usr/bin/env python3
"""
Fatif Adapter — Corner Radius Test Comb

Generates a single DXF of labeled corner "gauges" for verifying the actual
corner radii of the Fatif DS 20x25 casting before committing to finished
re-fabrication. Cut cheaply in bare aluminum / acrylic / MDF (no finish),
drop each gauge into the matching casting corner, and find the radius that
seats flush — flats registering against the casting flats with no diagonal
tip interference and no corner gap.

Why a comb instead of one computed blank:
  The corner setback along the 45 degree diagonal is s = R*(sqrt(2)-1), so a
  measured diagonal interference dd maps to a radius change dR = dd/(sqrt(2)-1)
  = 2.414*dd. That 2.414x amplification means a ~0.2mm caliper slop on dd is
  ~0.5mm on R, so bracketing beats trusting a single computed value.

First-fab measurements (calipers, diagonal tip overhang at one corner):
  Front + middle (BOARD profile, X-Y confirmed OK):  ~1.08mm too tight
    -> R = 50.75 + 2.414*1.08 = 53.36mm  (clean-metric candidate: 53.0 / 53.5)
  Rear (REAR profile, also ~0.5mm oversize in X-Y):  ~1.0mm too tight
    -> R = 45.0  + 2.414*1.00 = 47.41mm  (clean-metric candidate: 47.0 / 47.5)

The 1970s/80s Italian casting was almost certainly laid out in clean metric
values, so the brackets step in 0.5mm increments straddling each computed R.

Each gauge is a convex rounded corner (replicating a board corner) with two
90-degree registration flats FLAT_LEN long. Sharp corner at top-right of each
gauge; material extends toward lower-left. Cut lines on layer CUT; radius
labels on layer LABEL (score/ignore — not part of the cut path).
"""

import argparse
import math
import os

import ezdxf

# --- Radius brackets (mm), 0.5mm increments around the computed targets ---
OUTER_RADII = [52.0, 52.5, 53.0, 53.5, 54.0]   # front+middle: calc 53.36
REAR_RADII = [46.5, 47.0, 47.5, 48.0]          # rear:         calc 47.41

# --- Gauge geometry ---
FLAT_LEN = 30.0      # registration flat length on each side of the corner
LABEL_H = 6.0        # text height

# --- Sheet layout ---
COL_PITCH = 105.0    # X spacing between gauge sharp corners
ROW_PITCH = 120.0    # Y spacing between the two rows

# 90-degree arc bulge, CW (convex toward the sharp corner): -tan(90/4 deg)
_ARC_BULGE = -math.tan(math.radians(90.0) / 4.0)   # = -0.41421...


def add_corner_gauge(msp, cx, cy, R, label):
    """One corner gauge with its sharp (theoretical) corner at (cx, cy).

    Top flat runs along y=cy toward -X; right flat along x=cx toward -Y;
    the fillet of radius R bulges toward (cx, cy). Inner side closed with a
    45 degree diagonal to save material.
    """
    top_far = (cx - R - FLAT_LEN, cy)
    top_tan = (cx - R, cy)
    right_tan = (cx, cy - R)
    right_far = (cx, cy - R - FLAT_LEN)

    # Closed contour: line, arc (bulge), line, closing diagonal.
    pts = [
        (top_far[0], top_far[1], 0.0),          # -> top_tan (line)
        (top_tan[0], top_tan[1], _ARC_BULGE),   # -> right_tan (arc, convex to corner)
        (right_tan[0], right_tan[1], 0.0),       # -> right_far (line)
        (right_far[0], right_far[1], 0.0),       # -> top_far (closing diagonal)
    ]
    msp.add_lwpolyline(pts, format="xyb", close=True, dxfattribs={"layer": "CUT"})

    # Label centered inside the pentagon, along the diagonal, rotated 45 deg.
    lx = cx - 0.40 * (R + FLAT_LEN)
    ly = cy - 0.40 * (R + FLAT_LEN)
    txt = msp.add_text(
        label,
        dxfattribs={"layer": "LABEL", "height": LABEL_H, "rotation": 45.0},
    )
    txt.set_placement((lx, ly), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)


def add_note(msp, x, y, text, height=8.0):
    msp.add_text(text, dxfattribs={"layer": "LABEL", "height": height}).set_placement(
        (x, y), align=ezdxf.enums.TextEntityAlignment.LEFT
    )


def build(output_dir):
    doc = ezdxf.new("R2010")
    doc.layers.add("CUT", color=7)     # white/black — the cut path
    doc.layers.add("LABEL", color=3)   # green — text, do not cut
    msp = doc.modelspace()

    # Row 1: outer (front + middle) brackets.
    add_note(msp, -FLAT_LEN - 54, LABEL_H * 1.5,
             "OUTER  (front + middle, 171.5 profile)  calc R53.36")
    for i, R in enumerate(OUTER_RADII):
        add_corner_gauge(msp, i * COL_PITCH, 0.0, R, "R%.1f" % R)

    # Row 2: rear brackets, below.
    add_note(msp, -FLAT_LEN - 54, -ROW_PITCH + LABEL_H * 1.5,
             "REAR  (160 profile)  calc R47.41")
    for i, R in enumerate(REAR_RADII):
        add_corner_gauge(msp, i * COL_PITCH, -ROW_PITCH, R, "R%.1f" % R)

    add_note(msp, -FLAT_LEN - 54, ROW_PITCH * 0.65,
             "FATIF CORNER RADIUS TEST COMB  -  cut cheap, no finish", height=10.0)

    path = os.path.join(output_dir, "fatif_corner_comb.dxf")
    doc.saveas(path)
    print("  Corner comb: %d outer + %d rear gauges -> %s"
          % (len(OUTER_RADII), len(REAR_RADII), path))


def main():
    ap = argparse.ArgumentParser(description="Generate Fatif corner-radius test comb DXF")
    ap.add_argument("--output-dir", default=".", help="Output directory (default: .)")
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    build(args.output_dir)


if __name__ == "__main__":
    main()
