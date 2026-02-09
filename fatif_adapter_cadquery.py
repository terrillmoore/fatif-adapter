#!/usr/bin/env python3
"""
Fatif DS 20x25 Adapter Lensboard — Three-Piece Laminated Design

Generates STEP and DXF files for laser-cut fabrication (SendCutSend).

Design: Terry Moore / Claude
Assembly: Three sheets laminated with M3 flat head screws

Materials (as-finished thicknesses from SendCutSend):
  Front:  .063" 6061-T6, powder coated matte black → 1.78mm
  Middle: .025" 2024-T3, bare (sandwiched, no finish needed) → 0.64mm
  Rear:   .100" 6061-T6, black anodized → ~2.56mm

Coordinate convention:
  Z axis: z=0 is back face (camera side)
  Rear sheet:   z=0.00 to z=2.56  (camera side, black anodized)
  Middle sheet: z=2.56 to z=3.20  (light seal, bare aluminum)
  Front sheet:  z=3.20 to z=4.98  (lens side, powder coated)
  XY: origin at center of board
  +Y = top, -Y = bottom, +X = right, -X = left (viewed from lens side)

Dimensions from caliper measurements of Fatif DS original lensboard:
  Outer profile: 171.5mm square, R50.75 corners (70mm straight edge)
  Lip thickness: 2.50mm (clips accommodate exactly this, no more)
  Lip/step width: 5.75mm from outer edge
  Casting opening depth: 5.5mm (4.9mm to inner rib)

Three-piece laminated approach:
  Front sheet (1.78mm): Full Fatif profile with Gowland cutout
  Middle sheet (0.64mm): Full Fatif profile with bore only — seals
    corner light leaks where rear sheet R45 corners don't cover
    the front sheet's 139mm square cutout at the diagonals
  Rear sheet (2.56mm): Smaller "baffle" profile with bore
  Front+middle overhang rear by 5.75mm all around, creating the
    2.42mm lip that seats into the Fatif standard spring clips.
  Total thickness: 1.78 + 0.64 + 2.56 = 4.98mm

Board retention — Cambo / Crown Graphic style clips:
  Fixed bottom clip: rectangular flat bar, 2 screws, no tabs
  Sliding top clip: dog-bone profile (wider at slot ends, narrower in
    middle), 135° cam slots (push -X to open, gravity closes), single
    45° tab at -X end for finger grip (Crown Graphic style)
  Clip material: .060" 304 stainless steel (1.52mm)
"""

import cadquery as cq
import math
import os

# ================================================================
# PARAMETERS (all dimensions in mm, as-finished unless noted)
# ================================================================

# --- Outer profile (from caliper measurements of Fatif original) ---
BOARD_SIZE = 171.5          # square dimension (ruler measurement)
BOARD_CORNER_R = 50.75      # corner radius: (171.5 - 70mm straight edge) / 2

# --- Sheet thicknesses (as-finished, including coatings) ---
# Front: SendCutSend .063" 6061-T6 powder coated (1.60 raw + 0.18 coat)
# Middle: SendCutSend .025" 2024-T3 bare (sandwiched, no finish)
# Rear: SendCutSend .100" 6061-T6 black anodized (2.54 raw + ~0.02 anodize)
FRONT_THICK = 1.78          # .063" 6061 powder coated
MIDDLE_THICK = 0.64         # .025" 2024-T3 bare
REAR_THICK = 2.56           # .100" 6061 black anodized

TOTAL_THICKNESS = FRONT_THICK + MIDDLE_THICK + REAR_THICK  # = 4.98mm

# --- Back perimeter step (from caliper measurement) ---
STEP_WIDTH = 5.75           # lip width from outer edge (caliper)
REAR_SIZE = BOARD_SIZE - 2 * STEP_WIDTH        # = 160.0
REAR_CORNER_R = BOARD_CORNER_R - STEP_WIDTH    # = 45.0

# --- Front cutout (Gowland board drops through this) ---
# Gowland boards measure 137.76 x 137.70mm; cutout gives ~0.6mm clearance/side
GOWLAND_SIZE = 139.0        # cutout size
GOWLAND_CORNER_R = 3.4      # Gowland board corner radius

# --- Central through bore (rear + middle sheets) ---
BORE_DIA = 110.0            # clears Ilex #5 flange with margin

