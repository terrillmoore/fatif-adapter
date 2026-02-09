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

TOP_CLIP_VERTS = [
    (-45, 66), (-20, 66), (-15, 72),
    (15, 72), (20, 66), (45, 66),
    (45, 80), (-45, 80),
]

BOT_CLIP_VERTS = [
    (-45, -80), (45, -80),
    (45, -70), (-45, -70),
]

ASSY_SCREWS = [(-74.75, 0), (74.75, 0)]
TOP_CLIP_SCREWS = [(-25, 74), (25, 74)]
BOT_CLIP_SCREWS = [(-25, -72.5), (25, -72.5)]

PAINT_CX = 0.0
PAINT_CY = 76.0  # center of narrow section (for text placement)

# Paint fill: inset ~1mm from clip edges, stops at tab bend lines
PAINT_INSET = 1.0       # mm inset from clip edges
PAINT_TAB_MARGIN = 2.0  # mm from clip ends to clear the bend line

# Inset paint outline (follows dog-bone, R side then mirrored)
# Clip ends at X=±45; paint stops at ±43
# Clip outer Y=80 → paint Y=79; inner wide Y=66 → paint Y=67
# Inner narrow Y=72 → paint Y=73; taper X=15→20 → paint X=16→21
_pe = 45 - PAINT_TAB_MARGIN   # 43
_pi = PAINT_INSET
PAINT_VERTS = [
    (-_pe, 66 + _pi),           # bottom-left (wide section)
    (-20 - _pi, 66 + _pi),      # approach taper
    (-15 - _pi, 72 + _pi),      # taper to narrow
    ( 15 + _pi, 72 + _pi),      # narrow section
    ( 20 + _pi, 66 + _pi),      # taper back to wide
    ( _pe, 66 + _pi),           # bottom-right (wide section)
    ( _pe, 80 - _pi),           # top-right
    (-_pe, 80 - _pi),           # top-left
]

# The narrow section height for text sizing (paint inner narrow to paint outer)
PAINT_NARROW_H = (80 - _pi) - (72 + _pi)  # 79 - 73 = 6mm

SLOT_LENGTH = 9.0
SLOT_WIDTH = 3.4
SLOT_ANGLE = 135.0

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


def draw_cam_slot(ax, cx, cy, length, width, angle_deg, **kwargs):
    angle_rad = np.radians(angle_deg)
    half_l, half_w = length / 2, width / 2
    dx, dy = np.cos(angle_rad), np.sin(angle_rad)
    nx, ny = -dy, dx
    n_arc = 12
    pts = []
    for i in range(n_arc + 1):
        theta = np.pi / 2 + np.pi * i / n_arc
        pts.append((cx + half_l * dx + half_w * (nx * np.cos(theta) + dx * np.sin(theta)),
                     cy + half_l * dy + half_w * (ny * np.cos(theta) + dy * np.sin(theta))))
    for i in range(n_arc + 1):
        theta = -np.pi / 2 + np.pi * i / n_arc
        pts.append((cx - half_l * dx + half_w * (nx * np.cos(theta) + dx * np.sin(theta)),
                     cy - half_l * dy + half_w * (ny * np.cos(theta) + dy * np.sin(theta))))
    pts.append(pts[0])
    xs, ys = zip(*pts)
    ax.fill(xs, ys, **kwargs)


def draw_paint_fill(ax, edgecolor="none", lw=0, **kwargs):
    """Draw the full-clip paint area (inset dog-bone polygon)."""
    pv = PAINT_VERTS
    ax.fill([v[0] for v in pv], [v[1] for v in pv],
            color=PAINT_BLACK, edgecolor=edgecolor, lw=lw, zorder=7, **kwargs)


def get_px_per_mm(ax):
    """Get pixels per data-unit (mm) from the axes transform. Call after fig.canvas.draw()."""
    d0 = ax.transData.transform((0, 0))
    d1 = ax.transData.transform((1, 0))
    return d1[0] - d0[0]


