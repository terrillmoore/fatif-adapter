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
  Fixed bottom clip: rectangular flat bar, 2 screws, bent tabs at both ends
  Sliding top clip: dog-bone profile (wider at slot ends, narrower in
    middle), 45° cam slots (sliding retracts clip from board), gravity
    return (no springs), bent tabs at both ends for finger grip
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

# --- Clips (Cambo / Crown Graphic style) ---
CLIP_BAR_LENGTH = 90.0      # flat bar length on adapter face (both clips)
CLIP_THICK = 2.0            # sheet metal thickness (both clips)
CLIP_OVERLAP = 3.5          # overlap onto board edge (both clips)
TAB_HEIGHT = 8.0            # bent tab height at both ends (both clips)

# Bottom clip: simple rectangular bar
BOT_CLIP_WIDTH = 10.0       # uniform width

# Top clip: dog-bone profile (Crown Graphic style)
# Wider at screw/slot ends, narrower in middle (nameplate area).
# Inner edge (board side) is straight for uniform overlap.
# Outer edge has the dog-bone taper.
TOP_CLIP_WIDE = 14.0        # width at ends (accommodates 45° cam slots)
TOP_CLIP_NARROW = 8.0       # width in middle
TOP_CLIP_TAPER_INNER = 15.0 # X from center where taper begins
TOP_CLIP_TAPER_OUTER = 20.0 # X from center where full width begins

# Top clip cam slots (135° = cam action: push tab +X to close,
# push tab -X to open/retract, gravity return to closed)
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