# --- Assembly screws (M3 flat head, countersunk into front sheet) ---
M3_CLEARANCE = 3.4          # M3 clearance hole diameter
M3_TAP = 2.5                # M3 tap drill diameter
M3_CSK_DIA = 6.5            # M3 flat head countersink diameter
M3_CSK_DEPTH = 1.2          # countersink depth (< FRONT_THICK)

# --- Screw placement ---
# Overlap zone where all three sheets are solid:
#   Front cutout inner edge: 69.5mm from center
#   Rear sheet outer edge:   80.0mm from center
#   Band: 69.5 to 80.0mm (10.5mm wide)
ASSY_SCREW_R = 74.75        # midpoint of overlap band

# Clip screws at top and bottom (also laminate all three sheets)
CLIP_SCREW_X_SPACING = 50.0 # distance between clip screw pair
BOT_CLIP_SCREW_Y = 72.5     # Y offset for bottom clip screws
TOP_CLIP_SCREW_Y = 74.0     # Y offset for top clip screws
# Top clip X offset: center clip in X when in closed (gravity) position.
# Closed position shifts clip +X by half_travel/√2 along 135° slot.
import math as _m
_half_travel = (9.0 - 3.4) / 2   # (SLOT_LENGTH - SLOT_WIDTH) / 2
TOP_CLIP_SCREW_X_OFFSET = -_half_travel / _m.sqrt(2)  # ≈ -1.98mm

# --- Clips (Cambo / Crown Graphic style) ---
# Material: 304 stainless steel, .060" (1.52mm)
CLIP_BAR_LENGTH = 90.0      # flat bar length on adapter face (both clips)
CLIP_THICK = 1.52           # .060" 304 stainless steel
CLIP_OVERLAP = 2.0          # overlap onto board edge (both clips) — enough to retain, allows angling board in
TAB_HEIGHT = 8.0            # tab height (perpendicular to bend line)
TAB_BEND_RUN = 10.0         # 45° bend line: 10mm along each edge from corner
CLIP_CORNER_R = 2.0         # corner radius for clip body (finger-friendly)

# Bottom clip: simple rectangular bar
BOT_CLIP_WIDTH = 10.0       # uniform width

# Top clip: dog-bone profile (Crown Graphic style)
# Wider at screw/slot ends, narrower in middle (nameplate area).
# Inner edge (board side) has dog-bone profile.
# Outer edge (+Y) is straight.
# Single 45° tab at -X end (matches 135° cam slot push direction).
TOP_CLIP_WIDE = 14.0        # width at ends (accommodates cam slots)
TOP_CLIP_NARROW = 8.0       # width in middle
TOP_CLIP_TAPER_INNER = 15.0 # X from center where taper begins
TOP_CLIP_TAPER_OUTER = 20.0 # X from center where full width begins

# Top clip cam slots (135° = cam action: push tab -X to open,
# gravity return to closed)
SLOT_LENGTH = 9.0           # slot length
SLOT_WIDTH = 3.4            # M3 clearance
SLOT_ANGLE = 135.0          # degrees from X axis

# --- Derived ---
HALF_BOARD = BOARD_SIZE / 2
HALF_GOWLAND = GOWLAND_SIZE / 2
HALF_REAR = REAR_SIZE / 2

REAR_Z_BOT = 0.0
REAR_Z_TOP = REAR_THICK
MIDDLE_Z_BOT = REAR_THICK
MIDDLE_Z_TOP = REAR_THICK + MIDDLE_THICK
FRONT_Z_BOT = REAR_THICK + MIDDLE_THICK
FRONT_Z_TOP = TOTAL_THICKNESS

# Lip thickness = front + middle (these two sheets overhang the rear)
LIP_THICK = FRONT_THICK + MIDDLE_THICK  # = 2.42mm (≤ 2.50mm clip limit)


# ================================================================
# HELPER: rounded rectangle sketch
# ================================================================

def rounded_rect(wp, size, corner_r):
    """Create a rounded rectangle sketch on the given workplane."""
    return (
        wp.sketch()
        .rect(size, size)
        .vertices().fillet(corner_r)
        .finalize()
    )


# ================================================================
# SCREW HOLE POSITIONS
# ================================================================

