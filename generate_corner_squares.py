#!/usr/bin/env python3
"""
Fatif Adapter — Corner Radius Test Squares (SendCutSend-ready)

Generates a DXF of two SOLID square gauges for verifying the actual corner
radii of the Fatif DS 20x25 casting before committing to finished re-fab,
plus a printed reference key (PDF) that maps each corner to its radius.

Each square's FOUR corners each carry a DIFFERENT candidate radius. Push one
corner of the square into the matching casting corner, register the two
adjacent flats against the casting flats, and judge the fit (flush = right
radius; diagonal tip gap or interference = wrong). Rotate to test each corner.

Two squares:
  FRONT (front + middle sheets, 171.5 profile): corners R52.5/53.0/53.5/54.0
    (calc R53.36)
  REAR  (rear sheet, 160 profile):              corners R46.5/47.0/47.5/48.0
    (calc R47.41)

The 45-degree corner setback is s = R*(sqrt(2)-1), so a measured diagonal
interference dd maps to dR = 2.414*dd -- that amplification plus laser
tolerance (~0.13mm) is why we bracket in 0.5mm steps around each target.

Cost-driven design (throwaway gauges): SOLID squares, no inner hole and no
cut-through numerals -- laser cost is dominated by pierce count and cut
length, and per-corner numerals were ~65 tiny pierces per part. Instead each
square gets ONE small orientation hole at its smallest-radius corner (BL);
the printed key (fatif_corner_squares_key.pdf) says radii step up 0.5mm going
counterclockwise from that hole. So the DXF is just 2 outlines + 2 holes.

SendCutSend setup (per their current guidelines):
  * Upload each DXF, NOT the PDF. Instant-price 2D formats are dxf/dwg/eps/ai.
  * TWO separate files, one square each (fatif_corner_squares_front.dxf and
    _rear.dxf). SCS prices per part and its quote UI keys size/options off the
    whole file's bbox, so a nested file misreads size and hides options.
  * Units stamped as mm ($INSUNITS=4).
  * All geometry is closed contours on a single layer ("0"). No text entities.
  * Suggested material: bare 5052 aluminum, .040"-.063", no finish.
  * The key PDF is a human reference only -- do not upload it for cutting.
"""

import argparse
import math
import os

import ezdxf

# --- Candidate radii per corner, order = [BL, BR, TR, TL] (CCW from lower-left)
FRONT_RADII = [52.5, 53.0, 53.5, 54.0]   # front + middle sheets: calc 53.36
REAR_RADII = [46.5, 47.0, 47.5, 48.0]    # rear sheet:            calc 47.41

# --- Geometry (mm) ---
FLAT_MIN = 50.0        # shortest straight flat (registration length)
ORIENT_HOLE_DIA = 2.5  # orientation hole marking the BL (smallest-R) corner
ORIENT_HOLE_INSET = 13.0  # hole distance in from the BL corner arc
# Hole direction from the BL arc center: biased toward the BOTTOM edge (not the
# 45deg diagonal) so orientation is flip-proof -- the part is otherwise
# mirror-symmetric, and a bottom-biased hole reads "nearer left edge" only when
# the part is flipped over. 250deg = down and slightly left.
ORIENT_HOLE_ANGLE = 250.0
NEST_GAP = 20.0        # gap between the two squares in the combined DXF

CUT_LAYER = "0"        # SendCutSend: all cut geometry on one layer

# 90-degree convex corner arc, CCW traversal: bulge = +tan(90/4 deg).
_BULGE = math.tan(math.radians(90.0) / 4.0)   # +0.41421...
_SQRT2 = math.sqrt(2.0)


def square_size(radii):
    """Bounding-box size B so every straight flat is >= FLAT_MIN.

    Flat on the edge between adjacent corners i,j is B - R_i - R_j; the tightest
    edge is the largest adjacent-radius sum around the 4-cycle BL-BR-TR-TL.
    """
    pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return max(radii[i] + radii[j] for (i, j) in pairs) + FLAT_MIN


