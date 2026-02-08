#!/usr/bin/env python3
"""
Fatif DS 20x25 Adapter Lensboard — Three-Piece Laminated Design

Generates STEP and DXF files for laser-cut fabrication (SendCutSend).

Design: Terry Moore / Claude
Material: 6061-T6 aluminum, laser cut + powder coat
Assembly: Three sheets laminated with M3 flat head screws

Coordinate convention:
  Z axis: z=0 is back face (camera side)
  Rear sheet:   z=0.0 to z=3.0  (3.0mm thick, camera side)
  Middle sheet: z=3.0 to z=3.5  (0.5mm thick, light seal)
  Front sheet:  z=3.5 to z=5.5  (2.0mm thick, lens side)
  XY: origin at center of board
  +Y = top, -Y = bottom, +X = right, -X = left (viewed from lens side)

Three-piece laminated approach:
  Front sheet (2.0mm):  Full Fatif profile with Gowland cutout
  Middle sheet (0.5mm): Full Fatif profile with bore only — seals light
    leaks at corners where rear sheet R42.5 corners don't cover
    the front sheet's 139mm square cutout
  Rear sheet (3.0mm):   Smaller "baffle" profile with bore
  Front+middle overhang rear by 7.5mm all around, creating the
    2.5mm-thick lip that seats into the Fatif standard clips.
  Total thickness: 2.0 + 0.5 + 3.0 = 5.5mm (matches original)

Board retention — Cambo-style clips:
  Fixed bottom clip: flat bar mounted below cutout, overlaps board ~3mm
  Sliding top clip: spring-loaded flat bar with elongated slots,
    pulled up via finger tab to insert/remove board
"""

import cadquery as cq
import math
import os

# ================================================================
# PARAMETERS (all dimensions in mm)
# ================================================================

# --- Outer profile (matches Fatif original lensboard) ---
BOARD_SIZE = 170.0          # square dimension
BOARD_CORNER_R = 50.0       # corner radius
TOTAL_THICKNESS = 5.5       # total laminated thickness

# --- Sheet thicknesses (TBD after measuring — adjust here) ---
FRONT_THICK = 2.0           # front sheet thickness
MIDDLE_THICK = 0.5          # middle sheet thickness (light seal)
REAR_THICK = 3.0            # rear sheet thickness

# --- Back perimeter step (created by size difference between sheets) ---
STEP_WIDTH = 7.5            # overhang of front+middle beyond rear
REAR_SIZE = BOARD_SIZE - 2 * STEP_WIDTH        # = 155.0
REAR_CORNER_R = BOARD_CORNER_R - STEP_WIDTH    # = 42.5

# --- Front cutout (Gowland board drops through this) ---
GOWLAND_SIZE = 139.0        # 138.5mm nominal + 0.5mm clearance
GOWLAND_CORNER_R = 3.4      # Gowland board corner radius

# --- Central through bore (rear + middle sheets) ---
BORE_DIA = 110.0            # clears Ilex #5 flange with margin

# --- Assembly screws (M3 flat head, countersunk into front sheet) ---
M3_CLEARANCE = 3.4          # M3 clearance hole diameter
M3_TAP = 2.5                # M3 tap drill diameter
M3_CSK_DIA = 6.5            # M3 flat head countersink diameter
M3_CSK_DEPTH = 1.5          # countersink depth (< FRONT_THICK)

# --- Screw placement ---
# Assembly screws at 4 diagonal positions in the overlap zone
# Overlap band: ~69.5mm to ~77.5mm from center
ASSY_SCREW_R = 73.5         # radial distance from center for assembly screws

# Clip screws at top and bottom center
CLIP_SCREW_X_SPACING = 50.0 # distance between clip screw pair (center to center)
CLIP_SCREW_Y_OFFSET = 73.5  # Y distance from center for clip screws

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
HALF_BOARD = BOARD_SIZE / 2          # = 85.0
HALF_GOWLAND = GOWLAND_SIZE / 2     # = 69.5
HALF_REAR = REAR_SIZE / 2           # = 77.5

REAR_Z_BOT = 0.0                                # rear sheet bottom
REAR_Z_TOP = REAR_THICK                         # = 3.0
MIDDLE_Z_BOT = REAR_THICK                       # = 3.0
MIDDLE_Z_TOP = REAR_THICK + MIDDLE_THICK        # = 3.5
FRONT_Z_BOT = REAR_THICK + MIDDLE_THICK         # = 3.5
FRONT_Z_TOP = TOTAL_THICKNESS                    # = 5.5

