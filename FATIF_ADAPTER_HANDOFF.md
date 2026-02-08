# Fatif DS 20x25 Adapter Lensboard — Claude Code Handoff

## Project Summary
Design and fabricate a CNC-machined adapter lensboard for a Fatif DS 20x25 (8x10) large format camera that accepts existing 138.5mm Gowland 8x10 lensboards via a horizontal slide mechanism with ball plunger retention. Target output: STEP file for upload to Xometry or Protolabs.

## Background
- User (Terry Moore, github: terrillmoore) has a Fatif DS 20x25 camera with one lensboard (Copal #3 hole)
- User has multiple Gowland cameras (4x5 Pocket View, 8x10) with a full set of laser-cut lensboards
- Existing Gowland lensboard designs: https://github.com/terrillmoore/lensboards
- Goal: use all existing Gowland 8x10 lensboards on the Fatif camera interchangeably
- Fabrication: online CNC service (Xometry, Protolabs, Fictiv) — upload STEP, get part back
- Material: 6061-T6 aluminum
- Finish: black anodize or matte black powder coat (back face and bore especially)

## Key Dimensions (measured by hand, no calipers — VERIFY BEFORE FINAL ORDER)

### Fatif Lensboard (original)
- **Outer profile:** 170mm square, corners heavily rounded at R50mm
- **Straight edge per side:** ~70mm
- **Thickness:** 2.5mm (base plate)
- **Back face "baffle" rib:** 2.5mm wide, centered 7.5mm from outer edge, 3mm tall
  - The rib is NOT a light baffle in the traditional sense — it's the sealing surface that bears against the inner edge of the front standard casting
  - Inner radius of rib path: R42.5mm (50 - 7.5)
  - There is ~1mm clearance between the rib top and adjacent metal in the standard
- **Diagonal stiffeners:** run from baffle rib toward center, ~2.5mm wide, ~1mm high (cast features)
- **Original board is a casting**, crummy peeling paint
- **Retention:** small clips at bottom of standard opening, large clip at top — board slides in vertically
- **Thickness tolerance is TIGHT** — very little play, otherwise board would rattle
- **Lateral play:** ~0.5mm side-to-side when mounted — could add thin compressible material to back of lip if needed

### Gowland 8x10 Lensboards
- **Size:** 138.5mm × 138.5mm (confirmed from AI file and repo)
- **Corner radius:** 3.4mm (extracted from Illustrator file path data — essentially square with barely broken corners)
- **Thickness:** 0.063" aluminum (~1.6mm) with powder coat
- **Center hole:** 5.006mm diameter (on the blank/cover board)
- **Designs optimized for SendCutSend** laser cutting, 6061-T6, 0.063" thickness, black matte powder coat
- **Existing boards include:** Copal #0, Copal #1, Betax #3, Alphax #5 (for Kodak Commercial Ektar 14" f/6.3 in Ilex #5), Seiko S-1

### User's Lenses
- Heaviest: Kodak Commercial Ektar 14" f/6.3 in Ilex #5 shutter
  - Uses a flange; rear element fits through flange opening
  - Flange + protruding nuts need ~105mm radius clearance, 110mm is plenty
- Various other lenses in Copal #0, #1, Betax #3, Seiko shutters

## Design Specification

### Overall
- **Material:** 6061-T6 aluminum
- **Stock:** 6mm plate, faced to 5.5mm (or use 5.5mm if available)
- **Outer profile:** 170mm square, R50mm corners (matching Fatif original)

### Back Face (camera side, z=0 in our convention)
- **Perimeter step:** 3.0mm deep, creating a 2.5mm thick lip around the perimeter
- **Step width:** 7.5mm from outer edge
- **Step inner profile:** follows board shape at R42.5mm corners
- **Purpose:** the 2.5mm lip fits into the Fatif front standard clips
- **Everything inboard of the step stays at full 5.5mm thickness** — we are NOT milling out the center. The original used a rib to save material on a casting. We're starting thick and only cutting the perimeter step. This means no separate baffle rib is needed — the full-thickness center IS the baffle.

### Front Face (lens side, z=5.5mm)
- **Recess:** 0.5mm deep pocket for the Gowland board
- **Recess shape:** 139.0mm square (138.5mm nominal + 0.5mm clearance), R3.4mm corners
- **Centered on the board**
- **Slide opening:** recess extends to the +X edge of the board (right side) for horizontal board insertion, Graflex Speed Graphic style
- **Fixed stop:** on the -X side (left side) — the left wall of the recess
- **Ball plunger retention:** M6 (or possibly M5/M4 — see note below) tapped hole in the -Y wall (bottom) of the recess, centered on X axis, horizontal, pointing into the recess. Spring-loaded ball bears against Gowland board edge to hold it against the fixed stop.

### Through Hole
- **110mm diameter, centered, through all**
- Provides clearance for largest rear element/flange (Ilex #5)

### Ball Plunger Concern
The Gowland board sits in a 0.5mm recess and is 1.6mm thick, so only ~1.1mm of board edge is exposed above the recess floor. The ball plunger ball needs to engage this narrow target. An M6 plunger may work but consider:
- M5 or M4 with a smaller ball might be a better fit
- The plunger hole position needs to be at the right Z height to catch the board edge
- Plunger center should be at approximately z = 5.5 - 0.5 + 0.8 = 5.8mm? (recess floor + half the exposed board height) — needs to be worked out carefully

### Amazon ball plunger reference
- M6 x 10mm hex socket type: https://www.amazon.com/20pcs-Stainless-Thread-Spring-Plunger/dp/B07T6TBNJN
- McMaster: search "ball-nose spring plunger M6" (they don't allow direct linking)

## Files Created So Far

### In this conversation
1. **fatif_adapter_lensboard.scad** — OpenSCAD parametric model (needs refinement)
2. **fatif_adapter_lensboard_freecad.py** — FreeCAD Python script for STEP export (needs refinement)
3. **fatif_adapter_drawing.html** — Dimensioned technical drawing (reference)

### Issues with current models
- The slide opening geometry needs cleanup — currently just extends the recess with a box, but should properly merge with the outer profile
- Ball plunger hole Z position needs to be calculated properly for the 1.1mm engagement target
- Corner intersections between the recess corners and the slide opening need to be clean
- The OpenSCAD model can't export STEP directly (only STL)
- The FreeCAD script hasn't been tested

## Recommended Approach for Claude Code

### Option A: CadQuery (preferred)
```bash
pip install cadquery
# CadQuery can export STEP natively, parametric, Python-based
# Good for this kind of plate-with-pockets geometry
```

### Option B: FreeCAD
```bash
# FreeCAD with Python scripting
# Can export STEP
# More complex but very capable
```

### Option C: OpenSCAD + STEP conversion
```bash
# OpenSCAD for modeling, then convert STL to STEP
# Lossy conversion — CNC services prefer native STEP
# Not recommended
```

### Deliverables
1. **STEP file** — ready to upload to Xometry/Protolabs
2. **Technical drawing PDF** — for the machinist's reference (dimensions, tolerances, finish notes)
3. Optionally: OpenSCAD or CadQuery source for future parametric adjustments

## Open Questions
1. Exact ball plunger size (M4/M5/M6) — depends on engagement geometry
2. Whether 139.0mm recess clearance is right or should be tighter (138.7mm?)
3. Exact Z position of plunger hole
4. Whether the slide channel needs any relief/chamfer at the entry to guide the board in
5. Whether we need alignment features (e.g., a small V-notch or pin) for centering

## User's Environment
- macOS
- GitHub user: terrillmoore
- Has OpenSCAD, Adobe Illustrator
- Python available
- May or may not have FreeCAD installed
- Located in Ithaca, NY area
- Member of Fat Cat Fab Lab in Manhattan (has CNC access but prefers online service for simplicity)
