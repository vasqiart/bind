# Bind

A macOS desktop app that combines all JPEG images in a folder into a single PDF **in filename order**.

## Overview

- **Input**: `.jpg` / `.jpeg` (case-insensitive) inside a folder
- **Output**: One PDF generated in the parent directory of the selected folder
- **Sorting**: Natural sort (extracts numeric parts from filenames)
- **Quality**: No JPEG re-compression (keeps image quality)

## Features

- Convert up to ~300 JPEG images in a folder into **one** PDF
- Drag & drop folder support
- Progress display / progress bar
- Natural filename order (e.g. `1, 2, 10` not `1, 10, 2`)
- No JPEG recompression (minimizes quality loss)

## Setup (macOS)

### Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run (development)

```bash
python app.py
```

### Build app (.app)

```bash
pip install pyinstaller
pyinstaller --windowed --name Bind app.py
```

The generated `.app` file is in `dist/Bind.app`.

## Usage

1. Launch `Bind.app`
2. Drag & drop a folder, or click "Select Folder"
3. Click "Create PDF"
4. PDF is saved in the parent directory as `foldername.pdf`
   - Example: `/Desktop/KindleShots/` → `/Desktop/KindleShots.pdf`

## Specifications

- **Output PDF name**: `foldername.pdf`
- **Save location**: Parent directory of the selected folder
- **If PDF already exists**: Overwrite
- **Sorting**: Natural sort (extracts numeric sequences from filenames)
- **Supported extensions**: `.jpg` / `.jpeg` (case-insensitive)
- **Batch size**: Up to 300 images processed at once; larger sets are automatically batched

## Notes

- All processing is local (no external data transmission)
- No JPEG recompression (preserves image quality)
- Error displayed if non-folder is dropped
