#!/usr/bin/env python3
"""Generate SVG paint artwork for clip nameplates.

Output:
  fatif_top_clip_paint.svg    — "fatif" paint mask for top clip
  fatif_bottom_clip_paint.svg — "GOWLAND" paint mask for bottom clip

Each SVG contains:
  - Clip outline (dashed gray, for registration/alignment with DXF)
  - Paint mask: compound path with even-odd fill (black paint area with
    letter-shaped cutouts where bare stainless shows through)
  - Screw/slot holes (thin gray reference marks)

Coordinates are in clip-local mm, matching the DXF flat patterns.
SVG Y is negated (Y-up in clip coords → Y-down in SVG display).

Usage:
  source .venv/bin/activate && python3 generate_paint_artwork.py
"""

import numpy as np
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MplPath
import math

# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------
FUTURA_PATH = "/System/Library/Fonts/Supplemental/Futura.ttc"
futura_medium = FontProperties(fname=FUTURA_PATH, weight="medium")
futura_light = FontProperties(fname=FUTURA_PATH, weight="light")

# ---------------------------------------------------------------------------
# Dimensions (from fatif_adapter_cadquery.py, clip-local flat pattern coords)
# ---------------------------------------------------------------------------
HB = 45.0               # clip half bar length
BOT_W = 10.0             # bottom clip width
TOP_WIDE = 14.0          # top clip wide section
TOP_NARROW = 8.0         # top clip narrow section
DOG_BONE_INSET = TOP_WIDE - TOP_NARROW   # 6mm
TAPER_IN = 15.0          # X where taper meets narrow
TAPER_OUT = 20.0         # X where taper meets wide
CR = 2.0                 # clip corner radius
BEND_RUN = 10.0          # tab bend run (45° diagonal)

PI = 1.0                 # paint inset from clip edges
PR = 2.0                 # paint corner radius
PTM = 1.0                # perpendicular tab margin

SL = 9.0                 # slot length
SW = 3.4                 # slot width
SA_DEG = 135.0           # slot angle (degrees)
SCM = 1.0                # slot clearance margin

# Slot positions in flat pattern
_ht = (SL - SW) / 2
_cdx = _ht / math.sqrt(2)
SLOT_XS = [-(HB + TAPER_OUT) / 2 + _cdx, (TAPER_OUT + HB) / 2 + _cdx]
SLOT_Y = 6.5             # slot Y in flat pattern (= screw_Y - inner_wide_Y)

# Text sizing (matching generate_nameplate_mockup.py)
NARROW_PAINT_H = 6.0     # narrow section paint height (top - bottom with inset)
MARGIN_FRAC = 0.15        # vertical margin fraction used in mockup
FATIF_INK_H = NARROW_PAINT_H * (1 - 2 * MARGIN_FRAC)       # ~4.2mm
GOWLAND_INK_H = NARROW_PAINT_H * 0.95 * (1 - 2 * MARGIN_FRAC)  # ~3.99mm
FATIF_SPACING = 0.5
GOWLAND_SPACING = 0.62

# Bottom clip screw positions (flat pattern: clip centered, Y=0 to 10)
BOT_SCREW_XS = [-25.0, 25.0]
BOT_SCREW_Y = BOT_W / 2  # 5.0
M3_CLEAR = 3.4            # M3 clearance hole diameter


# ---------------------------------------------------------------------------
# Helpers: polygon filleting
# ---------------------------------------------------------------------------

def fillet_polygon(verts, radius, n_arc=16):
    """Compute filleted polygon vertices. radius can be scalar or per-vertex list."""
    n = len(verts)
    radii = [radius] * n if isinstance(radius, (int, float)) else list(radius)
    result = []
    for i in range(n):
        r = radii[i]
        if r <= 0:
            result.append(verts[i])
            continue
        p_prev = np.array(verts[(i - 1) % n])
        p_curr = np.array(verts[i])
        p_next = np.array(verts[(i + 1) % n])
        v_in = p_prev - p_curr
        v_out = p_next - p_curr
        len_in, len_out = np.linalg.norm(v_in), np.linalg.norm(v_out)
        if len_in < 1e-9 or len_out < 1e-9:
            result.append(tuple(p_curr))
            continue
        u_in, u_out = v_in / len_in, v_out / len_out
        dot = np.clip(np.dot(u_in, u_out), -1, 1)
        half_angle = np.arccos(dot) / 2
        if abs(np.sin(half_angle)) < 1e-9:
            result.append(tuple(p_curr))
            continue
        max_r = min(len_in, len_out) / 2 * 0.9
        if np.tan(half_angle) > 1e-9:
            r = min(r, max_r / np.tan(half_angle))
        tan_len = r * np.tan(math.pi / 2 - half_angle)
        p_start = p_curr + u_in * tan_len
        p_end = p_curr + u_out * tan_len
        bisect = u_in + u_out
        bl = np.linalg.norm(bisect)
        if bl < 1e-9:
            result.append(tuple(p_curr))
            continue
        center = p_curr + (bisect / bl) * (r / np.sin(half_angle))
        a_start = np.arctan2(p_start[1] - center[1], p_start[0] - center[0])
        a_end = np.arctan2(p_end[1] - center[1], p_end[0] - center[0])
        cross = u_in[0] * u_out[1] - u_in[1] * u_out[0]
        if cross > 0:
            if a_end > a_start: a_end -= 2 * math.pi
        else:
            if a_end < a_start: a_end += 2 * math.pi
        for a in np.linspace(a_start, a_end, n_arc):
            result.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a)))
    return result