def corner_centers(radii, x0, y0):
    """Arc centers for [BL, BR, TR, TL] of the square at origin (x0, y0)."""
    B = square_size(radii)
    return B, [
        (x0 + radii[0], y0 + radii[0]),          # BL
        (x0 + B - radii[1], y0 + radii[1]),      # BR
        (x0 + B - radii[2], y0 + B - radii[2]),  # TR
        (x0 + radii[3], y0 + B - radii[3]),      # TL
    ]


def _outline(radii, x0, y0):
    """Closed rounded-square outline (CCW) as (x, y, bulge) vertices."""
    B, (cBL, cBR, cTR, cTL) = corner_centers(radii, x0, y0)
    return [
        (cBL[0], y0, 0.0),          # bottom flat, from BL bottom tangent
        (cBR[0], y0, _BULGE),       # -> BR bottom tangent, arc up
        (x0 + B, cBR[1], 0.0),      # right flat
        (x0 + B, cTR[1], _BULGE),   # -> TR right tangent, arc left
        (cTR[0], y0 + B, 0.0),      # top flat
        (cTL[0], y0 + B, _BULGE),   # -> TL top tangent, arc down
        (x0, cTL[1], 0.0),          # left flat
        (x0, cBL[1], _BULGE),       # -> BL left tangent, arc to start
    ]


def orient_hole_center(radii, x0, y0):
    """Small hole marking the BL (smallest-radius) corner, bottom-biased."""
    _, centers = corner_centers(radii, x0, y0)
    cx, cy = centers[0]                      # BL
    r = radii[0] - ORIENT_HOLE_INSET
    a = math.radians(ORIENT_HOLE_ANGLE)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def add_square(msp, radii, x0, y0):
    """Draw one solid square outline + its orientation hole. Returns B."""
    msp.add_lwpolyline(_outline(radii, x0, y0), format="xyb", close=True,
                       dxfattribs={"layer": CUT_LAYER})
    hx, hy = orient_hole_center(radii, x0, y0)
    msp.add_circle((hx, hy), ORIENT_HOLE_DIA / 2.0, dxfattribs={"layer": CUT_LAYER})
    return square_size(radii)


def _key_layout():
    """Side-by-side placement used only for the printed key (not the cut files)."""
    bf = square_size(FRONT_RADII)
    return [
        (FRONT_RADII, 0.0, 0.0, "FRONT"),
        (REAR_RADII, bf + NEST_GAP, 0.0, "REAR"),
    ]


def _write_one(radii, name, output_dir):
    """Write one solid square gauge to its own DXF at origin (one SCS part)."""
    doc = ezdxf.new("R2010")
    # Declare millimeters so vendors don't misread the units. Without an
    # explicit mm flag ($INSUNITS=4), some importers (Ponoko) assume inches
    # and scale the part by 25.4 (157.5mm -> 4000mm).
    doc.units = ezdxf.units.MM          # sets $INSUNITS = 4
    doc.header["$MEASUREMENT"] = 1       # metric
    B = add_square(doc.modelspace(), radii, 0.0, 0.0)
    path = os.path.join(output_dir, "fatif_corner_squares_%s.dxf" % name.lower())
    doc.saveas(path)
    print("  %-5s square: %.1fx%.1fmm, corners %s -> %s"
          % (name, B, B, "/".join("%.1f" % r for r in radii), path))
    return path


def write_dxf(output_dir):
    # Separate files, one part each: SCS prices per part and its quote UI keys
    # size/options off the whole file's bbox, so a nested file misreads size
    # and can hide thickness/finish options.
    _write_one(FRONT_RADII, "FRONT", output_dir)
    _write_one(REAR_RADII, "REAR", output_dir)


