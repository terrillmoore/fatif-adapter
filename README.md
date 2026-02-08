# Fatif DS 20x25 Adapter Lensboard

A three-piece laminated adapter that lets Gowland 8x10 lensboards mount in a
Fatif DS 20x25 large-format camera front standard. Designed for laser-cut
fabrication via [SendCutSend](https://sendcutsend.com/).

## Design

Three aluminum sheets laminated with M3 flat head screws:

| Sheet | Size | Material | Thickness | Finish | Feature |
|-------|------|----------|-----------|--------|---------|
| Front | 171.5mm sq, R50.75 | .063" 6061-T6 | 1.78mm | Powder coat matte black | 139mm square cutout for Gowland board |
| Middle | 171.5mm sq, R50.75 | .025" 2024-T3 | 0.64mm | Bare (sandwiched) | 110mm bore only — seals corner light leaks |
| Rear | 160mm sq, R45 | .100" 6061-T6 | 2.56mm | Black anodize | 110mm bore |

- **Total thickness:** 4.98mm
- **Lip:** Front + middle overhang rear by 5.75mm, creating the 2.42mm lip for Fatif spring clips (limit: 2.50mm)
- **Board retention:** Cambo-style clips — fixed bottom bar + spring-loaded sliding top bar
- **Assembly:** 4x M3 flat head screws on cardinal axes at R=74.75mm

The CadQuery script generates individual STEP and DXF files for each part,
plus a combined assembly STEP for visualization.

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

References:
- [TAMU Reflectance of Black Materials Catalog](https://instrumentation.tamu.edu/reflectance-black/)
- [Pioneer Metal Finishing: Optical Black](https://www.pioneermetal.com/processes/optical-black/)

## Quick Start

```sh
make init    # create venv, install CadQuery
make build   # generate STEP + DXF files
```

Run `make help` to see all targets.

### Prerequisites

- Python 3.9+
- `make`

Everything else is installed automatically by `make init`.

### Generated Files

| File | Description |
|------|-------------|
| `fatif_front_sheet.step/.dxf` | Front sheet with cutout and screw holes |
| `fatif_middle_sheet.step/.dxf` | Middle light-seal sheet with bore |
| `fatif_rear_sheet.step/.dxf` | Rear sheet with bore and tapped holes |
| `fatif_bottom_clip.step/.dxf` | Fixed bottom retention clip |
| `fatif_top_clip.step/.dxf` | Sliding top retention clip (with finger tab) |
| `fatif_assembly.step` | Combined assembly for visualization |

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

Then re-run `make build`.

## License

[MIT](LICENSE) — Copyright (c) 2026 Terrill Moore