def stadium_pts(cx, cy, half_l, half_w, angle_deg, n_arc=16):
    """Stadium shape (rect with semicircular endcaps) as point list."""
    ar = math.radians(angle_deg)
    ax_v = np.array([math.cos(ar), math.sin(ar)])
    c = np.array([cx, cy])
    shl = max(half_l - half_w, 0)
    pts = []
    rc = c + shl * ax_v
    for i in range(n_arc + 1):
        theta = ar + math.pi / 2 - math.pi * i / n_arc
        pts.append((rc[0] + half_w * math.cos(theta), rc[1] + half_w * math.sin(theta)))
    lc = c - shl * ax_v
    for i in range(n_arc + 1):
        theta = ar - math.pi / 2 - math.pi * i / n_arc
        pts.append((lc[0] + half_w * math.cos(theta), lc[1] + half_w * math.sin(theta)))
    return pts


# ---------------------------------------------------------------------------
# Helpers: SVG path generation
# ---------------------------------------------------------------------------

def pts_to_svg_d(pts, close=True):
    """Convert point list to SVG path data string. Negates Y for SVG coords."""
    if not pts:
        return ""
    d = f"M{pts[0][0]:.4f},{-pts[0][1]:.4f}"
    for p in pts[1:]:
        d += f" L{p[0]:.4f},{-p[1]:.4f}"
    if close:
        d += " Z"
    return d


def mpl_to_svg_d(vertices, codes):
    """Convert matplotlib path vertices+codes to SVG path data. Negates Y."""
    parts = []
    i, n = 0, len(codes)
    while i < n:
        c = codes[i]
        v = vertices[i]
        if c == MplPath.MOVETO:
            parts.append(f"M{v[0]:.4f},{-v[1]:.4f}")
            i += 1
        elif c == MplPath.LINETO:
            parts.append(f"L{v[0]:.4f},{-v[1]:.4f}")
            i += 1
        elif c == MplPath.CURVE3:
            v2 = vertices[i + 1]
            parts.append(f"Q{v[0]:.4f},{-v[1]:.4f} {v2[0]:.4f},{-v2[1]:.4f}")
            i += 2
        elif c == MplPath.CURVE4:
            v2, v3 = vertices[i + 1], vertices[i + 2]
            parts.append(
                f"C{v[0]:.4f},{-v[1]:.4f} {v2[0]:.4f},{-v2[1]:.4f} "
                f"{v3[0]:.4f},{-v3[1]:.4f}")
            i += 3
        elif c == MplPath.CLOSEPOLY:
            parts.append("Z")
            i += 1
        else:
            i += 1
    return " ".join(parts)


def text_svg_paths(text, font_prop, ink_h, cx, cy, spacing_em=0.5):
    """Return list of SVG path data strings for spaced text at (cx, cy)."""
    ref_size = 72
    char_data = []
    for ch in text:
        tp = TextPath((0, 0), ch, size=ref_size, prop=font_prop)
        char_data.append((tp.vertices.copy(), tp.codes.copy()))

    # Measure reference ink height
    all_ys = np.concatenate([v[:, 1] for v, _ in char_data])
    y_top, y_bot = all_ys.max(), all_ys.min()
    scale = ink_h / (y_top - y_bot)
    y_center = (y_top + y_bot) / 2

    # Character widths (scaled)
    widths = [(v[:, 0].max() - v[:, 0].min()) * scale for v, _ in char_data]
    avg_w = np.mean(widths)
    gap = avg_w * spacing_em
    total_w = sum(widths) + gap * (len(text) - 1)

    # Position and generate SVG paths
    paths = []
    x = cx - total_w / 2
    for (verts, codes), w in zip(char_data, widths):
        sv = verts * scale
        sv[:, 1] = cy + (sv[:, 1] - y_center * scale)
        sv[:, 0] += x - sv[:, 0].min()
        paths.append(mpl_to_svg_d(sv, codes))
        x += w + gap
    return paths


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

