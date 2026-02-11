#!/usr/bin/env python3
"""Convert DXF files to PDF for quick visual review."""

import argparse
import sys
import os
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Convert DXF files to PDF")
parser.add_argument("--output-dir", default=".", help="Output directory for PDFs")
parser.add_argument("dxf_files", nargs="+", help="DXF files to convert")
args = parser.parse_args()

for path in args.dxf_files:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp)
    ax.set_aspect("equal")
    basename = os.path.splitext(os.path.basename(path))[0]
    pdf_path = os.path.join(args.output_dir, basename + ".pdf")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path} -> {pdf_path}")
