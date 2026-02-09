#!/usr/bin/env python3
"""Generate a two-panel mockup of the Fatif adapter with painted nameplate on the top clip."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
from matplotlib.path import Path
import matplotlib.font_manager as fm
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
STAINLESS = "#D0D0D8"        # 304 SS bare metal (polished)
STAINLESS_BRIGHT = "#E0E0E8" # text on dark background — brighter for contrast
STAINLESS_EDGE = "#888890"
DARK_GRAY = "#2A2A2A"        # powder-coated front sheet
BORE_BLACK = "#0A0A0A"       # bore / background
PAINT_BLACK = "#1A1A1A"      # matte black paint on clip
SCREW_COLOR = "#555555"
SHEET_EDGE = "#444444"

# ---------------------------------------------------------------------------
# Geometry (mm) — from fatif_adapter_cadquery.py
# ---------------------------------------------------------------------------
BOARD = 171.5
R_BOARD = 50.75
GOWLAND = 139.0
R_GOWLAND = 3.4
BORE_DIA = 110.0
HALF_GOWLAND = GOWLAND / 2   # 69.5

# Clip parameters
CLIP_OVERLAP = 2.0
CLIP_BAR_LENGTH = 90.0
TOP_CLIP_WIDE = 14.0
TOP_CLIP_NARROW = 8.0
CLIP_CORNER_R = 2.0
TAB_BEND_RUN = 10.0
SLOT_LENGTH = 9.0
SLOT_WIDTH = 3.4
SLOT_ANGLE = 135.0
BOT_CLIP_WIDTH = 10.0

# Top clip in CLOSED (gravity) position:
# Closed = screw at +X,−Y end of 135° slot → clip shifts +dx, −dy
_half_travel = (SLOT_LENGTH - SLOT_WIDTH) / 2   # 2.8mm along slot
_closed_dx = _half_travel / math.sqrt(2)         # ≈ +1.98mm
_closed_dy = -_half_travel / math.sqrt(2)        # ≈ −1.98mm

# Top clip coordinates (closed position)
_top_outer_y = HALF_GOWLAND - CLIP_OVERLAP + TOP_CLIP_WIDE + _closed_dy  # 81.5 - 1.98 ≈ 79.52
_top_inner_wide = _top_outer_y - TOP_CLIP_WIDE                            # ≈ 65.52
_top_inner_narrow = _top_outer_y - TOP_CLIP_NARROW                        # ≈ 71.52
_hb = CLIP_BAR_LENGTH / 2                                                 # 45
_hb_shifted = _hb - _closed_dx                                            # 45 - 1.98 ≈ 43.02

# Top clip vertices in closed position (body outline with chamfer at upper-left)
# Bend line from A to B: A on outer edge, B on left edge
_tab_ax = -_hb_shifted + TAB_BEND_RUN + _closed_dx  # ≈ -33 + 1.98 ≈ -31.02...
# Actually: in closed position, clip is shifted (+dx, +dy) from neutral.
# Neutral clip body spans X=[-45, 45], Y=[67.5, 81.5].
# Closed: X=[-45+dx, 45+dx], Y=[67.5+dy, 81.5+dy].
# Let me just compute from the shifted values:
_cx = _closed_dx   # clip center X offset
_cy = _closed_dy   # clip center Y offset

TOP_CLIP_VERTS = [
    (-45 + _cx, 67.5 + _cy),    # lower-left
    (-20 + _cx, 67.5 + _cy),    # taper start
    (-15 + _cx, 73.5 + _cy),    # narrow
    ( 15 + _cx, 73.5 + _cy),
    ( 20 + _cx, 67.5 + _cy),    # taper back
    ( 45 + _cx, 67.5 + _cy),    # lower-right
    ( 45 + _cx, 81.5 + _cy),    # upper-right
    (-45 + TAB_BEND_RUN + _cx, 81.5 + _cy),  # A (bend start on outer edge)
    (-45 + _cx, 81.5 - TAB_BEND_RUN + _cy),  # B (bend end on left edge)
]

# Bottom clip (fixed, no offset)
bot_inner_y = -(HALF_GOWLAND - CLIP_OVERLAP)    # -67.5
bot_outer_y = bot_inner_y - BOT_CLIP_WIDTH       # -77.5
BOT_CLIP_VERTS = [
    (-45, bot_outer_y), (45, bot_outer_y),
    (45, bot_inner_y), (-45, bot_inner_y),
]

# Screw positions
# Top clip screws: offset in X for centering when closed
_screw_x_offset = -_half_travel / math.sqrt(2)   # ≈ -1.98
TOP_CLIP_SCREWS = [(-25 + _screw_x_offset, 74), (25 + _screw_x_offset, 74)]
BOT_CLIP_SCREWS = [(-25, -72.5), (25, -72.5)]
ASSY_SCREWS = [(-74.75, 0), (74.75, 0)]

# Paint geometry — on the clip body, offset by closed position
PAINT_CX = 0.0 + _cx
PAINT_CY = 77.5 + _cy   # center of narrow section

PAINT_INSET = 1.0        # mm inset from clip edges
PAINT_TAB_MARGIN = 1.0   # mm perpendicular margin from bend line
PAINT_CORNER_R = 2.0

# Paint extent: left side follows offset bend line (parallel, PAINT_TAB_MARGIN perp)
# Bend line equation (in neutral clip coords): X = Y - 116.5  (from A(-35,81.5) to B(-45,71.5))
# Offset paint line (inward): X = Y - 116.5 + PAINT_TAB_MARGIN * √2
# In closed position: shift by (_cx, _cy)
_pi = PAINT_INSET
_bend_offset_x = PAINT_TAB_MARGIN * math.sqrt(2)

# Paint boundary points (in absolute coords, closed position)
_pe_right = 45 + _cx - _pi          # right edge of paint
_pe_top = 81.5 + _cy - _pi          # top of paint
_pe_bot_wide = 67.5 + _cy + _pi     # bottom of wide section paint
_pe_bot_narrow = 73.5 + _cy + _pi   # bottom of narrow section paint

# Taper X positions — compute left/right separately (sign of _cx matters)
_pe_lt_outer = -20 + _cx             # left taper, outer (Y inset provides margin)
_pe_lt_inner = -15 + _cx             # left taper, narrow
_pe_rt_inner = 15 + _cx              # right taper, narrow
_pe_rt_outer = 20 + _cx              # right taper, outer

# Left edge follows offset bend line at each Y level
# In neutral clip coords: X_bend = Y - 116.5
# Offset: X_paint = Y - 116.5 + bend_offset_x
# In absolute: X_paint = (Y_abs - _cy) - 116.5 + bend_offset_x + _cx
def _bend_left_x(y):
    """X of paint left boundary at given Y (follows offset bend line)."""
    return (y - _cy) - 116.5 + _bend_offset_x + _cx

_left_top_x = _bend_left_x(_pe_top)
_left_bot_x = _bend_left_x(_pe_bot_wide)

PAINT_NARROW_H = _pe_top - _pe_bot_narrow

# Slot clearance
SLOT_CLEAR_MARGIN = 1.0

# Output
SAVE_DPI = 200

# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------
FUTURA_PATH = "/System/Library/Fonts/Supplemental/Futura.ttc"
try:
    futura_prop = fm.FontProperties(fname=FUTURA_PATH, weight="medium")
    fm.findfont(futura_prop)
except Exception:
    futura_prop = fm.FontProperties(family="sans-serif", weight="medium")
    print("Warning: Futura not found, falling back to sans-serif")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def rounded_rect_path(cx, cy, w, h, r):
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    r = min(r, w / 2, h / 2)
    verts = [
        (x0 + r, y0),
        (x1 - r, y0), (x1, y0), (x1, y0 + r),
        (x1, y1 - r), (x1, y1), (x1 - r, y1),
        (x0 + r, y1), (x0, y1), (x0, y1 - r),
        (x0, y0 + r), (x0, y0), (x0 + r, y0),
    ]
    codes = [
        Path.MOVETO,
        Path.LINETO, Path.CURVE3, Path.CURVE3,
        Path.LINETO, Path.CURVE3, Path.CURVE3,
        Path.LINETO, Path.CURVE3, Path.CURVE3,
        Path.LINETO, Path.CURVE3, Path.CURVE3,
    ]
    return Path(verts, codes)


def rounded_square_path(cx, cy, size, r):
    return rounded_rect_path(cx, cy, size, size, r)


def stadium_points(cx, cy, half_l, half_w, angle_deg, n_arc=16):
    """Return (xs, ys) outline of a stadium (rect with semicircular end caps)."""
    angle_rad = np.radians(angle_deg)
    ax_v = np.array([np.cos(angle_rad), np.sin(angle_rad)])
    perp = np.array([-np.sin(angle_rad), np.cos(angle_rad)])
    center = np.array([cx, cy])
    shl = max(half_l - half_w, 0.0)
    pts = []
    rc = center + shl * ax_v
    angle_perp = angle_rad + np.pi / 2
    for i in range(n_arc + 1):
        theta = angle_perp - np.pi * i / n_arc
        pts.append(rc + half_w * np.array([np.cos(theta), np.sin(theta)]))
    lc = center - shl * ax_v
    for i in range(n_arc + 1):
        theta = angle_perp - np.pi - np.pi * i / n_arc
        pts.append(lc + half_w * np.array([np.cos(theta), np.sin(theta)]))
    pts.append(pts[0])
    return [p[0] for p in pts], [p[1] for p in pts]


def draw_cam_slot(ax, cx, cy, length, width, angle_deg, **kwargs):
    """Draw a stadium-shaped cam slot."""
    xs, ys = stadium_points(cx, cy, length / 2, width / 2, angle_deg)
    ax.fill(xs, ys, **kwargs)


def _fillet_polygon(verts, radius, n_arc=6):
    """
    Take a list of (x, y) polygon vertices and return a new list with each
    corner replaced by a circular arc of the given radius. radius can be a
    scalar (same for all corners) or a list of per-vertex radii.
    """
    n = len(verts)
    if isinstance(radius, (int, float)):
        radii = [radius] * n
    else:
        radii = list(radius)
    result = []
    for i in range(n):
        r = radii[i]
        if r <= 0:
            result.append(tuple(verts[i]))
            continue
        p_prev = np.array(verts[(i - 1) % n])
        p_curr = np.array(verts[i])
        p_next = np.array(verts[(i + 1) % n])
        v_in = p_prev - p_curr
        v_out = p_next - p_curr
        len_in = np.linalg.norm(v_in)
        len_out = np.linalg.norm(v_out)
        if len_in < 1e-9 or len_out < 1e-9:
            result.append(tuple(p_curr))
            continue
        u_in = v_in / len_in
        u_out = v_out / len_out
        half_bisect = (u_in + u_out)
        half_len = np.linalg.norm(half_bisect)
        if half_len < 1e-9:
            result.append(tuple(p_curr))
            continue
        dot = np.clip(np.dot(u_in, u_out), -1, 1)
        angle = np.arccos(dot)
        half_angle = angle / 2
        if abs(np.sin(half_angle)) < 1e-9:
            result.append(tuple(p_curr))
            continue
        max_r = min(len_in, len_out) / 2 * 0.9
        r = min(r, max_r / np.tan(half_angle)) if np.tan(half_angle) > 1e-9 else r
        tan_len = r * np.tan(np.pi / 2 - half_angle)
        p_start = p_curr + u_in * tan_len
        p_end = p_curr + u_out * tan_len
        bisect = half_bisect / half_len
        center_dist = r / np.sin(half_angle)
        center = p_curr + bisect * center_dist
        angle_start = np.arctan2(p_start[1] - center[1], p_start[0] - center[0])
        angle_end = np.arctan2(p_end[1] - center[1], p_end[0] - center[0])
        cross = u_in[0] * u_out[1] - u_in[1] * u_out[0]
        if cross > 0:
            if angle_end > angle_start:
                angle_end -= 2 * np.pi
        else:
            if angle_end < angle_start:
                angle_end += 2 * np.pi
        angles = np.linspace(angle_start, angle_end, n_arc)
        for a in angles:
            result.append((center[0] + r * np.cos(a), center[1] + r * np.sin(a)))
    result.append(result[0])
    return result


def paint_outline_points():
    """
    Build the paint outline as a smooth polygon with rounded corners.
    Left side follows the offset bend line (parallel to 45° tab bend),
    clamped to clip left boundary + inset where the diagonal would exceed it.
    Vertices are counterclockwise: bottom inner edge → right → top → left diagonal.
    """
    # Clip left boundary + inset (in closed position)
    _clip_left_x = -_hb + _cx + _pi
    # Y where the diagonal paint edge meets the vertical clip boundary
    _y_diag_meets_vert = _cy + 71.5 + _pi - _bend_offset_x
    needs_clamp = _left_bot_x < _clip_left_x

    # Start at left taper, trace counterclockwise
    sharp = [
        (_pe_lt_outer, _pe_bot_wide),      # left taper, bottom
        (_pe_lt_inner, _pe_bot_narrow),    # left taper, narrow
        (_pe_rt_inner, _pe_bot_narrow),    # right taper, narrow
        (_pe_rt_outer, _pe_bot_wide),      # right taper, bottom
        ( _pe_right, _pe_bot_wide),        # bottom-right
        ( _pe_right, _pe_top),             # top-right
        (_left_top_x, _pe_top),            # top-left (bend line margin)
    ]
    if needs_clamp:
        # Diagonal extends past clip left edge — add vertical segment
        sharp.append((_clip_left_x, _y_diag_meets_vert))   # diagonal → vertical
        sharp.append((_clip_left_x, _pe_bot_wide))          # bottom-left (clamped)
    else:
        sharp.append((_left_bot_x, _pe_bot_wide))           # bottom-left on diagonal
    # Closing segment: bottom-left → left taper (horizontal at _pe_bot_wide)
    return _fillet_polygon(sharp, PAINT_CORNER_R)


def draw_paint_fill(ax, edgecolor="none", lw=0, **kwargs):
    """Draw the full-clip paint area with rounded corners and slot clearance cutouts."""
    outline = paint_outline_points()
    ax.fill([p[0] for p in outline], [p[1] for p in outline],
            color=PAINT_BLACK, edgecolor=edgecolor, lw=lw, zorder=7, **kwargs)
    # Slot clearance racetracks (screws are at fixed adapter positions)
    clear_half_l = SLOT_LENGTH / 2 + SLOT_CLEAR_MARGIN
    clear_half_w = SLOT_WIDTH / 2 + SLOT_CLEAR_MARGIN
    for sx, sy in TOP_CLIP_SCREWS:
        xs, ys = stadium_points(sx, sy, clear_half_l, clear_half_w, SLOT_ANGLE)
        ax.fill(xs, ys, color=STAINLESS, edgecolor="none", zorder=8)


def get_px_per_mm(ax):
    d0 = ax.transData.transform((0, 0))
    d1 = ax.transData.transform((1, 0))
    return d1[0] - d0[0]


def draw_spaced_text(ax, text, cx, cy, paint_h_mm, color, spacing_em=0.5):
    """Draw 'text' in Futura centered in a paint area at (cx, cy)."""
    fig = ax.get_figure()
    fig_dpi = fig.dpi
    px_per_mm = get_px_per_mm(ax)
    du_per_px = 1.0 / px_per_mm
    pts_per_px = 72.0 / fig_dpi
    ref_em = 400
    ref_font = ImageFont.truetype(FUTURA_PATH, ref_em)
    ref_ascent, _ = ref_font.getmetrics()
    canvas_w = ref_em * len(text) * 3
    canvas_h = ref_em * 3
    ref_img = Image.new("L", (canvas_w, canvas_h), 0)
    ref_draw = ImageDraw.Draw(ref_img)
    anchor_x, anchor_y = ref_em, ref_em
    ref_draw.text((anchor_x, anchor_y), text, font=ref_font, fill=255)
    ref_arr = np.array(ref_img)
    ink_rows = np.where(np.any(ref_arr > 0, axis=1))[0]
    ink_top = ink_rows[0]
    ink_bot = ink_rows[-1]
    ink_h = ink_bot - ink_top + 1
    baseline_row = anchor_y + ref_ascent
    ink_above_baseline = baseline_row - ink_top
    ink_below_baseline = ink_bot - baseline_row
    ink_center_above_bl = (ink_above_baseline - ink_below_baseline) / 2.0
    margin_frac = 0.15
    target_ink_h_mm = paint_h_mm * (1.0 - 2 * margin_frac)
    target_ink_h_px = target_ink_h_mm * px_per_mm
    scale = target_ink_h_px / ink_h
    em_px = ref_em * scale
    fontsize_pts = em_px * pts_per_px
    baseline_y = cy - (ink_center_above_bl * scale * du_per_px)
    render_font = ImageFont.truetype(FUTURA_PATH, max(int(round(em_px)), 1))
    char_widths_px = []
    for ch in text:
        bbox = render_font.getbbox(ch)
        char_widths_px.append(bbox[2] - bbox[0])
    avg_w = max(np.mean(char_widths_px), 1)
    char_w = [w * du_per_px for w in char_widths_px]
    gap = avg_w * spacing_em * du_per_px
    total_w = sum(char_w) + gap * (len(text) - 1)
    x = cx - total_w / 2
    for ch, w in zip(text, char_w):
        ax.text(x + w / 2, baseline_y, ch, fontproperties=futura_prop,
                fontsize=fontsize_pts, color=color, ha="center", va="baseline",
                zorder=10)
        x += w + gap


def _draw_clip(ax, verts, corner_r, edgecolor, lw, zorder, facecolor=STAINLESS):
    """Draw a clip with filleted corners."""
    filleted = _fillet_polygon(verts, corner_r)
    ax.fill([p[0] for p in filleted], [p[1] for p in filleted],
            color=facecolor, edgecolor=edgecolor, lw=lw, zorder=zorder)


# ---------------------------------------------------------------------------
# Draw geometry
# ---------------------------------------------------------------------------
def draw_full_view_geom(ax):
    ax.set_aspect("equal")
    ax.set_xlim(-105, 105)
    ax.set_ylim(-105, 105)
    ax.set_facecolor("#F5F5F0")
    ax.set_title("Fatif Adapter \u2014 Front View", fontsize=11, fontweight="bold", pad=8)

    ax.add_patch(mpatches.PathPatch(
        rounded_square_path(0, 0, BOARD, R_BOARD),
        facecolor=DARK_GRAY, edgecolor=SHEET_EDGE, lw=1.2, zorder=1))
    ax.add_patch(mpatches.PathPatch(
        rounded_square_path(0, 0, GOWLAND, R_GOWLAND),
        facecolor="#1A1A1A", edgecolor="#333333", lw=0.8, zorder=2))
    ax.add_patch(Circle((0, 0), BORE_DIA / 2,
                         facecolor=BORE_BLACK, edgecolor="#222222", lw=0.6, zorder=3))

    # Top clip (closed position, with corner radii)
    # Per-vertex radii: R2 on body corners, 0 on bend endpoints A and B
    tc_radii = [CLIP_CORNER_R] * 6 + [CLIP_CORNER_R, 0, 0]  # 6 body + A + B
    _draw_clip(ax, TOP_CLIP_VERTS, tc_radii, STAINLESS_EDGE, 1.0, 5)

    # 45° diagonal bend line (A to B in closed position)
    ax.plot([TOP_CLIP_VERTS[7][0], TOP_CLIP_VERTS[8][0]],
            [TOP_CLIP_VERTS[7][1], TOP_CLIP_VERTS[8][1]],
            color=STAINLESS_EDGE, lw=1.5, zorder=6, linestyle="--", solid_capstyle="butt")

    # Paint fill
    draw_paint_fill(ax)

    # Cam slot holes
    for sx, sy in TOP_CLIP_SCREWS:
        draw_cam_slot(ax, sx, sy, SLOT_LENGTH, SLOT_WIDTH, SLOT_ANGLE,
                      color="#333333", edgecolor="#555555", linewidth=0.3, zorder=9)

    # Bottom clip (with corner radii)
    _draw_clip(ax, BOT_CLIP_VERTS, CLIP_CORNER_R, STAINLESS_EDGE, 1.0, 5)

    # Screws
    for sx, sy in ASSY_SCREWS:
        ax.plot(sx, sy, "o", color=SCREW_COLOR, markersize=4, zorder=9)
        ax.plot(sx, sy, "+", color="#333333", markersize=3, markeredgewidth=0.6, zorder=9)
    for sx, sy in TOP_CLIP_SCREWS:
        ax.plot(sx, sy, "o", color=SCREW_COLOR, markersize=2.5, zorder=9)
    for sx, sy in BOT_CLIP_SCREWS:
        ax.plot(sx, sy, "o", color=SCREW_COLOR, markersize=2.5, zorder=9)

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def draw_detail_geom(ax):
    ax.set_aspect("equal")
    ax.set_xlim(-52, 52)
    ax.set_ylim(61, 84)
    ax.set_facecolor("#F5F5F0")
    ax.set_title("Top Clip \u2014 Nameplate Detail (4\u00d7 zoom)", fontsize=11,
                 fontweight="bold", pad=8)

    # Top clip with corner radii
    tc_radii = [CLIP_CORNER_R] * 6 + [CLIP_CORNER_R, 0, 0]
    _draw_clip(ax, TOP_CLIP_VERTS, tc_radii, STAINLESS_EDGE, 1.5, 2)

    # 45° diagonal bend line
    ax.plot([TOP_CLIP_VERTS[7][0], TOP_CLIP_VERTS[8][0]],
            [TOP_CLIP_VERTS[7][1], TOP_CLIP_VERTS[8][1]],
            color=STAINLESS_EDGE, lw=2, zorder=3, linestyle="--", solid_capstyle="butt")
    ax.annotate("tab\n(45\u00b0 bend)", xy=(TOP_CLIP_VERTS[8][0] - 3, (TOP_CLIP_VERTS[7][1] + TOP_CLIP_VERTS[8][1]) / 2),
                fontsize=5, ha="center", va="center", color="#666666", zorder=4)

    # Paint fill
    draw_paint_fill(ax, edgecolor="#444444", lw=0.8)

    # Cam slot holes
    for sx, sy in TOP_CLIP_SCREWS:
        draw_cam_slot(ax, sx, sy, SLOT_LENGTH, SLOT_WIDTH, SLOT_ANGLE,
                      color="#333333", edgecolor="#555555", linewidth=0.5, zorder=9)

    # Screw heads
    for sx, sy in TOP_CLIP_SCREWS:
        ax.plot(sx, sy, "o", color=SCREW_COLOR, markersize=5, zorder=9)
        ax.plot(sx, sy, "+", color="#333333", markersize=4, markeredgewidth=0.8, zorder=9)

    # Dimension annotations
    ax.text(-37 + _cx, _pe_top + 1.5, f"{PAINT_INSET:.0f}mm inset", fontsize=4.5,
            ha="center", color="#888888", style="italic")

    cw_y = 62.0
    ax.annotate("", xy=(45 + _cx, cw_y), xytext=(-45 + _cx, cw_y),
                arrowprops=dict(arrowstyle="<->", color="#4477AA", lw=0.8))
    ax.text(0 + _cx, cw_y - 1.0, "90mm (clip length)", fontsize=5, ha="center", color="#4477AA")

    ax.annotate("8mm\n(narrow)", xy=(0 + _cx, _pe_bot_narrow - 0.5), fontsize=5, ha="center", va="top",
                color="#666666", style="italic")

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    fig = plt.figure(figsize=(10, 14), dpi=SAVE_DPI, facecolor="white")

    ax1 = fig.add_axes([0.05, 0.42, 0.90, 0.55])
    draw_full_view_geom(ax1)

    ax2 = fig.add_axes([0.05, 0.02, 0.90, 0.38])
    draw_detail_geom(ax2)

    fig.canvas.draw()

    draw_spaced_text(ax1, "fatif", PAINT_CX, PAINT_CY, paint_h_mm=PAINT_NARROW_H,
                     color=STAINLESS_BRIGHT)
    draw_spaced_text(ax2, "fatif", PAINT_CX, PAINT_CY, paint_h_mm=PAINT_NARROW_H,
                     color=STAINLESS_BRIGHT)

    out = "fatif_nameplate_mockup.png"
    fig.savefig(out, dpi=SAVE_DPI, facecolor="white")
    print(f"Saved {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
