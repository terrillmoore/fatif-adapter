# Fatif Adapter - Claude Code Context

## Project Overview

CadQuery-based parametric model for an adapter lensboard that mounts Gowland
8x10 lensboards in a Fatif DS 20x25 large-format camera front standard. Two
design variants: three-piece laminate (laser cut) and single-piece CNC milled.
Outputs STEP/DXF files for fabrication, plus nameplate mockup and paint artwork.

## Build

Environment is uv-managed (`pyproject.toml` + `uv.lock`). Make targets run
scripts via `uv run`; there is no venv to activate.

```sh
make init      # uv sync (create .venv/ from uv.lock)
make all       # generate everything into output/
make clean     # rm -rf output/
```

Output directory is configurable: `make all OUTPUT_DIR=custom_dir`.

Individual targets: `build` (STEP+DXF), `mockup` (PNG), `artwork` (SVGs),
`blanks` (corner-radius test squares DXF), `pdf` (DXF-to-PDF conversion).

Run scripts without make via `uv run python <script>.py --output-dir output`.
On Windows, `make` needs Git Bash + GNU make (`scoop install make`); or just
use `uv run` directly. `nlopt` is pinned to 2.9.1 in `pyproject.toml` (newest
release with macOS x86_64 wheels alongside arm64/win/linux — keeps the lock
cross-platform).

## File Layout

| File | Purpose |
|------|---------|
| `fatif_adapter_cadquery.py` | Main CadQuery script: laminate + CNC body models, DXF flat patterns, assembly STEPs |
| `generate_nameplate_mockup.py` | Three-panel matplotlib mockup of clip nameplates |
| `generate_paint_artwork.py` | Paint artwork SVGs (even-odd compound paths for knockout text) |
| `generate_corner_squares.py` | Corner-radius test squares DXF (verify casting corners pre-refab) |
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
- `CNC_POCKET_SIZE`/`CNC_POCKET_R` = 139.47mm/R3.95 — smaller than the laminate
  `GOWLAND_SIZE` (139.75/R4.09) because the CNC body is anodized, not powder
  coated, so its pocket wall removes less material; both hit ~0.30mm/side fit
- `CNC_M3_ROLL_TAP` = 2.75mm (SCS roll tap minimum for M3x0.5)

## Code Conventions

- Python 3.9+, no type annotations in existing code
- CadQuery 2.6.1, uv-managed (`.venv/` synced from `uv.lock`)
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
  - File: upload DXF/DWG/EPS/AI for instant pricing; PDF is custom-quote only
  - Multiple parts allowed pre-nested in one 2D file (same material/thickness)
  - No solid/raster engraving — only single-line etch (layer `SCS_SLE`) or
    no-kerf through-cut (layer `SCS_NOKERF`); it's LAYER-NAME based, not color.
    Both need a checkout note and are material-limited
  - Cheap/no-finish prototype stock: bare 5052 aluminum (economical alloy)
  - Corner squares (`make blanks`) → `fatif_corner_squares_front.dxf` +
    `_rear.dxf` (cut, one part each) + `_key.pdf` (print, don't cut). Two SOLID
    squares (front 157.5mm, rear 145.5mm), each corner a different candidate
    radius. SEPARATE files (not nested) — SCS prices per part and its quote UI
    keys size/options off the file bbox, so a nested file misreads size and
    hides options. Kept solid + label-free on purpose: laser
    cost tracks pierce count, and per-corner 7-seg numerals were ~65 pierces
    each. Instead one small orientation hole marks the smallest-R (BL) corner,
    bottom-biased so it's flip-proof; the key PDF maps corners → radii. All
    closed contours on layer `0`, mm-stamped (`$INSUNITS=4`; Ponoko misreads
    unstamped files as inches). Was earlier a comb, then labeled frames.
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