def write_key(output_dir):
    """Printed reference: outlines + per-corner radius labels + orient hole."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    fig, ax = plt.subplots(figsize=(11, 6))
    diag = [(-1, -1), (1, -1), (1, 1), (-1, 1)]     # BL, BR, TR, TL outward
    for radii, x0, y0, name in _key_layout():
        B, centers = corner_centers(radii, x0, y0)
        # Outline: sample each arc so the rounded square renders true.
        xs, ys = _outline_points(radii, x0, y0)
        ax.plot(xs, ys, "k-", lw=1.2)
        # Corner radius labels, placed just outside each corner.
        for i, (cx, cy) in enumerate(centers):
            dx, dy = diag[i]
            lx = cx + dx / _SQRT2 * (radii[i] + 12)
            ly = cy + dy / _SQRT2 * (radii[i] + 12)
            ax.text(lx, ly, "R%.1f" % radii[i], ha="center", va="center",
                    fontsize=12, fontweight="bold")
        # Orientation hole + callout.
        hx, hy = orient_hole_center(radii, x0, y0)
        ax.add_patch(Circle((hx, hy), ORIENT_HOLE_DIA / 2.0, fc="k"))
        ax.annotate("orient. hole = smallest R,\nnearer BOTTOM edge\n"
                    "(nearer LEFT edge = flipped)", (hx, hy),
                    xytext=(x0 + B * 0.5, y0 + B * 0.30), fontsize=7.5,
                    ha="center", color="0.35",
                    arrowprops=dict(arrowstyle="->", color="0.5", lw=0.8))
        ax.text(x0 + B / 2, y0 + B / 2, "%s\n%.1fmm sq" % (name, B),
                ha="center", va="center", fontsize=13, color="0.25")

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Fatif corner-radius gauges — reference key  "
                 "(radii step +0.5mm CCW from the orientation hole)",
                 fontsize=11)
    fig.text(0.5, 0.03,
             "Push each corner into the matching casting corner; the flush one "
             "(no tip gap, no interference) is the true radius.  "
             "Bare 5052 aluminum, .040-.063in, no finish.",
             ha="center", fontsize=8, color="0.4")
    path = os.path.join(output_dir, "fatif_corner_squares_key.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("  Reference key (PRINT this, do not cut) -> %s" % path)
    return path


def _outline_points(radii, x0, y0, per_arc=24):
    """Expand the bulge outline into a dense point list for plotting."""
    verts = _outline(radii, x0, y0)
    xs, ys = [], []
    n = len(verts)
    for i in range(n):
        x0v, y0v, b = verts[i]
        x1v, y1v, _ = verts[(i + 1) % n]
        xs.append(x0v)
        ys.append(y0v)
        if b:  # arc from this vertex to the next
            chord = math.hypot(x1v - x0v, y1v - y0v)
            ang = 4 * math.atan(b)
            r = chord / (2 * math.sin(ang / 2))
            mx, my = (x0v + x1v) / 2, (y0v + y1v) / 2
            # center offset perpendicular to the chord
            d = math.sqrt(max(r * r - (chord / 2) ** 2, 0))
            ux, uy = (x1v - x0v) / chord, (y1v - y0v) / chord
            cx, cy = mx - uy * d, my + ux * d
            a0 = math.atan2(y0v - cy, x0v - cx)
            for k in range(1, per_arc):
                a = a0 + ang * k / per_arc
                xs.append(cx + r * math.cos(a))
                ys.append(cy + r * math.sin(a))
    xs.append(verts[0][0])
    ys.append(verts[0][1])
    return xs, ys


def build(output_dir):
    write_dxf(output_dir)
    write_key(output_dir)
    print("  Upload the DXF (not PDF); bare 5052 aluminum .040-.063, no finish.")


def main():
    ap = argparse.ArgumentParser(description="Generate Fatif corner-radius test squares DXF + key")
    ap.add_argument("--output-dir", default=".", help="Output directory (default: .)")
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    build(args.output_dir)


if __name__ == "__main__":
    main()
