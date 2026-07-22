.PHONY: help init all build mockup artwork blanks pdf clean

# Environment is uv-managed (pyproject.toml + uv.lock). `uv run` resolves the
# interpreter and auto-syncs deps, so there is no venv path to hardcode --
# this works the same on macOS, Linux, and Windows (git bash).
UV := uv
SCRIPT := fatif_adapter_cadquery.py
OUTPUT_DIR ?= output

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-10s %s\n", $$1, $$2}'

init: ## Sync the uv-managed environment (.venv from uv.lock)
	$(UV) sync

all: build mockup artwork ## Generate all artifacts (STEP, DXF, PNG, SVG)

build: ## Generate STEP and DXF files
	@mkdir -p $(OUTPUT_DIR)
	$(UV) run python $(SCRIPT) --output-dir $(OUTPUT_DIR)

mockup: ## Generate nameplate mockup PNG
	@mkdir -p $(OUTPUT_DIR)
	$(UV) run python generate_nameplate_mockup.py --output-dir $(OUTPUT_DIR)

artwork: ## Generate paint artwork SVGs
	@mkdir -p $(OUTPUT_DIR)
	$(UV) run python generate_paint_artwork.py --output-dir $(OUTPUT_DIR)

blanks: ## Generate corner-radius test squares DXF
	@mkdir -p $(OUTPUT_DIR)
	$(UV) run python generate_corner_squares.py --output-dir $(OUTPUT_DIR)

pdf: build ## Convert DXF files to PDF for viewing
	$(UV) run python dxf2pdf.py --output-dir $(OUTPUT_DIR) $(OUTPUT_DIR)/*.dxf

clean: ## Remove generated output directory
	rm -rf $(OUTPUT_DIR)
