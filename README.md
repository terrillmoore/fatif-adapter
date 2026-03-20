# Fatif DS 20x25 Adapter Lensboard

An adapter that lets Gowland 8x10 lensboards mount in a Fatif DS 20x25
large-format camera front standard. Two design variants: three-piece laminate
(laser cut) and single-piece CNC milled. Both fabricated via
[SendCutSend](https://sendcutsend.com/).

## Design

### Three-piece laminate (laser cut)

Three aluminum sheets laminated with M3 screws:

| Sheet | Size | Material | Thickness | Finish | Feature |
|-------|------|----------|-----------|--------|---------|
| Front | 171.5mm sq, R50.75 | .063" 6061-T6 | 1.78mm | Powder coat matte black | 139mm square cutout for Gowland board |
| Middle | 171.5mm sq, R50.75 | .025" 2024-T3 | 0.64mm | Bare (sandwiched) | 110mm bore only — seals corner light leaks |
| Rear | 160mm sq, R45 | .100" 6061-T6 | 2.56mm | Black anodize | 110mm bore |

- **Total thickness:** 4.98mm
- **Lip:** Front + middle overhang rear by 5.75mm, creating the 2.42mm lip for Fatif spring clips (limit: 2.50mm)
- **Board retention:** Cambo / Crown Graphic style clips (see below)
- **Assembly:** 2x M3 pan head screws at (±74.75, 0) + 4x M3 clip screws

The CadQuery script generates individual STEP and DXF files for each part,
plus a combined assembly STEP for visualization.

### CNC single-piece alternative

A single 6061-T6 billet replaces all three sheets, eliminating the middle
sheet, 2 assembly screws, and inter-sheet alignment. CNC machined by
SendCutSend (upload STEP file directly).

| Feature | Spec |
|---------|------|
| Material | 0.250" (6.35mm) 6061-T6 billet |
| Outer profile | 171.5mm sq, R50.75 (same as laminate) |
| Rear perimeter step | 160mm sq (R45) inner, 3.93mm deep — creates 2.42mm lip |
| Front board pocket | 139mm sq (R3.4), 1.78mm deep — Gowland board sits flush |
| Through bore | 110mm dia |
| Screw holes | 4x M3 blind roll-tap (2.75mm pilot, 5mm deep) — clip screws only |
| Finish | Black Type II anodize (no powder coat available for CNC) |

- **Part count:** 5 (body + 2 clips + 4 screws) vs laminate's 8
- **Light seal:** Continuous machined pocket floor — no laminate gaps at corners
- **Trade-off:** ~3x cost vs laminate ($372 vs $117 at qty 1, March 2026 pricing)

### Clip design

Board retention uses a Cambo / Crown Graphic style mechanism:

| Clip | Material | Size | Features |
|------|----------|------|----------|
| Bottom (fixed) | .060" 304 SS (1.52mm) | 90mm × 10mm | Simple rectangular bar, R2 corners, 2.0mm board overlap |
| Top (sliding) | .060" 304 SS (1.52mm) | 90mm dog-bone, R2 corners | 14mm wide at ends / 8mm narrow in middle, 135° cam slots, single 45° rectangular tab (8mm tall) at -X end |

**Operation:** Push the top clip tab toward -X to retract it from the board
(cam slots convert lateral force to vertical retraction). Tilt the board in
under the fixed bottom clip, release the top clip, and gravity returns it
to the closed position — no springs needed. The cam slots provide 5.6mm of
travel, yielding ~4.0mm of Y retraction from the board edge.

**Clip screws:** Adapter screw holes are at the center of each wide end
(X = ±32.5, Y = 74, spacing 65mm) so the top clip body is centered on the
adapter when in the gravity/closed position.

### Nameplate paint treatment

Both clips have painted nameplates — matte black paint with cutout letters
(bare 304 SS shows through):

| Clip | Text | Font | Spacing | Paint area |
|------|------|------|---------|------------|
| Top | "fatif" (lowercase) | Futura Medium | 0.5em | Follows dog-bone profile, 1mm inset, with slot clearance cutouts |
| Bottom | "GOWLAND" (uppercase) | Futura Light | 0.62em | 88mm × 8mm rounded rect, 1mm inset, no screw clearance (black screws) |

Text height is ~4mm cap height for both. The bottom clip uses Futura Light
to better match the engraved lettering on original Gowland front standards.

**Fabrication options:**
1. Paint entire clip, then fiber-laser the letter outlines off (paint + laser etch)
2. Vinyl stencil with letter cutouts, spray matte black, peel
3. Silk screen (traditional method)

Paint artwork SVGs (`make artwork`) provide vector outlines for any of these
methods.

### Hardware (laminate variant)

| Qty | Fastener | Length | Use | Notes |
|-----|----------|--------|-----|-------|
| 2 | M3 pan head screw (DIN 7985), **black oxide** | M3×4 | Assembly screws at (±74.75, 0) | Through front + middle, ~1.6mm thread engagement in tapped rear |
| 2 | M3 pan head screw (DIN 7985), stainless | M3×6 | Top clip screws at (±32.5, 74) | Through clip + front + middle, ~2.1mm into tapped rear |
| 2 | M3 pan head screw (DIN 7985), **black oxide** | M3×6 | Bottom clip screws at (±25, -72.5) | Same stack; black to blend with painted clip |

All 6 screws laminate through all three sheets into tapped holes in the rear
sheet (M3×0.5, tap drill 2.5mm).

### Hardware (CNC variant)

| Qty | Fastener | Length | Use | Notes |
|-----|----------|--------|-----|-------|
| 2 | M3 pan head screw (DIN 7985), stainless | M3×6 | Top clip screws at (±32.5, 74) | Through clip into blind roll-tapped hole in body |
| 2 | M3 pan head screw (DIN 7985), **black oxide** | M3×6 | Bottom clip screws at (±25, -72.5) | Same; black to blend with painted clip |

4 screws total. No assembly screws needed. Roll-tap pilot holes are 2.75mm
(not 2.5mm cut-tap) per SendCutSend CNC requirements.

### Fabrication notes

- **Vendor:** [SendCutSend](https://sendcutsend.com/) for laser cutting
  (laminate) or CNC machining (single-piece), plus powder coat and anodize.
  [Ponoko](https://www.ponoko.com/) is an alternative for 304 SS clips
  (also offers painting for logo application).
- **Deburring:** Specify deburring on all parts, especially clip edges
  that will be handled during board changes.
- **Clip DXFs** show 2D profiles (flat patterns for the top clip, outline
  for the bottom clip). The top clip has a single 45° rectangular tab at
  the upper-left corner; bend 90° up along the diagonal bend line.
- **Tapping (laminate):** Rear sheet M3 holes are tap drill size (2.5mm).
  Specify M3×0.5 tapping, or tap by hand after receiving parts.
- **Tapping (CNC):** Holes are 2.75mm (roll-tap pilot). Select M3×0.5
  roll tap in the SendCutSend tapping setup. Apply to all 4 holes.

### Surface finish rationale

The rear sheet faces into the camera body and is the primary stray-light
surface. Black anodize (MIL-A-8625 Type II Class 2) was chosen over matte
powder coat for several reasons:

- **Lower visible-spectrum reflectance.** Black anodize measures ~4-7% total
  hemispherical reflectance (THR) in 400-700nm vs ~5-10% for matte powder
  coat. SendCutSend's Axalta Black Magic BK120 is spec'd at 0-9% gloss (60°).
- **Thinner coating.** Anodize adds ~0.02mm total vs ~0.18mm for powder coat,
  which matters for the tight lip thickness budget.
- **Durability.** Anodize is integral to the metal surface and won't chip from
  board changes or stacking.

Standard black anodize does get reflective in the near-IR (~25-35% above
700nm) due to the organic dye, but this is largely irrelevant for photographic
film and digital sensors. For specialty optical applications, bead-blasted
surfaces or optical-grade anodize (e.g. Pioneer Optical Black, ~1% THR) would
improve performance further.

The front sheet is powder coated because it faces outward (not a stray-light
concern inside the camera) and benefits from the more durable, thicker finish
for handling. The middle sheet needs no finish since it is sandwiched between
the other two.

The CNC single-piece variant uses black Type II anodize on all surfaces
(powder coat is not available for SendCutSend CNC parts). This is acceptable
since anodize provides adequate stray-light performance on both the camera-
facing and outward-facing surfaces.

References:
- [TAMU Reflectance of Black Materials Catalog](https://instrumentation.tamu.edu/reflectance-black/)
- [Pioneer Metal Finishing: Optical Black](https://www.pioneermetal.com/processes/optical-black/)

## Quick Start

```sh
make init      # create venv, install CadQuery
make all       # generate everything (STEP, DXF, PNG, SVG)
```

All generated files go to the `output/` directory (configurable via
`make all OUTPUT_DIR=custom_dir`).

Individual targets: `make build` (STEP + DXF), `make mockup` (PNG),
`make artwork` (paint SVGs).

Run `make help` to see all targets.

### Prerequisites

- Python 3.9+
- `make`

Everything else is installed automatically by `make init`.

### Generated Files

All files are written to `output/` (override with `OUTPUT_DIR`).

| File | Description |
|------|-------------|
| `output/fatif_front_sheet.step/.dxf` | Front sheet with cutout and screw holes |
| `output/fatif_middle_sheet.step/.dxf` | Middle light-seal sheet with bore |
| `output/fatif_rear_sheet.step/.dxf` | Rear sheet with bore and tapped holes |
| `output/fatif_bottom_clip.step/.dxf` | Fixed bottom retention clip (flat pattern) |
| `output/fatif_top_clip.step/.dxf` | Sliding top retention clip with tab (flat pattern) |
| `output/fatif_assembly.step` | Laminate assembly for visualization |
| `output/fatif_cnc_body.step` | CNC single-piece body (upload to SCS for quote) |
| `output/fatif_cnc_assembly.step` | CNC assembly with clips for visualization |
| `output/fatif_nameplate_mockup.png` | Three-panel mockup showing both nameplates |
| `output/fatif_top_clip_paint.svg` | Paint artwork for top clip ("fatif") |
| `output/fatif_bottom_clip_paint.svg` | Paint artwork for bottom clip ("GOWLAND") |

### Adjusting Dimensions

All dimensions are parametric. The current values are from caliper
measurements of an actual Fatif DS original lensboard. Key parameters
near the top of `fatif_adapter_cadquery.py`:

```python
BOARD_SIZE = 171.5      # outer profile (mm, square)
BOARD_CORNER_R = 50.75  # corner radius
FRONT_THICK = 1.78      # .063" 6061 powder coated
MIDDLE_THICK = 0.64     # .025" 2024-T3 bare
REAR_THICK = 2.56       # .100" 6061 black anodized
STEP_WIDTH = 5.75       # lip width from outer edge
```

Then re-run `make all`.

## License

[MIT](LICENSE) — Copyright (c) 2026 Terrill Moore