# Assembly screws: left and right only.  Top/bottom positions are
# covered by clip screws, which also laminate all three sheets.
ASSY_SCREW_POSITIONS = [
    ( ASSY_SCREW_R,  0),   # right
    (-ASSY_SCREW_R,  0),   # left
]

# Bottom clip screws: 2 positions at -Y
BOTTOM_CLIP_SCREW_POSITIONS = [
    (-CLIP_SCREW_X_SPACING / 2, -BOT_CLIP_SCREW_Y),
    ( CLIP_SCREW_X_SPACING / 2, -BOT_CLIP_SCREW_Y),
]

# Top clip screws: 2 positions at +Y (offset in X so clip is centered when closed)
TOP_CLIP_SCREW_POSITIONS = [
    (-CLIP_SCREW_X_SPACING / 2 + TOP_CLIP_SCREW_X_OFFSET, TOP_CLIP_SCREW_Y),
    ( CLIP_SCREW_X_SPACING / 2 + TOP_CLIP_SCREW_X_OFFSET, TOP_CLIP_SCREW_Y),
]

ALL_SCREW_POSITIONS = (
    ASSY_SCREW_POSITIONS +
    BOTTOM_CLIP_SCREW_POSITIONS +
    TOP_CLIP_SCREW_POSITIONS
)


# ================================================================
# PART 1: FRONT SHEET
# ================================================================

print("Building three-piece laminated Fatif adapter...\n")
print("  [1/6] Front sheet: %.1fmm sq, R%.2f, %.2fmm thick (z=%.2f to %.2f)"
      % (BOARD_SIZE, BOARD_CORNER_R, FRONT_THICK, FRONT_Z_BOT, FRONT_Z_TOP))
print("         .063\" 6061-T6 powder coated matte black")

# Base plate
front_sheet = (
    rounded_rect(cq.Workplane("XY").workplane(offset=FRONT_Z_BOT),
                 BOARD_SIZE, BOARD_CORNER_R)
    .extrude(FRONT_THICK)
)

# Gowland cutout (through-all)
cutout = (
    rounded_rect(cq.Workplane("XY").workplane(offset=FRONT_Z_BOT - 1),
                 GOWLAND_SIZE, GOWLAND_CORNER_R)
    .extrude(FRONT_THICK + 2)
)
front_sheet = front_sheet.cut(cutout)

# Clearance holes for all screws
for (x, y) in ALL_SCREW_POSITIONS:
    hole = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_BOT - 1)
        .center(x, y)
        .circle(M3_CLEARANCE / 2)
        .extrude(FRONT_THICK + 2)
    )
    front_sheet = front_sheet.cut(hole)

# Countersinks only for assembly screws (clip screws use pan heads
# that sit on top of the clips, not countersunk into the front sheet)
for (x, y) in ASSY_SCREW_POSITIONS:
    csk = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_TOP - M3_CSK_DEPTH)
        .center(x, y)
        .circle(M3_CSK_DIA / 2)
        .extrude(M3_CSK_DEPTH + 1)
    )
    front_sheet = front_sheet.cut(csk)


# ================================================================
# PART 2: MIDDLE SHEET (light seal)
# ================================================================

print("  [2/6] Middle sheet: %.1fmm sq, R%.2f, %.2fmm thick (z=%.2f to %.2f)"
      % (BOARD_SIZE, BOARD_CORNER_R, MIDDLE_THICK, MIDDLE_Z_BOT, MIDDLE_Z_TOP))
print("         .025\" 2024-T3 bare (sandwiched)")

# Same outer profile as front sheet — full Fatif size for corner coverage
middle_sheet = (
    rounded_rect(cq.Workplane("XY").workplane(offset=MIDDLE_Z_BOT),
                 BOARD_SIZE, BOARD_CORNER_R)
    .extrude(MIDDLE_THICK)
)

# Central bore
bore_middle = (
    cq.Workplane("XY")
    .workplane(offset=MIDDLE_Z_BOT - 1)
    .circle(BORE_DIA / 2)
    .extrude(MIDDLE_THICK + 2)
)
middle_sheet = middle_sheet.cut(bore_middle)

