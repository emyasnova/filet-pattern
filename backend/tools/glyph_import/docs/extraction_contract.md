# Extraction input contract

Phase 14 adds a local extraction mode for preparing individual symbol images from one
source sheet.

## CLI

```bash
python -m src.main --extract --input input/raw/sheet.png
```

Optional tuning arguments:

* `--threshold` - grayscale binarization threshold, `0..255`, default `128`
* `--no-denoise` - disable median denoise before binarization
* `--denoise-size` - positive odd median filter size, default `3`
* `--min-symbol-width` - minimum component width, default `8`
* `--min-symbol-height` - minimum component height, default `8`
* `--min-symbol-area` - minimum black-pixel component area, default `64`
* `--crop-padding` - non-negative crop padding in pixels, default `2`
* `--debug` - print verbose parameter output

## Input

* `--input` must point to one existing `.jpg` or `.png` file.
* The image may contain several separated symbol schemes on a light background.
* Symbol regions are detected as connected dark components after preprocessing.
* The mode does not infer `char` values and does not require `--char`.

## Output

For source `input/raw/sheet.png`, extraction writes:

* symbol crops to `input/extracted/sheet_001.png`, `sheet_002.png`, ...
* binary debug image to `input/debug/sheet_extraction_binary.png`
* bounding-box overlay to `input/debug/sheet_extraction_overlay.png`
* manifest to `output/manifests/manifest.json`

The manifest contains:

* source image path and format
* extracted symbol count
* debug artifact paths
* for each symbol: index, crop path, width, height, and pixel bounds