def draw_spaced_text(ax, text, cx, cy, paint_h_mm, color, spacing_em=0.5):
    """
    Draw 'text' in Futura centered in a paint area at (cx, cy).
    Sizes the text to fit within paint_h_mm with equal top/bottom margins.
    Uses Pillow rendering to measure actual ink bounds, then places text
    with va='baseline' at the exact computed baseline position.
    Must be called after fig.canvas.draw() so transData is accurate.
    """
    fig = ax.get_figure()
    fig_dpi = fig.dpi
    px_per_mm = get_px_per_mm(ax)
    du_per_px = 1.0 / px_per_mm
    pts_per_px = 72.0 / fig_dpi

    # --- Render text with Pillow at a reference size to measure ink bounds ---
    ref_em = 400  # large for precision
    ref_font = ImageFont.truetype(FUTURA_PATH, ref_em)
    ref_ascent, _ = ref_font.getmetrics()

    # Draw at anchor (0, 0) — Pillow places the top-left of the line box at (0, 0),
    # so the baseline is at y = ref_ascent.
    canvas_w = ref_em * len(text) * 3
    canvas_h = ref_em * 3
    ref_img = Image.new("L", (canvas_w, canvas_h), 0)
    ref_draw = ImageDraw.Draw(ref_img)
    # Draw at a known anchor position
    anchor_x, anchor_y = ref_em, ref_em
    ref_draw.text((anchor_x, anchor_y), text, font=ref_font, fill=255)
    ref_arr = np.array(ref_img)

    ink_rows = np.where(np.any(ref_arr > 0, axis=1))[0]
    ink_top = ink_rows[0]    # topmost ink pixel row
    ink_bot = ink_rows[-1]   # bottommost ink pixel row
    ink_h = ink_bot - ink_top + 1

    # Baseline is at anchor_y + ref_ascent in image coordinates
    baseline_row = anchor_y + ref_ascent

    # Ink position relative to baseline (positive = above baseline in image = above)
    ink_above_baseline = baseline_row - ink_top   # pixels from baseline up to ink top
    ink_below_baseline = ink_bot - baseline_row    # pixels from baseline down to ink bottom

    # Ink center relative to baseline (positive = above baseline)
    ink_center_above_bl = (ink_above_baseline - ink_below_baseline) / 2.0

    # --- Size the text to fit within paint area with margins ---
    margin_frac = 0.15
    target_ink_h_mm = paint_h_mm * (1.0 - 2 * margin_frac)
    target_ink_h_px = target_ink_h_mm * px_per_mm

    scale = target_ink_h_px / ink_h
    em_px = ref_em * scale
    fontsize_pts = em_px * pts_per_px

    # --- Compute baseline Y in data coordinates ---
    # We want the ink center at cy. The ink center is ink_center_above_bl * scale
    # pixels above the baseline. In data coords (Y up):
    #   cy = baseline_y + ink_center_above_bl * scale * du_per_px
    #   baseline_y = cy - ink_center_above_bl * scale * du_per_px
    baseline_y = cy - (ink_center_above_bl * scale * du_per_px)

    # --- Measure character widths at final size ---
    render_font = ImageFont.truetype(FUTURA_PATH, max(int(round(em_px)), 1))
    char_widths_px = []
    for ch in text:
        bbox = render_font.getbbox(ch)
        char_widths_px.append(bbox[2] - bbox[0])
    avg_w = max(np.mean(char_widths_px), 1)

    char_w = [w * du_per_px for w in char_widths_px]
    gap = avg_w * spacing_em * du_per_px
    total_w = sum(char_w) + gap * (len(text) - 1)

    # --- Place characters using va='baseline' ---
    x = cx - total_w / 2
    for ch, w in zip(text, char_w):
        ax.text(x + w / 2, baseline_y, ch, fontproperties=futura_prop,
                fontsize=fontsize_pts, color=color, ha="center", va="baseline",
                zorder=10)
        x += w + gap