# Clearance holes for all screws
for (x, y) in ALL_SCREW_POSITIONS:
    hole = (
        cq.Workplane("XY")
        .workplane(offset=MIDDLE_Z_BOT - 1)
        .center(x, y)
        .circle(M3_CLEARANCE / 2)
        .extrude(MIDDLE_THICK + 2)
    )
    middle_sheet = middle_sheet.cut(hole)


# ================================================================
# PART 3: REAR SHEET
# ================================================================

print("  [3/6] Rear sheet: %.1fmm sq, R%.2f, %.2fmm thick (z=%.2f to %.2f)"
      % (REAR_SIZE, REAR_CORNER_R, REAR_THICK, REAR_Z_BOT, REAR_Z_TOP))
print("         .100\" 6061-T6 black anodized")

# Base plate
rear_sheet = (
    rounded_rect(cq.Workplane("XY"), REAR_SIZE, REAR_CORNER_R)
    .extrude(REAR_THICK)
)

# Central bore
bore_rear = (
    cq.Workplane("XY")
    .workplane(offset=-1)
    .circle(BORE_DIA / 2)
    .extrude(REAR_THICK + 2)
)
rear_sheet = rear_sheet.cut(bore_rear)

# Tap drill holes for all screws
for (x, y) in ALL_SCREW_POSITIONS:
    tap_hole = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .center(x, y)
        .circle(M3_TAP / 2)
        .extrude(REAR_THICK + 2)
    )
    rear_sheet = rear_sheet.cut(tap_hole)


# ================================================================
# PART 4: FIXED BOTTOM CLIP
# ================================================================

# Simple rectangular bar straddling the bottom cutout edge.
# Inner portion overlaps board by CLIP_OVERLAP; outer portion holds screws.
bot_inner_y = -(HALF_GOWLAND - CLIP_OVERLAP)        # -67.5 (board side)
bot_outer_y = bot_inner_y - BOT_CLIP_WIDTH           # -77.5 (away from board)
bot_center_y = (bot_inner_y + bot_outer_y) / 2       # -72.5
cr = CLIP_CORNER_R

print("  [4/6] Bottom clip: %.0fmm bar, %.0fmm wide, %.1fmm thick (fixed, R%.0f corners)"
      % (CLIP_BAR_LENGTH, BOT_CLIP_WIDTH, CLIP_THICK, cr))

# Flat bar with rounded corners — no bent tabs (fixed clip)
hw = CLIP_BAR_LENGTH / 2
hh = BOT_CLIP_WIDTH / 2
bottom_clip = (
    cq.Workplane("XY")
    .workplane(offset=FRONT_Z_TOP)
    .center(0, bot_center_y)
    .rect(CLIP_BAR_LENGTH, BOT_CLIP_WIDTH)
    .extrude(CLIP_THICK)
    .edges("|Z").fillet(cr)
)

# Two clearance holes for mounting screws
for (x, y) in BOTTOM_CLIP_SCREW_POSITIONS:
    hole = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_TOP - 1)
        .center(x, y)
        .circle(M3_CLEARANCE / 2)
        .extrude(CLIP_THICK + 2)
    )
    bottom_clip = bottom_clip.cut(hole)


# ================================================================
# PART 5: SLIDING TOP CLIP (dog-bone profile, Crown Graphic style)
# ================================================================

# Outer edge (away from board, +Y) is STRAIGHT.
# Inner edge (board side, lower Y) has dog-bone profile:
#   wide at ends = more overlap (board grip at screw locations)
#   narrow in middle = less overlap (connecting bar / nameplate area)
# Single 45° tab at -X end (push direction matches 135° cam slots).
# All body corners radiused except where tab attaches (top-left).
import math

top_outer_y = HALF_GOWLAND - CLIP_OVERLAP + TOP_CLIP_WIDE  # 81.5 (straight)
top_inner_wide = top_outer_y - TOP_CLIP_WIDE                # 67.5 (ends)
top_inner_narrow = top_outer_y - TOP_CLIP_NARROW            # 73.5 (middle)
hb = CLIP_BAR_LENGTH / 2                                    # 45.0
ti = TOP_CLIP_TAPER_INNER                                   # 15.0
to_ = TOP_CLIP_TAPER_OUTER                                  # 20.0

