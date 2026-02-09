.PHONY: help init all build mockup artwork pdf clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
SCRIPT := fatif_adapter_cadquery.py

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-10s %s\n", $$1, $$2}'

init: $(VENV)/.installed ## Create venv and install dependencies

$(VENV)/.installed:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install cadquery
	@touch $@

all: build mockup artwork ## Generate all artifacts (STEP, DXF, PNG, SVG)

build: $(VENV)/.installed ## Generate STEP and DXF files
	$(PYTHON) $(SCRIPT)

mockup: $(VENV)/.installed ## Generate nameplate mockup PNG
	$(PYTHON) generate_nameplate_mockup.py

artwork: $(VENV)/.installed ## Generate paint artwork SVGs
	$(PYTHON) generate_paint_artwork.py

pdf: build ## Convert DXF files to PDF for viewing
	$(PYTHON) dxf2pdf.py *.dxf

clean: ## Remove generated STEP, STL, DXF, PDF, PNG, and SVG files
	rm -f *.step *.stl *.dxf *.pdf fatif_nameplate_mockup.png *_paint.svg
