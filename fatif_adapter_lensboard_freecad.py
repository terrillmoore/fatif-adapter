#!/usr/bin/env python3
"""
Fatif DS 20x25 Adapter Lensboard - FreeCAD STEP Generator

Run this script in FreeCAD's Python console or via command line:
    freecad -c fatif_adapter_lensboard_freecad.py

It will generate: fatif_adapter_lensboard.step

Design: Terry Moore / Claude
Date: 2026-02-07
Material: 6061-T6 aluminum, machine from 6mm stock, face to 5.5mm
"""

import sys
import os
import math

try:
    import FreeCAD
    import Part
except ImportError:
    print("ERROR: This script must be run inside FreeCAD.")
    print("  Option 1: Open FreeCAD, go to View > Panels > Python Console,")
    print("            then run: exec(open('fatif_adapter_lensboard_freecad.py').read())")
    print("  Option 2: freecad -c fatif_adapter_lensboard_freecad.py")
    sys.exit(1)

# === PARAMETERS (all in mm) ===

# Outer board profile
BOARD_SIZE = 170.0
BOARD_CORNER_R = 50.0
BOARD_THICKNESS = 5.5  # total thickness

# Back perimeter step
STEP_WIDTH = 7.5       # width from outer edge
STEP_DEPTH = 3.0       # depth from back face
STEP_INNER_SIZE = BOARD_SIZE - 2 * STEP_WIDTH   # 155mm
STEP_INNER_R = BOARD_CORNER_R - STEP_WIDTH       # 42.5mm

# Front recess for Gowland board
GOWLAND_SIZE = 139.0   # 138.5 nominal + 0.5mm clearance
GOWLAND_CORNER_R = 3.4
RECESS_DEPTH = 0.5     # from front face

# Central bore
BORE_DIA = 110.0

# Ball plunger (M6)
PLUNGER_DIA = 5.0      # tap drill for M6 (~5.0mm)
PLUNGER_DEPTH = 10.0
PLUNGER_X = 0.0        # centered on slide axis
PLUNGER_Y_WALL = -GOWLAND_SIZE / 2  # -Y wall of recess

# Slide opening: recess extends to +X board edge
SLIDE_MARGIN = 2.0     # extra past board edge (gets clipped by profile)

# === HELPER: Rounded rectangle wire ===

def make_rounded_rect_wire(size_x, size_y, radius, z=0):
    """Create a wire for a rounded rectangle centered at origin."""
    half_x = size_x / 2
    half_y = size_y / 2
    r = radius

    # Corner centers
    cx = half_x - r
    cy = half_y - r

    edges = []

    # Bottom edge (left to right)
    edges.append(Part.makeLine(
        FreeCAD.Vector(-cx, -half_y, z),
        FreeCAD.Vector(cx, -half_y, z)))

    # Bottom-right corner
    edges.append(Part.makeCircle(r,
        FreeCAD.Vector(cx, -cy, z),
        FreeCAD.Vector(0, 0, 1),
        270, 360))

    # Right edge (bottom to top)
    edges.append(Part.makeLine(
        FreeCAD.Vector(half_x, -cy, z),
        FreeCAD.Vector(half_x, cy, z)))

    # Top-right corner
    edges.append(Part.makeCircle(r,
        FreeCAD.Vector(cx, cy, z),
        FreeCAD.Vector(0, 0, 1),
        0, 90))

    # Top edge (right to left)
    edges.append(Part.makeLine(
        FreeCAD.Vector(cx, half_y, z),
        FreeCAD.Vector(-cx, half_y, z)))

    # Top-left corner
    edges.append(Part.makeCircle(r,
        FreeCAD.Vector(-cx, cy, z),
        FreeCAD.Vector(0, 0, 1),
        90, 180))

    # Left edge (top to bottom)
    edges.append(Part.makeLine(
        FreeCAD.Vector(-half_x, cy, z),
        FreeCAD.Vector(-half_x, -cy, z)))

    # Bottom-left corner
    edges.append(Part.makeCircle(r,
        FreeCAD.Vector(-cx, -cy, z),
        FreeCAD.Vector(0, 0, 1),
        180, 270))

    wire = Part.Wire(edges)
    return wire


def make_rounded_rect_solid(size_x, size_y, radius, height, z_base=0):
    """Extrude a rounded rectangle into a solid."""
    wire = make_rounded_rect_wire(size_x, size_y, radius, z_base)
    face = Part.Face(wire)
    solid = face.extrude(FreeCAD.Vector(0, 0, height))
    return solid


# === BUILD THE PART ===

print("Building Fatif adapter lensboard...")

# 1. Main body
body = make_rounded_rect_solid(BOARD_SIZE, BOARD_SIZE, BOARD_CORNER_R, BOARD_THICKNESS, 0)
print("  Main body created")

# 2. Back perimeter step: cut away outer ring from z=0 to z=STEP_DEPTH
outer_ring = make_rounded_rect_solid(BOARD_SIZE + 2, BOARD_SIZE + 2, BOARD_CORNER_R, STEP_DEPTH, 0)
inner_keep = make_rounded_rect_solid(STEP_INNER_SIZE, STEP_INNER_SIZE, STEP_INNER_R, STEP_DEPTH + 1, -0.5)
step_cut = outer_ring.cut(inner_keep)
body = body.cut(step_cut)
print("  Back perimeter step cut")

# 3. Front recess for Gowland board
# Main recess pocket
recess_z = BOARD_THICKNESS - RECESS_DEPTH
recess_pocket = make_rounded_rect_solid(GOWLAND_SIZE, GOWLAND_SIZE, GOWLAND_CORNER_R, RECESS_DEPTH + 1, recess_z)

# Slide opening extension: extend recess to +X edge
# Use a box from the recess right edge to well past the board edge
slide_ext = Part.makeBox(
    BOARD_SIZE,                          # length in X (oversized, will be clipped)
    GOWLAND_SIZE,                        # width in Y (same as recess)
    RECESS_DEPTH + 1,                    # height
    FreeCAD.Vector(0, -GOWLAND_SIZE/2, recess_z))  # start at center, extend +X

recess_total = recess_pocket.fuse(slide_ext)
body = body.cut(recess_total)
print("  Front recess and slide opening cut")

# 4. Central through-bore
bore = Part.makeCylinder(BORE_DIA / 2, BOARD_THICKNESS + 2,
    FreeCAD.Vector(0, 0, -1),
    FreeCAD.Vector(0, 0, 1))
body = body.cut(bore)
print("  Central bore cut")

# 5. Ball plunger hole (M6 tap drill = 5.0mm)
# Horizontal hole in -Y wall of recess, pointing +Y
# Z position: centered in the wall between recess floor and front face
plunger_z = BOARD_THICKNESS - RECESS_DEPTH / 2
plunger_hole = Part.makeCylinder(PLUNGER_DIA / 2, PLUNGER_DEPTH + 5,
    FreeCAD.Vector(PLUNGER_X, -BOARD_SIZE/2 - 1, plunger_z),
    FreeCAD.Vector(0, 1, 0))
body = body.cut(plunger_hole)
print("  Ball plunger hole cut")

# === EXPORT ===

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "fatif_adapter_lensboard.step")
body.exportStep(output_path)
print(f"\nSTEP file exported to: {output_path}")
print("Done!")
