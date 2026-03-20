# Fatif Adapter - Claude Code Context

## Project Overview

CadQuery-based parametric model for an adapter lensboard that mounts Gowland
8x10 lensboards in a Fatif DS 20x25 large-format camera front standard. Two
design variants: three-piece laminate (laser cut) and single-piece CNC milled.
Outputs STEP/DXF files for fabrication, plus nameplate mockup and paint artwork.

## Build

```sh
make init      # create .venv/, install CadQuery
make all       # generate everything into output/
make clean     # rm -rf output/
```

Output directory is configurable: `make all OUTPUT_DIR=custom_dir`.

Individual targets: `build` (STEP+DXF), `mockup` (PNG), `artwork` (SVGs),
`pdf` (DXF-to-PDF conversion).

## File Layout

| File | Purpose |
|------|---------|
| `fatif_adapter_cadquery.py` | Main CadQuery script: laminate + CNC body models, DXF flat patterns, assembly STEPs |
| `generate_nameplate_mockup.py` | Three-panel matplotlib mockup of clip nameplates |
| `generate_paint_artwork.py` | Paint artwork SVGs (even-odd compound paths for knockout text) |
| `dxf2pdf.py` | DXF-to-PDF converter using ezdxf + matplotlib |
| `Makefile` | Build system; all scripts accept `--output-dir` |
| `README.md` | Design docs, hardware BOM, fabrication notes |
| `FABRICATION.md` | Step-by-step ordering and assembly checklist |

## Key Design Parameters

All dimensions are parametric constants near the top of
`fatif_adapter_cadquery.py`. Key values come from caliper measurements of
actual hardware. Changing a parameter and running `make all` regenerates
everything.

Critical constraints:
- Lip thickness must not exceed 2.50mm (Fatif casting channel)
- Total stack (laminate): 1.78 + 0.64 + 2.56 = 4.98mm
- Top clip slot positions differ from screw positions by `_closed_dx` offset

CNC variant parameters:
- `CNC_BILLET_THICK` = 6.35mm (0.250" 6061-T6)
- `CNC_LIP_THICK` = 2.42mm (matches laminate lip)
- `CNC_BOARD_POCKET_DEPTH` = 1.78mm (board sits flush with front face)
- `CNC_M3_ROLL_TAP` = 2.75mm (SCS roll tap minimum for M3x0.5)

## Code Conventions

- Python 3.9+, no type annotations in existing code
- CadQuery 2.6.1 in `.venv/`
- All scripts use `argparse` with `--output-dir` (default `.`)
- Generated files go to `output/` (gitignored), never the repo root
- Units are millimeters throughout
- Coordinates: origin at adapter center, +X right, +Y up (top clip side)

## CadQuery Patterns

- `cq.Assembly` with `.save()` for color-coded STEP (deprecation warning is expected)
- Dog-bone/complex profiles: `.moveTo()/.lineTo()/.close()` polylines, not sketch API
- Selective filleting via `NearestToPointSelector` on `|Z` edges
- Flat pattern DXF: build separate unfolded body, section at Z mid-height
- Tab fusion: `body.val().fuse(tab.val())` then wrap back in Workplane
- Top clip DXF includes bend line on "Bend" layer (ezdxf post-processing, green/color 3)

## Paint Artwork (SVGs)

- matplotlib `TextPath` converts Futura glyphs to vector outlines
- Compound SVG paths with `fill-rule="evenodd"` for knockout text
- All Y values negated in SVG output (clip-local Y-up to SVG Y-down)
- Coordinates match DXF flat patterns (clip-local mm, 1:1 scale)
- Top clip: "fatif" in Futura Medium, 0.5em spacing
- Bottom clip: "GOWLAND" in Futura Light, 0.62em spacing

## Nameplate Mockup

- Three-panel layout: full adapter view, top clip detail, bottom clip detail
- Uses Pillow `ImageFont` for character width measurement
- `_fillet_polygon` generates polyline-approximated rounded corners
- Set `dpi=` at `plt.figure()` creation for correct `transData` scaling
- Must call `fig.canvas.draw()` before using `transData`

## Fabrication Vendors

- **SendCutSend** (laser cut): aluminum sheets (powder coat/anodize)
  - No countersinking on sheets thinner than .125"
  - No deburring on .025" 2024-T3
- **SendCutSend** (CNC machining): single-piece 6061-T6 billet body
  - Upload STEP file (not DXF); auto-detected as CNC part
  - Finishes: media blast, Type II anodize (no powder coat for CNC)
  - Roll tapping available (M3x0.5 needs 2.75mm pilot, not 2.5mm cut-tap)
  - Min part size 0.5" per axis (may need confirmation for thin plates)
- **Ponoko**: 304 SS clips (laser cut + bend)
  - Bend line must be on separate DXF layer for bending service
  - Cannot paint non-flat parts (paint before bend not offered)
  - Silkscreen/painting requires custom quote
- Clip painting done separately (pad printing or silkscreen vendor)

## Hardware

Laminate variant — 6 screws, M3 pan head (DIN 7985), thread into tapped rear sheet:
- 2x M3x4 black oxide (assembly, front face)
- 2x M3x6 stainless (top clip)
- 2x M3x6 black oxide (bottom clip)

CNC variant — 4 screws only (no assembly screws needed):
- 2x M3x6 stainless (top clip)
- 2x M3x6 black oxide (bottom clip)
- Holes are blind roll-tapped in CNC body (2.75mm pilot, 5mm deep)
