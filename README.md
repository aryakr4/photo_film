# photo_film

Personal batch film-simulation pipeline. Drops Fuji RAW (or JPEG/TIFF) photos
through [spektrafilm](https://github.com/andreavolpato/spektrafilm)'s Kodak
Portra 400 negative + Kodak Portra Endura print simulation, producing a
natural-looking, high-quality TIFF for each photo.

## Setup (one time, or on a fresh clone)

Requires [uv](https://docs.astral.sh/uv/) installed.

```bash
git clone <this-repo-url> photo_film
cd photo_film
./setup.sh
```

This creates `.venv/` with Python 3.13 and installs `spektrafilm` straight
from its GitHub repo (not vendored here), plus this project's own small
package.

## Usage

```bash
cp /path/to/your/photos/*.RAF raw_inbox/
.venv/bin/python process.py
```

Converted TIFFs land directly in `~/Downloads/`, named
`<original_filename>_kodak_portra_400_kodak_portra_endura.tif`.

- Supported input formats: Fuji/Canon/Nikon/Sony/etc. RAW
  (`.raf .cr2 .cr3 .nef .arw .dng .rw2 .orf .pef .srw`), JPEG (`.jpg .jpeg`),
  and linear scene-referred TIFF (`.tif .tiff`).
- Re-running is safe: a file already processed (its output already exists in
  `~/Downloads`) is skipped, not reprocessed.
- One bad file won't stop the batch — it's logged and the rest still run;
  a summary line prints at the end.
- Original files are **not** moved or deleted automatically — they stay in
  `raw_inbox/` until you remove them yourself.

## Configuration

Edit `config.toml` to change the film/print profile or output bit depth:

```toml
[profiles]
film = "kodak_portra_400"
print = "kodak_portra_endura"

[output]
directory = "~/Downloads"
bit_depth = 16
```

## Development

```bash
.venv/bin/python -m pytest tests/ -v
```
