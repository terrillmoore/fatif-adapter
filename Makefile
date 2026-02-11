.PHONY: help init all build mockup artwork pdf clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
SCRIPT := fatif_adapter_cadquery.py
OUTPUT_DIR ?= output

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
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON) $(SCRIPT) --output-dir $(OUTPUT_DIR)

mockup: $(VENV)/.installed ## Generate nameplate mockup PNG
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON) generate_nameplate_mockup.py --output-dir $(OUTPUT_DIR)

artwork: $(VENV)/.installed ## Generate paint artwork SVGs
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON) generate_paint_artwork.py --output-dir $(OUTPUT_DIR)

pdf: build ## Convert DXF files to PDF for viewing
	$(PYTHON) dxf2pdf.py --output-dir $(OUTPUT_DIR) $(OUTPUT_DIR)/*.dxf

clean: ## Remove generated output directory
	rm -rf $(OUTPUT_DIR)