# Lip thickness = front + middle = 2.0 + 0.5 = 2.5mm (matches original)
LIP_THICK = FRONT_THICK + MIDDLE_THICK


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
# Left/right at (±R, 0), top/bottom at (0, ±R).
# Top/bottom are 25mm from nearest clip screw — no conflict.
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
print("  [1/6] Front sheet: %.0fmm sq, R%.0f, %.1fmm thick (z=%.1f to %.1f)"
      % (BOARD_SIZE, BOARD_CORNER_R, FRONT_THICK, FRONT_Z_BOT, FRONT_Z_TOP))

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

print("  [2/6] Middle sheet: %.0fmm sq, R%.0f, %.1fmm thick (z=%.1f to %.1f)"
      % (BOARD_SIZE, BOARD_CORNER_R, MIDDLE_THICK, MIDDLE_Z_BOT, MIDDLE_Z_TOP))

# Same outer profile as front sheet — full Fatif size
middle_sheet = (
    rounded_rect(cq.Workplane("XY").workplane(offset=MIDDLE_Z_BOT),
                 BOARD_SIZE, BOARD_CORNER_R)
    .extrude(MIDDLE_THICK)
)

# Central bore (same as rear sheet)
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

print("  [3/6] Rear sheet: %.0fmm sq, R%.1f, %.1fmm thick (z=%.1f to %.1f)"
      % (REAR_SIZE, REAR_CORNER_R, REAR_THICK, REAR_Z_BOT, REAR_Z_TOP))

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
    print(f"    X: {bb.xmin:.1f} to {bb.xmax:.1f}  ({bb.xmax - bb.xmin:.1f}mm)")
    print(f"    Y: {bb.ymin:.1f} to {bb.ymax:.1f}  ({bb.ymax - bb.ymin:.1f}mm)")
    print(f"    Z: {bb.zmin:.1f} to {bb.zmax:.1f}  ({bb.zmax - bb.zmin:.1f}mm)")

# ================================================================
# DESIGN SUMMARY
# ================================================================

print("\n" + "=" * 60)
print("Design summary — Three-Piece Laminated Adapter:")
print(f"  Front sheet:    {BOARD_SIZE}x{BOARD_SIZE}mm, R{BOARD_CORNER_R}, "
      f"{FRONT_THICK}mm thick")
print(f"    Cutout:       {GOWLAND_SIZE}x{GOWLAND_SIZE}mm, R{GOWLAND_CORNER_R}")
print(f"  Middle sheet:   {BOARD_SIZE}x{BOARD_SIZE}mm, R{BOARD_CORNER_R}, "
      f"{MIDDLE_THICK}mm thick (light seal)")
print(f"    Bore:         dia {BORE_DIA}mm")
print(f"  Rear sheet:     {REAR_SIZE}x{REAR_SIZE}mm, R{REAR_CORNER_R}, "
      f"{REAR_THICK}mm thick")
print(f"    Bore:         dia {BORE_DIA}mm")
print(f"  Laminated:      {FRONT_THICK}+{MIDDLE_THICK}+{REAR_THICK} = "
      f"{TOTAL_THICKNESS}mm total")
print(f"  Lip:            {LIP_THICK}mm thick (front+middle overhang "
      f"{STEP_WIDTH}mm beyond rear)")
print(f"  Assembly screws: 4x M3 flat head at R={ASSY_SCREW_R}mm (cardinal axes)")
print(f"  Bottom clip:    {CLIP_LENGTH}x{CLIP_WIDTH}x{CLIP_THICK}mm, "
      f"fixed, {CLIP_OVERLAP}mm overlap")
print(f"  Top clip:       {CLIP_LENGTH}x{CLIP_WIDTH}x{CLIP_THICK}mm, "
      f"spring-loaded, slots for {SLOT_LENGTH - SLOT_WIDTH:.1f}mm travel")
print(f"  Clip screws:    2+2 M3 at X spacing {CLIP_SCREW_X_SPACING}mm, "
      f"Y offset {CLIP_SCREW_Y_OFFSET}mm")
print(f"  Material:       6061-T6 aluminum")
print(f"  Fabrication:    Laser cut + powder coat (SendCutSend)")
print("=" * 60)
print("\nFiles ready for SendCutSend upload (STEP for quoting, DXF for cutting)")