def svg_header(viewbox, width_mm, height_mm):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     viewBox="{viewbox}"\n'
        f'     width="{width_mm:.1f}mm" height="{height_mm:.1f}mm">\n'
    )


def svg_path(d, **attrs):
    attr_str = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'  <path d="{d}" {attr_str}/>\n'


def svg_circle(cx, cy, r, **attrs):
    attr_str = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'  <circle cx="{cx:.4f}" cy="{-cy:.4f}" r="{r:.4f}" {attr_str}/>\n'


def svg_footer():
    return '</svg>\n'


# ---------------------------------------------------------------------------
# Bottom clip SVG
# ---------------------------------------------------------------------------

def generate_bottom_clip():
    """Generate paint artwork SVG for bottom clip ("GOWLAND")."""
    # Clip outline (flat pattern: X=[-45,45], Y=[0,10], R2)
    clip_verts = [(-HB, 0), (HB, 0), (HB, BOT_W), (-HB, BOT_W)]
    clip_pts = fillet_polygon(clip_verts, CR)
    clip_d = pts_to_svg_d(clip_pts)

    # Paint area (1mm inset, R2)
    paint_verts = [(-HB + PI, PI), (HB - PI, PI),
                   (HB - PI, BOT_W - PI), (-HB + PI, BOT_W - PI)]
    paint_pts = fillet_polygon(paint_verts, PR)
    paint_d = pts_to_svg_d(paint_pts)

    # Text paths
    text_cx, text_cy = 0.0, BOT_W / 2
    text_ds = text_svg_paths("GOWLAND", futura_light, GOWLAND_INK_H,
                             text_cx, text_cy, GOWLAND_SPACING)

    # Compound path: paint area + text cutouts (even-odd creates holes)
    compound_d = paint_d + " " + " ".join(text_ds)

    # SVG: clip content at X=[-45,45], Y=[0,10] → SVG Y=[-10,0]
    # Add padding
    pad = 2
    vb_x, vb_w = -HB - pad, 2 * HB + 2 * pad
    vb_y, vb_h = -(BOT_W + pad), BOT_W + 2 * pad

    svg = svg_header(f"{vb_x:.1f} {vb_y:.1f} {vb_w:.1f} {vb_h:.1f}", vb_w, vb_h)
    svg += f'  <!-- Bottom clip paint artwork: "GOWLAND" in Futura Light -->\n'
    svg += f'  <!-- Coordinates: clip-local mm (X=[-45,45], Y=[0,10]) -->\n'

    # Clip outline (registration)
    svg += svg_path(clip_d, fill="none", stroke="#999999",
                    stroke_width="0.2", stroke_dasharray="1,0.5")

    # Paint mask with text cutouts
    svg += svg_path(compound_d, fill="black", fill_rule="evenodd", stroke="none")

    # Screw holes (reference)
    for sx in BOT_SCREW_XS:
        svg += svg_circle(sx, BOT_SCREW_Y, M3_CLEAR / 2,
                          fill="none", stroke="#cccccc", stroke_width="0.1")

    svg += svg_footer()

    path = "fatif_bottom_clip_paint.svg"
    with open(path, "w") as f:
        f.write(svg)
    print(f"Saved {path}")


# ---------------------------------------------------------------------------
# Top clip SVG
# ---------------------------------------------------------------------------