# Top clip screws: 2 positions at +Y
TOP_CLIP_SCREW_POSITIONS = [
    (-CLIP_SCREW_X_SPACING / 2, TOP_CLIP_SCREW_Y),
    ( CLIP_SCREW_X_SPACING / 2, TOP_CLIP_SCREW_Y),
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
bot_inner_y = -(HALF_GOWLAND - CLIP_OVERLAP)        # -66.0 (board side)
bot_outer_y = bot_inner_y - BOT_CLIP_WIDTH           # -76.0 (away from board)
bot_center_y = (bot_inner_y + bot_outer_y) / 2       # -71.0

print("  [4/6] Bottom clip: %.0fmm bar, %.0fmm wide, %.1fmm thick (fixed, no tabs)"
      % (CLIP_BAR_LENGTH, BOT_CLIP_WIDTH, CLIP_THICK))

# Simple flat bar — no bent tabs (fixed clip, nothing to grip)
bottom_clip = (
    cq.Workplane("XY")
    .workplane(offset=FRONT_Z_TOP)
    .center(0, bot_center_y)
    .rect(CLIP_BAR_LENGTH, BOT_CLIP_WIDTH)
    .extrude(CLIP_THICK)
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
# Cam action: 135° slots mean push -X to open, gravity returns to closed.
top_outer_y = HALF_GOWLAND - CLIP_OVERLAP + TOP_CLIP_WIDE  # 80.0 (straight)
top_inner_wide = top_outer_y - TOP_CLIP_WIDE                # 66.0 (ends)
top_inner_narrow = top_outer_y - TOP_CLIP_NARROW            # 72.0 (middle)
hb = CLIP_BAR_LENGTH / 2                                    # 45.0
ti = TOP_CLIP_TAPER_INNER                                   # 15.0
to_ = TOP_CLIP_TAPER_OUTER                                  # 20.0

print("  [5/6] Top clip: %.0fmm dog-bone bar + 2x%.0fmm tabs, "
      "%.0f/%.0fmm wide, %.1fmm thick"
      % (CLIP_BAR_LENGTH, TAB_HEIGHT, TOP_CLIP_NARROW, TOP_CLIP_WIDE, CLIP_THICK))
print("         135° cam slots, gravity return (no springs)")

# Dog-bone profile: straight outer edge (+Y), profiled inner edge
top_clip = (
    cq.Workplane("XY")
    .workplane(offset=FRONT_Z_TOP)
    .moveTo(-hb, top_inner_wide)          # bottom-left (wide, 66)
    .lineTo(-to_, top_inner_wide)         # taper start
    .lineTo(-ti, top_inner_narrow)        # taper to narrow (72)
    .lineTo( ti, top_inner_narrow)        # narrow middle
    .lineTo( to_, top_inner_wide)         # taper back to wide (66)
    .lineTo( hb, top_inner_wide)          # bottom-right (wide, 66)
    .lineTo( hb, top_outer_y)             # top-right (straight, 80)
    .lineTo(-hb, top_outer_y)             # top-left (straight, 80)
    .close()
    .extrude(CLIP_THICK)
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

# Bent tabs at both X ends (match wide end width for finger grip)
top_wide_center_y = (top_inner_wide + top_outer_y) / 2   # 73.0
for x_sign in [-1, 1]:
    tab_x = x_sign * (hb + CLIP_THICK / 2)
    tab = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_TOP)
        .center(tab_x, top_wide_center_y)
        .rect(CLIP_THICK, TOP_CLIP_WIDE)
        .extrude(TAB_HEIGHT + CLIP_THICK)
    )
    top_clip_solid = top_clip.val().fuse(tab.val())
    top_clip = cq.Workplane("XY").newObject([top_clip_solid])


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
        # Bottom clip flat pattern: simple rectangle + round holes (no tabs)
        flat = (
            cq.Workplane("XY")
            .rect(CLIP_BAR_LENGTH, BOT_CLIP_WIDTH)
            .extrude(CLIP_THICK)
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
        # Top clip flat pattern: dog-bone + tab extensions + cam slots
        # Local coords: inner edge (board side) at Y=0, outer at Y=TOP_CLIP_WIDE.
        # Inner edge is profiled (wide at ends, narrow in middle).
        # Tab material at each end matches the wide end width.
        flat_half = CLIP_BAR_LENGTH / 2 + TAB_HEIGHT     # 53
        dog_bone_inset = TOP_CLIP_WIDE - TOP_CLIP_NARROW # 6
        flat = (
            cq.Workplane("XY")
            .moveTo(-flat_half, 0)                 # left tab, inner (wide)
            .lineTo(-to_, 0)                       # taper start
            .lineTo(-ti, dog_bone_inset)           # taper to narrow
            .lineTo( ti, dog_bone_inset)           # narrow middle
            .lineTo( to_, 0)                       # taper back to wide
            .lineTo( flat_half, 0)                 # right tab, inner (wide)
            .lineTo( flat_half, TOP_CLIP_WIDE)     # right tab, outer
            .lineTo(-flat_half, TOP_CLIP_WIDE)     # left tab, outer
            .close()
            .extrude(CLIP_THICK)
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
print(f"  Top clip:       {CLIP_BAR_LENGTH}mm dog-bone bar + 2x{TAB_HEIGHT}mm tabs, "
      f"{TOP_CLIP_NARROW}/{TOP_CLIP_WIDE}mm wide")
print(f"    Cam action:   {SLOT_ANGLE:.0f}° slots, {SLOT_LENGTH - SLOT_WIDTH:.1f}mm travel, "
      f"gravity return (push -X to open)")
print(f"  Clip screws:    2+2 M3 pan head at X spacing {CLIP_SCREW_X_SPACING}mm")
print(f"    Bottom Y:     ±{BOT_CLIP_SCREW_Y}mm, Top Y: ±{TOP_CLIP_SCREW_Y}mm")
print(f"  Total screws:   6 (2 assembly + 4 clip, all laminate sheets)")
print(f"  Materials:      6061-T6 (front/rear), 2024-T3 (middle)")
print(f"  Finishes:       Powder coat (front), bare (middle), "
      f"black anodize (rear)")
print("=" * 60)
print("\nFiles ready for SendCutSend upload (STEP for quoting, DXF for cutting)")
print("Note: Clip DXFs show flat patterns (pre-bend). Bend tabs up 90° at each end.")
