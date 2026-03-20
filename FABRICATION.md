# Fatif Adapter Fabrication Checklist

## Phase 1: Generate Artifacts

- [ ] Run `make clean && make all` to regenerate all files from latest source
- [ ] Verify output files exist in `output/`:
  - [ ] 5 STEP files + 5 DXF files (laminate variant)
  - [ ] `output/fatif_cnc_body.step` and `output/fatif_cnc_assembly.step` (CNC variant)
  - [ ] `output/fatif_assembly.step` (color-coded laminate assembly)
  - [ ] `output/fatif_nameplate_mockup.png`
  - [ ] `output/fatif_top_clip_paint.svg` and `output/fatif_bottom_clip_paint.svg`
- [ ] Open assembly STEP(s) in a viewer — sanity-check fit and dimensions
- [ ] Open each DXF — verify profiles look correct

## Phase 2: Order Body (choose one variant)

### Option A: Three-Piece Laminate (SendCutSend laser cut)

Go to [sendcutsend.com](https://sendcutsend.com/) and create 3 line items:

### Front sheet

- [ ] Upload `output/fatif_front_sheet.dxf`
- [ ] Material: 6061-T6 Aluminum, .063" (1.60mm)
- [ ] Finish: Powder coat — matte black (Axalta Black Magic BK120)
- [ ] Add deburring
- [ ] Qty: 1 (or 2 for a spare)

### Middle sheet

- [ ] Upload `output/fatif_middle_sheet.dxf`
- [ ] Material: 2024-T3 Aluminum, .025" (0.64mm)
- [ ] Finish: None (bare)
- [ ] Deburring: not available at this thickness — hand deburr with scotch-brite if needed at assembly
- [ ] Qty: 1 (or 2)

### Rear sheet

- [ ] Upload `output/fatif_rear_sheet.dxf`
- [ ] Material: 6061-T6 Aluminum, .100" (2.54mm)
- [ ] Finish: Black anodize (Type II)
- [ ] Add tapping: M3x0.5 on all 6 screw holes — OR tap by hand after delivery
- [ ] Add deburring
- [ ] Qty: 1 (or 2)

### Before checkout

- [ ] Verify all 3 parts show correct outer dimensions (~171.5mm / ~160mm)
- [ ] Note: powder coat adds ~0.18mm; anodize adds ~0.02mm — already accounted for in design
- [ ] Save order confirmation / screenshot

### Option B: CNC Single-Piece Body (SendCutSend CNC machining)

Go to [sendcutsend.com](https://sendcutsend.com/) and upload the STEP file:

- [ ] Upload `output/fatif_cnc_body.step`
- [ ] Material: 6061-T6 Aluminum (auto-detected as CNC billet part)
- [ ] Add tapping: select all 4 holes, M3×0.5 Roll Tap
  - [ ] Verify holes show as 0.1083" / 2.75mm diameter
- [ ] Add finish: Black Type II anodize
- [ ] Qty: 1
- [ ] Note: no DXF needed, no middle/front sheets, no assembly screws

### Before checkout (either variant)

- [ ] Save order confirmation / screenshot

## Phase 3: Order Stainless Steel Clips (Ponoko)

Go to [ponoko.com/laser-cutting](https://www.ponoko.com/laser-cutting):

### Top clip

- [ ] Upload `output/fatif_top_clip.dxf`
- [ ] Material: #4 304 Stainless Steel, 1.52mm (.060")
- [ ] Add bending: 90° bend along the 45° diagonal line at upper-left corner (tab bends up 8mm)
  - [ ] Include a note/drawing showing bend line location and direction
- [ ] Add deburring
- [ ] Qty: 1 (or 2 — clips are the most likely part to need iteration)

### Bottom clip

- [ ] Upload `output/fatif_bottom_clip.dxf`
- [ ] Material: #4 304 Stainless Steel, 1.52mm (.060")
- [ ] Add deburring
- [ ] Qty: 1 (or 2)

### Painting/silkscreen (both clips)

- [ ] Request silkscreen or painting finishing on both clips
- [ ] Upload `output/fatif_top_clip_paint.svg` as artwork for top clip
- [ ] Upload `output/fatif_bottom_clip_paint.svg` as artwork for bottom clip
- [ ] Specify: matte black paint, even-odd fill rule (letters are cutouts — bare SS shows through)
- [ ] Note for top clip: paint artwork accounts for bend-line offset; apply paint to flat part BEFORE bending
- [ ] Note for bottom clip: black oxide M3 pan head screws will cover the screw holes; paint over them

### Before checkout

- [ ] Confirm 1.52mm thickness (not 1.50mm) — ask Ponoko support if ambiguous
- [ ] Verify pricing includes bending setup for top clip
- [ ] Save order confirmation

## Phase 4: Order Hardware

Source from McMaster-Carr, Bolt Depot, Amazon, or similar:

**Laminate variant (6 screws):**
- [ ] 2x M3×4mm pan head screw (DIN 7985), **black oxide** — assembly screws
- [ ] 2x M3×6mm pan head screw (DIN 7985), stainless steel — top clip screws
- [ ] 2x M3×6mm pan head screw (DIN 7985), **black oxide** — bottom clip screws
- [ ] (Optional) M3 tap + 2.5mm drill bit if tapping rear sheet by hand

**CNC variant (4 screws):**
- [ ] 2x M3×6mm pan head screw (DIN 7985), stainless steel — top clip screws
- [ ] 2x M3×6mm pan head screw (DIN 7985), **black oxide** — bottom clip screws

## Phase 5: Assembly

### Prep (laminate)

- [ ] Inspect all parts for burrs, defects, dimensional accuracy
- [ ] Test-fit Gowland board in front sheet cutout (should be ~0.5mm clearance per side)
- [ ] Verify bore alignment by stacking sheets without screws
- [ ] If rear sheet is not tapped: hand-tap 6x M3×0.5 holes

### Prep (CNC)

- [ ] Inspect body for burrs, defects, dimensional accuracy
- [ ] Test-fit Gowland board in front pocket (should be ~0.5mm clearance per side)
- [ ] Verify tapped holes accept M3 screws

### Laminate sheets (skip for CNC)

- [ ] Stack: front (powder coat side out) → middle → rear (anodize side in toward camera)
- [ ] Align all holes
- [ ] Install 2x M3×4 pan head assembly screws at (±74.75, 0) — black oxide, heads on front face
- [ ] Snug but don't overtighten (aluminum threads)

### Install clips

- [ ] Bottom clip: position with 2.0mm overlap on board opening, fasten with 2x M3×6 black oxide pan head screws at (±25, -72.5)
- [ ] Top clip: slide cam slots onto 2x M3×6 SS pan head screws at (±32.5, +74)
  - [ ] Verify slide action: push tab toward -X → clip retracts ~4mm from board edge
  - [ ] Release → gravity returns clip to closed (2.0mm overlap)
  - [ ] Verify clip moves freely, no binding

### Functional test

- [ ] Insert a Gowland lensboard: retract top clip, tilt board under bottom clip, release top clip
- [ ] Board should be held securely with no rattle
- [ ] Remove board: retract top clip, tilt board out
- [ ] Verify adapter seats properly in Fatif front standard casting (lip fits within 2.50mm channel)

## Phase 6: Final Checks

- [ ] Verify bore is unobstructed (110mm clear aperture)
- [ ] Check for light leaks: shine flashlight through from rear, look for gaps at middle sheet edges
- [ ] Mount a lens on a Gowland board and test on camera
- [ ] Photograph finished adapter for project documentation