print("  [5/6] Top clip: %.0fmm dog-bone bar + 45° rectangular tab (%.0fmm), "
      "%.0f/%.0fmm wide, %.1fmm thick"
      % (CLIP_BAR_LENGTH, TAB_HEIGHT, TOP_CLIP_NARROW, TOP_CLIP_WIDE, CLIP_THICK))
print("         135° cam slots, gravity return, R%.0f corners" % cr)

# Bend line endpoints for 45° triangular tab at upper-left corner.
# The bend line runs diagonally from A (on outer edge) to B (on left edge).
# The triangle A-C-B (C = original corner) bends 90° up from the clip face.
tab_ax = -hb + TAB_BEND_RUN                # A: X on outer edge
tab_by = top_outer_y - TAB_BEND_RUN        # B: Y on left edge

# Dog-bone profile with 45° chamfer at upper-left (tab material removed).
top_clip = (
    cq.Workplane("XY")
    .workplane(offset=FRONT_Z_TOP)
    .moveTo(-hb, top_inner_wide)
    .lineTo(-to_, top_inner_wide)
    .lineTo(-ti, top_inner_narrow)
    .lineTo( ti, top_inner_narrow)
    .lineTo( to_, top_inner_wide)
    .lineTo( hb, top_inner_wide)
    .lineTo( hb, top_outer_y)
    .lineTo(tab_ax, top_outer_y)          # A: bend line start on outer edge
    .lineTo(-hb, tab_by)                  # B: bend line end on left edge
    .close()                              # left edge: B → start
    .extrude(CLIP_THICK)
)

# Fillet body corners (before slot cutting and tab fusion).
# All 7 body corners get R2; bend endpoints A and B stay sharp.
_z_mid_clip = FRONT_Z_TOP + CLIP_THICK / 2
_body_fillet_pts = [
    (-hb, top_inner_wide),               # lower-left body
    (-to_, top_inner_wide),              # left taper, bottom
    (-ti, top_inner_narrow),             # left taper, narrow start
    ( ti, top_inner_narrow),             # right taper, narrow end
    ( to_, top_inner_wide),              # right taper, bottom
    ( hb, top_inner_wide),               # lower-right body
    ( hb, top_outer_y),                  # upper-right body
]
for fx, fy in _body_fillet_pts:
    top_clip = (
        top_clip.edges("|Z")
        .edges(cq.selectors.NearestToPointSelector((fx, fy, _z_mid_clip)))
        .fillet(cr)
    )

# 135° cam slots (push -X to open/retract from board, gravity closes)
for (x, y) in TOP_CLIP_SCREW_POSITIONS:
    slot = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_TOP - 1)
        .center(x, y)
        .slot2D(SLOT_LENGTH, SLOT_WIDTH, angle=SLOT_ANGLE)
        .extrude(CLIP_THICK + 2)
    )
    top_clip = top_clip.cut(slot)

# Single 45° rectangular tab at upper-left (Crown Graphic style).
# Rectangular tab extends perpendicular to the A-B bend line by TAB_HEIGHT.
# When bent 90° along A-B, creates a rectangular finger grip.
# Pushing the tab drives the clip along the 135° cam slot direction.
s2 = math.sqrt(2)
z_top = FRONT_Z_TOP + CLIP_THICK
ab_len = TAB_BEND_RUN * s2               # bend line length ≈ 17.0mm

# Build tab as rectangle on a vertical workplane containing bend line A-B.
# Workplane: xDir along A→B, yDir = (0,0,1) up, normal outward from body.
tab = (
    cq.Workplane(cq.Plane(
        origin=(tab_ax, top_outer_y, z_top),
        normal=(-1/s2, 1/s2, 0),
        xDir=(-1/s2, -1/s2, 0)
    ))
    .moveTo(0, 0)
    .lineTo(ab_len, 0)
    .lineTo(ab_len, TAB_HEIGHT)
    .lineTo(0, TAB_HEIGHT)
    .close()
    .extrude(CLIP_THICK)
)
top_clip_solid = top_clip.val().fuse(tab.val())
top_clip = cq.Workplane("XY").newObject([top_clip_solid])

