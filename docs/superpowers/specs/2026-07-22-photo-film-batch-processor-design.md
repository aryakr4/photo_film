# photo_film batch processor — design

## Purpose

A small, personal, easily-replicable tool for running photos (mostly Fuji RAW,
occasionally JPEG) through the [spektrafilm](https://github.com/andreavolpato/spektrafilm)
Kodak Portra 400 negative + Kodak Portra Endura print simulation, producing a
natural-looking high quality TIFF, without repeating the manual setup/scripting
work each time.

The project lives in its own private GitHub repo, `photo_film`, so it can be
cloned onto any machine and set up in a couple of commands.

## Non-goals

- Not building a GUI or a general-purpose CLI framework. One command, one
  batch, done.
- Not vendoring spektrafilm's source. It's installed as a normal dependency
  from its GitHub URL (avoids any ambiguity from redistributing GPLv3 source
  inside this repo, and stays up to date with upstream easily).
- Not auto-archiving/organizing original RAW files into dated folders. The
  user manages the lifecycle of raw originals manually (they've indicated
  they'll ask for them to be deleted after review).

## Architecture

Three files, plus the standard project scaffolding:

- `process.py` — the batch worker. Scans `raw_inbox/` for supported image
  files, runs each through the spektrafilm simulation, writes the result.
- `config.toml` — the only file a user should need to edit: film/print
  profile names, output bit depth, output directory.
- `setup.sh` — one-time bootstrap: creates a `uv`-managed Python 3.13
  virtualenv and installs spektrafilm + this project's (minimal/no extra)
  dependencies.

## Folder layout

```
photo_film/                  <- the git repo, cloned anywhere
  raw_inbox/                 <- (gitignored) drop new RAF/CR2/NEF/ARW/DNG/JPEG/TIFF files here
  process.py
  config.toml
  setup.sh
  pyproject.toml             <- declares spektrafilm as a git dependency
  .gitignore                 <- excludes raw_inbox/, .venv/, __pycache__/
  README.md
  docs/superpowers/specs/    <- this design doc
```

Processed output is **not** written inside the repo. It's dumped flat into
`~/Downloads/`, named `<original_basename>_portra400_endura.tif` (or whatever
film/print profile names are configured, following the same
`<basename>_<film>_<print>.tif` pattern so future stock changes stay
self-describing).

## Processing flow

For each file currently in `raw_inbox/`:

1. Compute the expected output path in `~/Downloads/`. If it already exists,
   skip this file (log "already processed, skipping") — makes reruns safe
   and idempotent without needing to move/rename inputs.
2. Detect format by extension:
   - RAW (`.raf .cr2 .cr3 .nef .arw .dng .rw2 .orf .pef .srw`): load via
     `spektrafilm.utils.raw_file_processor.load_and_process_raw_file`,
     as-shot white balance, linear ProPhoto RGB output.
   - JPEG (`.jpg .jpeg`): load via `load_image_oiio`, treat as sRGB SDR
     input (`input_color_space="sRGB"`, `input_cctf_decoding=True`).
   - TIFF (`.tif .tiff`): load via `load_image_oiio`, assumed already linear
     scene-referred ProPhoto RGB (spektrafilm's own recommended workflow via
     darktable export). This is documented in the README as an assumption —
     a rendered/gamma TIFF would need the JPEG-style handling instead.
   - Anything else: log as unsupported and skip.
3. Run `init_params(film_profile=..., print_profile=...)` from `config.toml`
   (defaults: `kodak_portra_400` / `kodak_portra_endura`), with neutral,
   natural settings (auto-exposure on, 0 EV compensation, neutral enlarger
   filters, default/physically-calibrated grain & halation — no stylized
   push), matching what was already validated manually earlier in this
   session.
4. `simulate()`, then save as a TIFF via `save_image_oiio` at the configured
   bit depth (default 16-bit) with an embedded sRGB ICC profile.
5. Leave the original file untouched in `raw_inbox/` (no move/delete —
   that's a manual, user-initiated step later).

A failure on one file (corrupt file, unsupported RAW variant, etc.) is
caught, logged with the reason, and the batch continues with the next file.
At the end, print a one-line summary: N processed, N skipped
(already done), N failed.

## Configuration (`config.toml`)

```toml
[profiles]
film = "kodak_portra_400"
print = "kodak_portra_endura"

[output]
directory = "~/Downloads"
bit_depth = 16   # 8, 16, or 32 (float)
```

## Setup / usage (what the README documents)

```bash
git clone <private-repo-url> photo_film
cd photo_film
./setup.sh              # one-time: creates .venv (Python 3.13 via uv), installs deps
cp your_photos/*.RAF raw_inbox/
./process.py            # or: .venv/bin/python process.py
# -> converted TIFFs appear in ~/Downloads/
```

## Testing

- Re-run today's already-validated case: copy `DSCF0892.jpg` into
  `raw_inbox/`, run `process.py`, confirm the output in `~/Downloads/`
  matches the visual result already approved earlier in this session.
- If a real Fuji `.RAF` file is available, run it through to confirm the RAW
  code path (`load_and_process_raw_file`) works end-to-end (this path has
  been read/understood but not yet exercised this session).
- Confirm rerun-safety: running `process.py` twice on the same inbox
  produces the "already processed, skipping" message the second time
  instead of reprocessing.

## GitHub

- Create a private repo named `photo_film` under the `aryakr4` account via
  `gh repo create photo_film --private --source=. --remote=origin`.
- Push the initial commit.