# ---------------------------------------------------------------------------
# Draw geometry (no text — text added after canvas.draw())
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

    # Top clip
    tc = TOP_CLIP_VERTS
    ax.fill([v[0] for v in tc], [v[1] for v in tc],
            color=STAINLESS, edgecolor=STAINLESS_EDGE, lw=1.0, zorder=5)

    # Tab indicators
    for sign in [-1, 1]:
        tx = sign * 45
        ax.plot([tx, tx], [72, 80], color=STAINLESS_EDGE, lw=2.5, zorder=6,
                solid_capstyle="butt")
        ax.annotate("", xy=(tx + sign * 3, 76), xytext=(tx, 76),
                    arrowprops=dict(arrowstyle="->", color=STAINLESS_EDGE, lw=1.0), zorder=6)

    # Paint fill (full clip face)
    draw_paint_fill(ax)

    # Cam slots (punch through paint — show stainless behind)
    for sx in [-25, 25]:
        draw_cam_slot(ax, sx, 74, SLOT_LENGTH, SLOT_WIDTH, SLOT_ANGLE,
                      color=STAINLESS, edgecolor=STAINLESS_EDGE, linewidth=0.4, zorder=8)

    # Bottom clip
    bc = BOT_CLIP_VERTS
    ax.fill([v[0] for v in bc], [v[1] for v in bc],
            color=STAINLESS, edgecolor=STAINLESS_EDGE, lw=1.0, zorder=5)

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
    ax.set_ylim(62, 84)
    ax.set_facecolor("#F5F5F0")
    ax.set_title("Top Clip \u2014 Nameplate Detail (4\u00d7 zoom)", fontsize=11,
                 fontweight="bold", pad=8)

    tc = TOP_CLIP_VERTS
    ax.fill([v[0] for v in tc], [v[1] for v in tc],
            color=STAINLESS, edgecolor=STAINLESS_EDGE, lw=1.5, zorder=2)

    for sign in [-1, 1]:
        tx = sign * 45
        ax.plot([tx, tx], [66, 80], color=STAINLESS_EDGE, lw=3, zorder=3,
                solid_capstyle="butt")
        ax.annotate("tab\n(bend up)", xy=(tx, 73), fontsize=5,
                    ha="center", va="center", color="#666666", zorder=4)

    # Paint fill (full clip face)
    draw_paint_fill(ax, edgecolor="#444444", lw=0.8)

    # Cam slots (punch through paint — show stainless)
    for sx in [-25, 25]:
        draw_cam_slot(ax, sx, 74, SLOT_LENGTH, SLOT_WIDTH, SLOT_ANGLE,
                      color=STAINLESS, edgecolor=STAINLESS_EDGE, linewidth=0.6, zorder=8)

    # Screw heads (visible through cam slots)
    for sx, sy in TOP_CLIP_SCREWS:
        ax.plot(sx, sy, "o", color=SCREW_COLOR, markersize=5, zorder=9)
        ax.plot(sx, sy, "+", color="#333333", markersize=4, markeredgewidth=0.8, zorder=9)

    # Dimension annotations
    ann_color = "#CC4444"
    ann_kw = dict(color=ann_color, fontsize=6, ha="center", va="center",
                  fontweight="bold",
                  bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=ann_color,
                            alpha=0.9, lw=0.6))

    # Paint inset margin
    ax.text(-37, 80.8, f"{PAINT_INSET:.0f}mm inset", fontsize=4.5,
            ha="center", color="#888888", style="italic")

    # Clip overall length
    cw_y = 64.0
    ax.annotate("", xy=(45, cw_y), xytext=(-45, cw_y),
                arrowprops=dict(arrowstyle="<->", color="#4477AA", lw=0.8))
    ax.text(0, cw_y - 1.2, "90mm (clip length)", fontsize=5, ha="center", color="#4477AA")

    # Narrow section label
    ax.annotate("8mm\n(narrow)", xy=(0, 72.3), fontsize=5, ha="center", va="top",
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

    # Finalize layout so transData is accurate
    fig.canvas.draw()

    # Add text with properly computed font sizes
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