# Fillet tab outer corners (A' and B') in 3D.
# These are the short edges at the top of the tab, running along the
# tab's thickness direction (normal = (-1/√2, 1/√2, 0)).
# Edge midpoints: corner position + half thickness along normal.
_half_norm = CLIP_THICK / (2 * s2)
_tab_corner_pts = [
    (tab_ax - _half_norm, top_outer_y + _half_norm, z_top + TAB_HEIGHT),   # A'
    (-hb - _half_norm, tab_by + _half_norm, z_top + TAB_HEIGHT),           # B'
]
for pt in _tab_corner_pts:
    top_clip = (
        top_clip.edges()
        .edges(cq.selectors.NearestToPointSelector(pt))
        .fillet(cr)
    )


# ================================================================
# PART 6: ASSEMBLY (color-coded visualization)
# ================================================================

print("  [6/6] Assembly: combining all parts (color-coded)")

assembly = cq.Assembly(name="fatif_adapter")
assembly.add(rear_sheet,   name="rear_sheet",
             color=cq.Color(0.12, 0.12, 0.14))   # near-black (anodized)
assembly.add(middle_sheet, name="middle_sheet",
             color=cq.Color(0.78, 0.78, 0.82))    # silver (bare aluminum)
assembly.add(front_sheet,  name="front_sheet",
             color=cq.Color(0.40, 0.40, 0.40))    # dark gray (powder coat)
assembly.add(bottom_clip,  name="bottom_clip",
             color=cq.Color(0.72, 0.45, 0.20))    # copper (for visibility)
assembly.add(top_clip,     name="top_clip",
             color=cq.Color(0.72, 0.45, 0.20))    # copper (for visibility)


# ================================================================
# EXPORT
# ================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))

individual_parts = {
    "fatif_front_sheet": front_sheet,
    "fatif_middle_sheet": middle_sheet,
    "fatif_rear_sheet": rear_sheet,
    "fatif_bottom_clip": bottom_clip,
    "fatif_top_clip": top_clip,
}

