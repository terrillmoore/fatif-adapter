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

Board retention — Cambo-style clips:
  Fixed bottom clip: flat bar mounted below cutout, overlaps board ~3mm
  Sliding top clip: spring-loaded flat bar with elongated slots,
    pulled up via finger tab to insert/remove board
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

# Clip screws at top and bottom center
CLIP_SCREW_X_SPACING = 50.0 # distance between clip screw pair (center to center)
CLIP_SCREW_Y_OFFSET = 74.75 # Y distance from center for clip screws

# --- Clips ---
CLIP_LENGTH = 139.0         # same as cutout width
CLIP_WIDTH = 5.0            # bar width (Y direction)
CLIP_THICK = 2.0            # bar thickness
CLIP_OVERLAP = 3.0          # how far clip overlaps board edge

# Top clip slots
SLOT_LENGTH = 7.0           # elongated slot length (allows ~5mm travel)
SLOT_WIDTH = 3.4            # M3 clearance width

# Top clip finger tab
TAB_LENGTH = 15.0           # tab extends beyond clip end
TAB_HEIGHT = 8.0            # bent tab height (90° upward)

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

# Assembly screws: 4 positions on cardinal axes (not diagonals —
# diagonals fall inside the front sheet's 139mm cutout).
ASSY_SCREW_POSITIONS = [
    ( ASSY_SCREW_R,  0),   # right
    (-ASSY_SCREW_R,  0),   # left
    ( 0,  ASSY_SCREW_R),   # top
    ( 0, -ASSY_SCREW_R),   # bottom
]

# Bottom clip screws: 2 positions at -Y
BOTTOM_CLIP_SCREW_POSITIONS = [
    (-CLIP_SCREW_X_SPACING / 2, -CLIP_SCREW_Y_OFFSET),
    ( CLIP_SCREW_X_SPACING / 2, -CLIP_SCREW_Y_OFFSET),
]

# Top clip screws: 2 positions at +Y
TOP_CLIP_SCREW_POSITIONS = [
    (-CLIP_SCREW_X_SPACING / 2, CLIP_SCREW_Y_OFFSET),
    ( CLIP_SCREW_X_SPACING / 2, CLIP_SCREW_Y_OFFSET),
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

# Clearance holes + countersinks for all screws
for (x, y) in ALL_SCREW_POSITIONS:
    hole = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_BOT - 1)
        .center(x, y)
        .circle(M3_CLEARANCE / 2)
        .extrude(FRONT_THICK + 2)
    )
    front_sheet = front_sheet.cut(hole)

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

print("  [4/6] Bottom clip: %.0fmm x %.0fmm x %.1fmm"
      % (CLIP_LENGTH, CLIP_WIDTH, CLIP_THICK))

# Clip sits on front face at bottom of cutout
clip_y_center = -(HALF_GOWLAND + CLIP_WIDTH / 2 - CLIP_OVERLAP)

