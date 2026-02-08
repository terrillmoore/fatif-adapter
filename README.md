# Fatif DS 20x25 Adapter Lensboard

A three-piece laminated adapter that lets Gowland 8x10 lensboards mount in a
Fatif DS 20x25 large-format camera front standard. Designed for laser-cut
fabrication via [SendCutSend](https://sendcutsend.com/).

## Design

Three aluminum sheets laminated with M3 flat head screws:

| Sheet | Size | Thickness | Feature |
|-------|------|-----------|---------|
| Front | 170mm sq, R50 | 2.0mm | 139mm square cutout for Gowland board |
| Middle | 170mm sq, R50 | 0.5mm | 110mm bore only — seals corner light leaks |
| Rear | 155mm sq, R42.5 | 3.0mm | 110mm bore |

- **Total thickness:** 5.5mm (matches Fatif original)
- **Lip:** Front + middle overhang rear by 7.5mm, creating the 2.5mm lip for Fatif standard clips
- **Board retention:** Cambo-style clips — fixed bottom bar + spring-loaded sliding top bar

The CadQuery script generates individual STEP and DXF files for each part,
plus a combined assembly STEP for visualization.

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

Sheet thicknesses are parametric — measure your Fatif standard with calipers
and edit the values near the top of `fatif_adapter_cadquery.py`:

```python
FRONT_THICK = 2.0
MIDDLE_THICK = 0.5
REAR_THICK = 3.0
```

Then re-run `make build`.

## License

[MIT](LICENSE) — Copyright (c) 2026 Terrill Moore