def generate_top_clip():
    """Generate paint artwork SVG for top clip ("fatif")."""
    # Clip outline (flat pattern dog-bone with tab cutoff)
    # Vertices: inner edge at Y=0, outer edge at Y=14
    clip_verts = [
        (-HB, 0),                             # 0: lower-left
        (-TAPER_OUT, 0),                       # 1: left taper start
        (-TAPER_IN, DOG_BONE_INSET),           # 2: left taper, narrow
        (TAPER_IN, DOG_BONE_INSET),            # 3: right taper, narrow
        (TAPER_OUT, 0),                        # 4: right taper start
        (HB, 0),                               # 5: lower-right
        (HB, TOP_WIDE),                        # 6: upper-right
        (-HB + BEND_RUN, TOP_WIDE),            # 7: bend point A
        (-HB, TOP_WIDE - BEND_RUN),            # 8: bend point B
    ]
    # R2 on body corners (0-6), R0 on bend endpoints (7,8)
    clip_radii = [CR] * 7 + [0, 0]
    clip_pts = fillet_polygon(clip_verts, clip_radii)
    clip_d = pts_to_svg_d(clip_pts)

    # Paint area (complex polygon with bend line offset on left side)
    # Bend line in flat coords: A(-35, 14) to B(-45, 4), equation: X = Y - 49
    # Offset paint line (PTM mm perpendicular = PTM*√2 in X): X = Y - 49 + √2*PTM
    bend_ox = PTM * math.sqrt(2)

    pe_right = HB - PI                  # 44
    pe_top = TOP_WIDE - PI              # 13
    pe_bot_wide = 0 + PI                # 1
    pe_bot_narrow = DOG_BONE_INSET + PI # 7

    # Left edge: follows offset bend line, clamped to clip left + inset
    clip_left_pi = -HB + PI             # -44
    diag_at_top = pe_top - 49 + bend_ox       # ~-34.586
    clamp_y = clip_left_pi + 49 - bend_ox     # ~3.586

    paint_verts = [
        (-TAPER_OUT, pe_bot_wide),       # left taper, bottom
        (-TAPER_IN, pe_bot_narrow),      # left taper, narrow
        (TAPER_IN, pe_bot_narrow),       # right taper, narrow
        (TAPER_OUT, pe_bot_wide),        # right taper, bottom
        (pe_right, pe_bot_wide),         # bottom-right
        (pe_right, pe_top),              # top-right
        (diag_at_top, pe_top),           # top-left (on diagonal offset)
        (clip_left_pi, clamp_y),         # diagonal → vertical
        (clip_left_pi, pe_bot_wide),     # bottom-left
    ]
    paint_pts = fillet_polygon(paint_verts, PR)
    paint_d = pts_to_svg_d(paint_pts)

    # Slot clearance cutouts (stadiums, bare metal through paint)
    slot_clear_ds = []
    for sx in SLOT_XS:
        pts = stadium_pts(sx, SLOT_Y,
                          SL / 2 + SCM, SW / 2 + SCM, SA_DEG)
        slot_clear_ds.append(pts_to_svg_d(pts))

    # Text paths
    text_cx = 0.0
    text_cy = (pe_bot_narrow + pe_top) / 2   # center of narrow paint section
    text_ds = text_svg_paths("fatif", futura_medium, FATIF_INK_H,
                             text_cx, text_cy, FATIF_SPACING)

    # Compound path: paint area + slot cutouts + text cutouts
    all_cutouts = slot_clear_ds + text_ds
    compound_d = paint_d + " " + " ".join(all_cutouts)

    # SVG bounds: content at X≈[-45,45], Y≈[0,14] → SVG Y≈[-14,0]
    pad = 2
    vb_x, vb_w = -HB - pad, 2 * HB + 2 * pad
    vb_y, vb_h = -(TOP_WIDE + pad), TOP_WIDE + 2 * pad

    svg = svg_header(f"{vb_x:.1f} {vb_y:.1f} {vb_w:.1f} {vb_h:.1f}", vb_w, vb_h)
    svg += f'  <!-- Top clip paint artwork: "fatif" in Futura Medium -->\n'
    svg += f'  <!-- Coordinates: clip-local mm (X=[-45,45], Y=[0,14]) -->\n'
    svg += f'  <!-- Bend line from A(-35,14) to B(-45,4): bend tab 90° up -->\n'

    # Clip outline (registration)
    svg += svg_path(clip_d, fill="none", stroke="#999999",
                    stroke_width="0.2", stroke_dasharray="1,0.5")

    # Paint mask with slot clearances and text cutouts
    svg += svg_path(compound_d, fill="black", fill_rule="evenodd", stroke="none")

    # Slot holes (reference, actual slot shape)
    for sx in SLOT_XS:
        pts = stadium_pts(sx, SLOT_Y, SL / 2, SW / 2, SA_DEG)
        svg += svg_path(pts_to_svg_d(pts), fill="none", stroke="#cccccc",
                        stroke_width="0.1")

    # Bend line (reference)
    bend_a = (-HB + BEND_RUN, TOP_WIDE)     # (-35, 14)
    bend_b = (-HB, TOP_WIDE - BEND_RUN)     # (-45, 4)
    svg += (f'  <line x1="{bend_a[0]:.3f}" y1="{-bend_a[1]:.3f}" '
            f'x2="{bend_b[0]:.3f}" y2="{-bend_b[1]:.3f}" '
            f'stroke="#cccccc" stroke-width="0.15" stroke-dasharray="0.5,0.5"/>\n')

    svg += svg_footer()

    path = "fatif_top_clip_paint.svg"
    with open(path, "w") as f:
        f.write(svg)
    print(f"Saved {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    generate_bottom_clip()
    generate_top_clip()


if __name__ == "__main__":
    main()