print("\nExporting...")
for name, part in individual_parts.items():
    # STEP file (3D, with bends for clips)
    step_path = os.path.join(script_dir, f"{name}.step")
    cq.exporters.export(part, step_path)
    print(f"  STEP: {step_path}")

    # DXF file (2D profile for laser cutting)
    dxf_path = os.path.join(script_dir, f"{name}.dxf")

    if name in ("fatif_front_sheet", "fatif_middle_sheet", "fatif_rear_sheet"):
        # Sheet parts: section at Z midpoint
        if name == "fatif_front_sheet":
            section_z = FRONT_Z_BOT + FRONT_THICK / 2
        elif name == "fatif_middle_sheet":
            section_z = MIDDLE_Z_BOT + MIDDLE_THICK / 2
        else:
            section_z = REAR_THICK / 2
        section = (
            cq.Workplane("XY")
            .workplane(offset=section_z)
            .newObject([part.val()])
        )
        cross = section.section()
        cq.exporters.export(cross, dxf_path)
    elif name == "fatif_bottom_clip":
        # Bottom clip flat pattern: rounded rectangle + round holes (no tabs)
        flat = (
            cq.Workplane("XY")
            .rect(CLIP_BAR_LENGTH, BOT_CLIP_WIDTH)
            .extrude(CLIP_THICK)
            .edges("|Z").fillet(cr)
        )
        # Screw holes at clip-relative positions (clip centered at Y=0)
        for (sx, sy) in BOTTOM_CLIP_SCREW_POSITIONS:
            rel_y = sy - bot_center_y
            feature = (
                cq.Workplane("XY").workplane(offset=-1)
                .center(sx, rel_y)
                .circle(M3_CLEARANCE / 2)
                .extrude(CLIP_THICK + 2)
            )
            flat = flat.cut(feature)
        section = (
            cq.Workplane("XY").workplane(offset=CLIP_THICK / 2)
            .newObject([flat.val()])
        )
        cross = section.section()
        cq.exporters.export(cross, dxf_path)

    else:  # fatif_top_clip
        # Top clip flat pattern: dog-bone body + rectangular tab at upper-left.
        # Tab extends perpendicular to 45° bend line A-B by TAB_HEIGHT.
        # Local coords: inner edge at Y=0, outer at Y=TOP_CLIP_WIDE.
        # Bend line: A_local=(-hb+TAB_BEND_RUN, TOP_CLIP_WIDE) to
        #            B_local=(-hb, TOP_CLIP_WIDE-TAB_BEND_RUN)
        dog_bone_inset = TOP_CLIP_WIDE - TOP_CLIP_NARROW  # 6
        c45 = math.cos(math.pi / 4)
        s45 = math.sin(math.pi / 4)

        # Tab corner positions (perpendicular to bend line, outward)
        # Outward direction from A-B: (-1/√2, 1/√2)
        perp_x = -1 / math.sqrt(2)
        perp_y = 1 / math.sqrt(2)
        # A on outer edge, B on left edge (local coords)
        a_lx = -hb + TAB_BEND_RUN               # -33
        a_ly = TOP_CLIP_WIDE                      # 14
        b_lx = -hb                                # -45
        b_ly = TOP_CLIP_WIDE - TAB_BEND_RUN      # 2
        # Tab outer corners: A' and B' at TAB_HEIGHT outward from A and B
        ap_x = a_lx + TAB_HEIGHT * perp_x        # A'
        ap_y = a_ly + TAB_HEIGHT * perp_y
        bp_x = b_lx + TAB_HEIGHT * perp_x        # B'
        bp_y = b_ly + TAB_HEIGHT * perp_y

        # Build sharp outline, then selectively fillet corners
        flat = (
            cq.Workplane("XY")
            .moveTo(b_lx, 0)
            # Bottom edge through dog-bone
            .lineTo(-to_, 0)
            .lineTo(-ti, dog_bone_inset)
            .lineTo( ti, dog_bone_inset)
            .lineTo( to_, 0)
            .lineTo( hb, 0)
            .lineTo( hb, TOP_CLIP_WIDE)
            # Top edge to bend line start (A)
            .lineTo(a_lx, a_ly)
            # Tab: A → A' → B' → B
            .lineTo(ap_x, ap_y)
            .lineTo(bp_x, bp_y)
            .lineTo(b_lx, b_ly)
            # Left edge: B → start
            .close()
            .extrude(CLIP_THICK)
        )
        # Fillet all corners: 3 body + 4 taper + 2 tab outer = 9 total.
        # Leaves bend endpoints A and B sharp (tab attachment).
        fillet_pts = [
            (b_lx, 0),                          # lower-left body
            (-to_, 0),                           # left taper, bottom
            (-ti, dog_bone_inset),               # left taper, narrow start
            ( ti, dog_bone_inset),               # right taper, narrow end
            ( to_, 0),                           # right taper, bottom
            (hb, 0),                             # lower-right body
            (hb, TOP_CLIP_WIDE),                 # upper-right body
            (ap_x, ap_y),                        # tab corner A'
            (bp_x, bp_y),                        # tab corner B'
        ]
        z_mid = CLIP_THICK / 2
        for fx, fy in fillet_pts:
            flat = (
                flat.edges("|Z")
                .edges(cq.selectors.NearestToPointSelector((fx, fy, z_mid)))
                .fillet(cr)
            )
        # Cam slots at clip-relative positions (screw Y relative to inner edge)
        for (sx, sy) in TOP_CLIP_SCREW_POSITIONS:
            rel_y = sy - top_inner_wide  # screw Y relative to wide inner edge
            feature = (
                cq.Workplane("XY").workplane(offset=-1)
                .center(sx, rel_y)
                .slot2D(SLOT_LENGTH, SLOT_WIDTH, angle=SLOT_ANGLE)
                .extrude(CLIP_THICK + 2)
            )
            flat = flat.cut(feature)
        section = (
            cq.Workplane("XY").workplane(offset=CLIP_THICK / 2)
            .newObject([flat.val()])
        )
        cross = section.section()
        cq.exporters.export(cross, dxf_path)
        # Note: bend line from A to B is internal (not in DXF outline)
        bend_a_local = (-hb + TAB_BEND_RUN, TOP_CLIP_WIDE)
        bend_b_local = (-hb, TOP_CLIP_WIDE - TAB_BEND_RUN)
        print(f"         Bend line (flat pattern): "
              f"({bend_a_local[0]:.0f}, {bend_a_local[1]:.0f}) to "
              f"({bend_b_local[0]:.0f}, {bend_b_local[1]:.0f})")

    print(f"  DXF:  {dxf_path}")

# Assembly STEP (color-coded)
assy_path = os.path.join(script_dir, "fatif_assembly.step")
assembly.save(assy_path)
print(f"  STEP: {assy_path}")