bottom_clip = (
    cq.Workplane("XY")
    .workplane(offset=FRONT_Z_TOP)
    .center(0, clip_y_center)
    .rect(CLIP_LENGTH, CLIP_WIDTH)
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
# PART 5: SLIDING TOP CLIP
# ================================================================

print("  [5/6] Top clip: %.0fmm x %.0fmm x %.1fmm (with slots + tab)"
      % (CLIP_LENGTH + TAB_LENGTH, CLIP_WIDTH, CLIP_THICK))

# Clip sits on front face at top of cutout
clip_y_center_top = HALF_GOWLAND + CLIP_WIDTH / 2 - CLIP_OVERLAP

# Main bar (extended by tab length on +X side)
top_clip = (
    cq.Workplane("XY")
    .workplane(offset=FRONT_Z_TOP)
    .center(TAB_LENGTH / 2, clip_y_center_top)
    .rect(CLIP_LENGTH + TAB_LENGTH, CLIP_WIDTH)
    .extrude(CLIP_THICK)
)

# Elongated slots (Y-direction slots for vertical sliding)
for (x, y) in TOP_CLIP_SCREW_POSITIONS:
    slot = (
        cq.Workplane("XY")
        .workplane(offset=FRONT_Z_TOP - 1)
        .center(x, y)
        .slot2D(SLOT_LENGTH, SLOT_WIDTH, angle=90)
        .extrude(CLIP_THICK + 2)
    )
    top_clip = top_clip.cut(slot)

# Bent tab at +X end (90° upward for finger grip)
tab_x = CLIP_LENGTH / 2 + TAB_LENGTH / 2
tab_z_center = FRONT_Z_TOP + CLIP_THICK + TAB_HEIGHT / 2
tab = (
    cq.Workplane("XZ")
    .center(tab_x, tab_z_center)
    .rect(TAB_LENGTH, TAB_HEIGHT)
    .extrude(-CLIP_WIDTH)
)
tab = tab.translate((0, clip_y_center_top + CLIP_WIDTH / 2, 0))
top_clip_solid = top_clip.val().fuse(tab.val())
top_clip = cq.Workplane("XY").newObject([top_clip_solid])


# ================================================================
# PART 6: ASSEMBLY (visualization)
# ================================================================

print("  [6/6] Assembly: combining all parts for visualization")

assy_solid = front_sheet.val().fuse(middle_sheet.val())
assy_solid = assy_solid.fuse(rear_sheet.val())
assy_solid = assy_solid.fuse(bottom_clip.val())
assy_solid = assy_solid.fuse(top_clip.val())
assembly = cq.Workplane("XY").newObject([assy_solid])


# ================================================================
# EXPORT
# ================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))

parts = {
    "fatif_front_sheet": front_sheet,
    "fatif_middle_sheet": middle_sheet,
    "fatif_rear_sheet": rear_sheet,
    "fatif_bottom_clip": bottom_clip,
    "fatif_top_clip": top_clip,
    "fatif_assembly": assembly,
}

print("\nExporting...")
for name, part in parts.items():
    # STEP file
    step_path = os.path.join(script_dir, f"{name}.step")
    cq.exporters.export(part, step_path)
    print(f"  STEP: {step_path}")

    # DXF file (2D profile — top-down view for laser cutting)
    # Skip DXF for assembly (it's 3D visualization only)
    if name != "fatif_assembly":
        dxf_path = os.path.join(script_dir, f"{name}.dxf")
        if name == "fatif_front_sheet":
            section_z = FRONT_Z_BOT + FRONT_THICK / 2
        elif name == "fatif_middle_sheet":
            section_z = MIDDLE_Z_BOT + MIDDLE_THICK / 2
        elif name == "fatif_rear_sheet":
            section_z = REAR_THICK / 2
        elif name in ("fatif_bottom_clip", "fatif_top_clip"):
            section_z = FRONT_Z_TOP + CLIP_THICK / 2

        section = (
            cq.Workplane("XY")
            .workplane(offset=section_z)
            .newObject([part.val()])
        )
        cross = section.section()
        cq.exporters.export(cross, dxf_path)
        print(f"  DXF:  {dxf_path}")

# ================================================================
# BOUNDING BOX CHECKS
# ================================================================

print("\n" + "=" * 60)
print("Bounding box verification:")
for name, part in parts.items():
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
print(f"  Assembly screws: 4x M3 flat head at R={ASSY_SCREW_R}mm (cardinal axes)")
print(f"  Bottom clip:    {CLIP_LENGTH}x{CLIP_WIDTH}x{CLIP_THICK}mm, "
      f"fixed, {CLIP_OVERLAP}mm overlap")
print(f"  Top clip:       {CLIP_LENGTH}x{CLIP_WIDTH}x{CLIP_THICK}mm, "
      f"spring-loaded, slots for {SLOT_LENGTH - SLOT_WIDTH:.1f}mm travel")
print(f"  Clip screws:    2+2 M3 at X spacing {CLIP_SCREW_X_SPACING}mm, "
      f"Y offset {CLIP_SCREW_Y_OFFSET}mm")
print(f"  Materials:      6061-T6 (front/rear), 2024-T3 (middle)")
print(f"  Finishes:       Powder coat (front), bare (middle), "
      f"black anodize (rear)")
print("=" * 60)
print("\nFiles ready for SendCutSend upload (STEP for quoting, DXF for cutting)")