# ================================================================
# BOUNDING BOX CHECKS
# ================================================================

print("\n" + "=" * 60)
print("Bounding box verification:")
for name, part in individual_parts.items():
    bb = part.val().BoundingBox()
    print(f"  {name}:")
    print(f"    X: {bb.xmin:.2f} to {bb.xmax:.2f}  ({bb.xmax - bb.xmin:.2f}mm)")
    print(f"    Y: {bb.ymin:.2f} to {bb.ymax:.2f}  ({bb.ymax - bb.ymin:.2f}mm)")
    print(f"    Z: {bb.zmin:.2f} to {bb.zmax:.2f}  ({bb.zmax - bb.zmin:.2f}mm)")

# ================================================================
# DESIGN SUMMARY
# ================================================================

print("\n" + "=" * 60)
print("Design summary — Three-Piece Laminated Adapter:")
print(f"  Front sheet:    {BOARD_SIZE}x{BOARD_SIZE}mm, R{BOARD_CORNER_R}, "
      f"{FRONT_THICK}mm (.063\" 6061 powder coated)")
print(f"    Cutout:       {GOWLAND_SIZE}x{GOWLAND_SIZE}mm, R{GOWLAND_CORNER_R}")
print(f"  Middle sheet:   {BOARD_SIZE}x{BOARD_SIZE}mm, R{BOARD_CORNER_R}, "
      f"{MIDDLE_THICK}mm (.025\" 2024-T3 bare)")
print(f"    Bore:         dia {BORE_DIA}mm")
print(f"  Rear sheet:     {REAR_SIZE}x{REAR_SIZE}mm, R{REAR_CORNER_R}, "
      f"{REAR_THICK}mm (.100\" 6061 black anodized)")
print(f"    Bore:         dia {BORE_DIA}mm")
print(f"  Laminated:      {FRONT_THICK}+{MIDDLE_THICK}+{REAR_THICK} = "
      f"{TOTAL_THICKNESS:.2f}mm total")
print(f"  Lip:            {LIP_THICK:.2f}mm (front+middle overhang "
      f"{STEP_WIDTH}mm beyond rear)  [limit: 2.50mm]")
print(f"  Assembly screws: 2x M3 flat head at (±{ASSY_SCREW_R}, 0)mm")
print(f"  Bottom clip:    {CLIP_BAR_LENGTH}mm bar, "
      f"{BOT_CLIP_WIDTH}mm wide, fixed, {CLIP_OVERLAP}mm overlap")
print(f"  Top clip:       {CLIP_BAR_LENGTH}mm dog-bone bar + 45° rectangular tab "
      f"({TAB_HEIGHT}mm tall, {TAB_BEND_RUN}mm bend run), "
      f"{TOP_CLIP_NARROW}/{TOP_CLIP_WIDE}mm wide, R{CLIP_CORNER_R} corners")
print(f"    Cam action:   {SLOT_ANGLE:.0f}° slots, {SLOT_LENGTH - SLOT_WIDTH:.1f}mm travel, "
      f"gravity return (push -X to open)")
print(f"  Clip screws:    2+2 M3 pan head at X spacing {CLIP_SCREW_X_SPACING}mm")
print(f"    Bottom Y:     ±{BOT_CLIP_SCREW_Y}mm, Top Y: ±{TOP_CLIP_SCREW_Y}mm")
print(f"  Total screws:   6 (2 assembly + 4 clip, all laminate sheets)")
print(f"  Materials:      6061-T6 (front/rear), 2024-T3 (middle), "
      f"304 SS (clips)")
print(f"  Finishes:       Powder coat (front), bare (middle), "
      f"black anodize (rear), bare (clips)")
print("=" * 60)
print("\nFiles ready for SendCutSend upload (STEP for quoting, DXF for cutting)")
print("Note: Clip DXFs show flat patterns (pre-bend).")
print(f"  Top clip: bend 90° up along 45° diagonal at upper-left corner")
print(f"    Bend line (flat coords): (-{int(hb - TAB_BEND_RUN)}, {int(TOP_CLIP_WIDE)}) "
      f"to (-{int(hb)}, {int(TOP_CLIP_WIDE - TAB_BEND_RUN)})")
