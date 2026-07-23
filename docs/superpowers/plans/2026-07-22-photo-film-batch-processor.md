# photo_film Batch Processor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small, cloneable `photo_film` repo that batch-processes Fuji RAW (and occasional JPEG/TIFF) photos through spektrafilm's Kodak Portra 400 + Portra Endura simulation, dumping high-quality TIFFs into `~/Downloads`.

**Architecture:** A thin `src/photo_film/` package with one module per concern (config loading, format detection/naming, inbox scanning, image loading, simulation+save, CLI orchestration), plus a `process.py` entry-point script the user actually runs. The pure/cheap logic (config parsing, format detection, naming, scanning, orchestration/error-handling) gets real pytest coverage. The two modules that call into spektrafilm directly (`loading.py`'s raw/jpeg/tiff branches, `simulate.py`) are thin wrappers around already-validated spektrafilm calls and are verified via one real end-to-end manual run instead of mocks, since mocking spektrafilm's `simulate()` would test nothing real.

**Tech Stack:** Python 3.13, `uv` for environment/dependency management, `spektrafilm` (installed as a git dependency, not vendored), stdlib `tomllib` for config, `pytest` for tests.

## Global Constraints

- Python version: `~=3.13` (spektrafilm's own requirement; this project must match it).
- `spektrafilm` is installed as a normal pip dependency from `git+https://github.com/andreavolpato/spektrafilm.git` — never copy its source into this repo.
- Photo folders: `raw_inbox/` lives inside the repo but is gitignored (never committed); processed output is written flat into `~/Downloads`, never inside the repo.
- Output naming: `<original_basename>_<film_profile>_<print_profile>.tif` (e.g. `DSCF0892_kodak_portra_400_kodak_portra_endura.tif`).
- Default profiles: `kodak_portra_400` film / `kodak_portra_endura` print, default output bit depth 16, all overridable via `config.toml`.
- A file already processed (its output path already exists) must be skipped on rerun, not reprocessed.
- One failing file must not abort the batch — log it and continue, and reflect it in the end-of-run summary.
- The repo is created as a **private** GitHub repo named `photo_film` under the `aryakr4` account.

---

### Task 1: Project scaffolding

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/pyproject.toml`
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/.gitignore`
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/config.toml`
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/__init__.py`
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/raw_inbox/.gitkeep`

**Interfaces:**
- Produces: an installable `photo_film` package (currently empty) that later tasks add modules to under `src/photo_film/`. Config file shape consumed by Task 2.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "photo_film"
version = "0.1.0"
description = "Personal batch film-simulation pipeline (Fuji RAW/JPEG -> Kodak Portra 400 + Endura print, via spektrafilm)"
requires-python = "~=3.13"
dependencies = [
    "spektrafilm @ git+https://github.com/andreavolpato/spektrafilm.git",
]

[project.optional-dependencies]
dev = [
    "pytest",
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["photo_film", "photo_film.*"]
```

- [ ] **Step 2: Create `.gitignore`**

```
.venv/
__pycache__/
*.pyc
raw_inbox/*
!raw_inbox/.gitkeep
```

- [ ] **Step 3: Create `config.toml`**

```toml
[profiles]
film = "kodak_portra_400"
print = "kodak_portra_endura"

[output]
directory = "~/Downloads"
bit_depth = 16
```

- [ ] **Step 4: Create the empty package marker**

```bash
mkdir -p /Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film
touch /Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/__init__.py
mkdir -p /Users/aryakrishnagiri/Downloads/ph/photo_film/raw_inbox
touch /Users/aryakrishnagiri/Downloads/ph/photo_film/raw_inbox/.gitkeep
```

- [ ] **Step 5: Create the venv and install the (currently-empty) package + dev deps**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
uv venv --python 3.13 .venv
uv pip install --python .venv -e ".[dev]"
```

Expected: succeeds (this pulls the full spektrafilm dependency tree from GitHub — numpy, scipy, OpenImageIO, rawpy, napari, etc. — so it can take several minutes). Verify with:

```bash
.venv/bin/python -c "import photo_film; import spektrafilm; print('ok')"
```

Expected output: `ok`

- [ ] **Step 6: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add pyproject.toml .gitignore config.toml src/photo_film/__init__.py raw_inbox/.gitkeep
git commit -m "Scaffold photo_film project"
```

---

### Task 2: Config loading

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/config.py`
- Test: `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass with fields `film_profile: str`, `print_profile: str`, `output_directory: Path`, `output_bit_depth: int`; and `load_config(config_path: Path) -> Config`. Used by Task 7 (`cli.py`).

- [ ] **Step 1: Write the failing test**

```bash
mkdir -p /Users/aryakrishnagiri/Downloads/ph/photo_film/tests
touch /Users/aryakrishnagiri/Downloads/ph/photo_film/tests/__init__.py
```

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_config.py`:

```python
from pathlib import Path

from photo_film.config import load_config


def test_load_config_reads_toml(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[profiles]
film = "kodak_portra_400"
print = "kodak_portra_endura"

[output]
directory = "~/Downloads"
bit_depth = 16
"""
    )

    config = load_config(config_path)

    assert config.film_profile == "kodak_portra_400"
    assert config.print_profile == "kodak_portra_endura"
    assert config.output_directory == Path("~/Downloads").expanduser()
    assert config.output_bit_depth == 16
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'photo_film.config'`

- [ ] **Step 3: Write the implementation**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/config.py`:

```python
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    film_profile: str
    print_profile: str
    output_directory: Path
    output_bit_depth: int


def load_config(config_path: Path) -> Config:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    profiles = data["profiles"]
    output = data["output"]

    return Config(
        film_profile=profiles["film"],
        print_profile=profiles["print"],
        output_directory=Path(output["directory"]).expanduser(),
        output_bit_depth=int(output["bit_depth"]),
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_config.py -v
```

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add src/photo_film/config.py tests/test_config.py tests/__init__.py
git commit -m "Add config.toml loading"
```

---

### Task 3: Format detection and output naming

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/naming.py`
- Test: `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_naming.py`

**Interfaces:**
- Produces: `detect_format(path: Path) -> str | None` (returns `"raw"`, `"jpeg"`, `"tiff"`, or `None`), `output_path_for(input_path: Path, output_dir: Path, film_profile: str, print_profile: str) -> Path`. Used by Tasks 4, 6, 7.

- [ ] **Step 1: Write the failing test**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_naming.py`:

```python
from pathlib import Path

from photo_film.naming import detect_format, output_path_for


def test_detect_format_raw():
    assert detect_format(Path("DSCF0892.RAF")) == "raw"
    assert detect_format(Path("photo.CR2")) == "raw"
    assert detect_format(Path("photo.dng")) == "raw"


def test_detect_format_jpeg():
    assert detect_format(Path("DSCF0892.jpg")) == "jpeg"
    assert detect_format(Path("DSCF0892.JPEG")) == "jpeg"


def test_detect_format_tiff():
    assert detect_format(Path("scan.tif")) == "tiff"
    assert detect_format(Path("scan.TIFF")) == "tiff"


def test_detect_format_unsupported():
    assert detect_format(Path("notes.txt")) is None


def test_output_path_for_builds_expected_name():
    result = output_path_for(
        Path("/tmp/inbox/DSCF0892.RAF"),
        Path("/tmp/downloads"),
        "kodak_portra_400",
        "kodak_portra_endura",
    )
    assert result == Path("/tmp/downloads/DSCF0892_kodak_portra_400_kodak_portra_endura.tif")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_naming.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'photo_film.naming'`

- [ ] **Step 3: Write the implementation**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/naming.py`:

```python
from __future__ import annotations

from pathlib import Path

RAW_EXTENSIONS = {
    ".raf", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".rw2", ".orf", ".pef", ".srw",
}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
TIFF_EXTENSIONS = {".tif", ".tiff"}


def detect_format(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in RAW_EXTENSIONS:
        return "raw"
    if ext in JPEG_EXTENSIONS:
        return "jpeg"
    if ext in TIFF_EXTENSIONS:
        return "tiff"
    return None


def output_path_for(
    input_path: Path, output_dir: Path, film_profile: str, print_profile: str
) -> Path:
    stem = input_path.stem
    return output_dir / f"{stem}_{film_profile}_{print_profile}.tif"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_naming.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add src/photo_film/naming.py tests/test_naming.py
git commit -m "Add format detection and output naming"
```

---

### Task 4: Inbox scanning with skip-if-already-done

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/scanning.py`
- Test: `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_scanning.py`

**Interfaces:**
- Consumes: `detect_format`, `output_path_for` from `photo_film.naming` (Task 3).
- Produces: `ScanResult` dataclass with fields `pending: list[Path]`, `already_done: list[Path]`, `unsupported: list[Path]`; and `scan_inbox(inbox_dir: Path, output_dir: Path, film_profile: str, print_profile: str) -> ScanResult`. Used by Task 7 (`cli.py`).

- [ ] **Step 1: Write the failing test**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_scanning.py`:

```python
from pathlib import Path

from photo_film.scanning import scan_inbox


def test_scan_inbox_splits_pending_done_and_unsupported(tmp_path):
    inbox = tmp_path / "raw_inbox"
    inbox.mkdir()
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    (inbox / "new_photo.RAF").write_bytes(b"fake raw bytes")
    (inbox / "already_done.jpg").write_bytes(b"fake jpeg bytes")
    (inbox / "notes.txt").write_text("not an image")

    (output_dir / "already_done_kodak_portra_400_kodak_portra_endura.tif").write_bytes(b"fake tiff")

    result = scan_inbox(inbox, output_dir, "kodak_portra_400", "kodak_portra_endura")

    assert result.pending == [inbox / "new_photo.RAF"]
    assert result.already_done == [inbox / "already_done.jpg"]
    assert result.unsupported == [inbox / "notes.txt"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_scanning.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'photo_film.scanning'`

- [ ] **Step 3: Write the implementation**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/scanning.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from photo_film.naming import detect_format, output_path_for


@dataclass(frozen=True)
class ScanResult:
    pending: list[Path]
    already_done: list[Path]
    unsupported: list[Path]


def scan_inbox(
    inbox_dir: Path, output_dir: Path, film_profile: str, print_profile: str
) -> ScanResult:
    pending: list[Path] = []
    already_done: list[Path] = []
    unsupported: list[Path] = []

    for path in sorted(inbox_dir.iterdir()):
        if not path.is_file():
            continue

        image_format = detect_format(path)
        if image_format is None:
            unsupported.append(path)
            continue

        output_path = output_path_for(path, output_dir, film_profile, print_profile)
        if output_path.exists():
            already_done.append(path)
        else:
            pending.append(path)

    return ScanResult(pending=pending, already_done=already_done, unsupported=unsupported)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_scanning.py -v
```

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add src/photo_film/scanning.py tests/test_scanning.py
git commit -m "Add inbox scanning with skip-if-already-done"
```

---

### Task 5: Image loading wrapper

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/loading.py`
- Test: `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_loading.py`

**Interfaces:**
- Consumes: `spektrafilm.utils.io.load_image_oiio`, `spektrafilm.utils.raw_file_processor.load_and_process_raw_file` (already validated manually earlier this session).
- Produces: `load_for_simulation(path: Path, image_format: str) -> tuple[np.ndarray, str, bool]` returning `(pixels, input_color_space, input_cctf_decoding)`. Used by Task 7 (`cli.py`).

Note: the `raw`/`jpeg`/`tiff` branches call directly into spektrafilm and need a real image file to exercise meaningfully — mocking them would only test that a mock was called. Only the error branch (unknown format) is unit tested here; the real branches are verified in Task 9's end-to-end run.

- [ ] **Step 1: Write the failing test**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_loading.py`:

```python
from pathlib import Path

import pytest

from photo_film.loading import load_for_simulation


def test_load_for_simulation_rejects_unknown_format():
    with pytest.raises(ValueError):
        load_for_simulation(Path("whatever.xyz"), "unknown")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_loading.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'photo_film.loading'`

- [ ] **Step 3: Write the implementation**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/loading.py`:

```python
from __future__ import annotations

from pathlib import Path

import numpy as np

from spektrafilm.utils.io import load_image_oiio


def load_for_simulation(path: Path, image_format: str) -> tuple[np.ndarray, str, bool]:
    """Load an image and return (pixels, input_color_space, input_cctf_decoding)
    ready to feed into spektrafilm's RuntimePhotoParams.io settings."""

    if image_format == "raw":
        from spektrafilm.utils.raw_file_processor import load_and_process_raw_file

        image = load_and_process_raw_file(
            path,
            white_balance="as_shot",
            output_colorspace="ProPhoto RGB",
            output_cctf_encoding=False,
        )
        return image, "ProPhoto RGB", False

    if image_format == "jpeg":
        image = load_image_oiio(str(path))
        return image, "sRGB", True

    if image_format == "tiff":
        image = load_image_oiio(str(path))
        return image, "ProPhoto RGB", False

    raise ValueError(f"Unsupported image format: {image_format!r}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_loading.py -v
```

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add src/photo_film/loading.py tests/test_loading.py
git commit -m "Add image loading wrapper for raw/jpeg/tiff"
```

---

### Task 6: Simulation + save wrapper

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/simulate.py`

**Interfaces:**
- Consumes: `spektrafilm.init_params`, `spektrafilm.simulate`, `spektrafilm.utils.io.save_image_oiio` (already validated manually earlier this session).
- Produces: `simulate_and_save(image, input_color_space: str, input_cctf_decoding: bool, film_profile: str, print_profile: str, output_bit_depth: int, output_path: Path) -> None`. Used by Task 7 (`cli.py`).

Note: no automated test here — this wraps the actual (slow) spektrafilm simulation call with the exact neutral/natural settings already validated manually earlier in this session. It's verified for real in Task 9's end-to-end run, not mocked.

- [ ] **Step 1: Write the implementation**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/simulate.py`:

```python
from __future__ import annotations

from pathlib import Path

import numpy as np

from spektrafilm import init_params, simulate
from spektrafilm.utils.io import save_image_oiio


def simulate_and_save(
    image: np.ndarray,
    input_color_space: str,
    input_cctf_decoding: bool,
    film_profile: str,
    print_profile: str,
    output_bit_depth: int,
    output_path: Path,
) -> None:
    params = init_params(film_profile=film_profile, print_profile=print_profile)

    params.io.input_color_space = input_color_space
    params.io.input_cctf_decoding = input_cctf_decoding

    params.camera.auto_exposure = True
    params.camera.exposure_compensation_ev = 0.0

    params.enlarger.y_filter_shift = 0.0
    params.enlarger.m_filter_shift = 0.0
    params.enlarger.print_exposure = 1.0

    params.io.scan_film = False
    params.io.upscale_factor = 1.0
    params.io.output_color_space = "sRGB"
    params.io.output_cctf_encoding = True

    result = simulate(image, params)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_image_oiio(
        str(output_path),
        result,
        bit_depth=output_bit_depth,
        color_space="sRGB",
        cctf_encoding=True,
    )
```

- [ ] **Step 2: Verify it imports cleanly**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -c "from photo_film.simulate import simulate_and_save; print('ok')"
```

Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add src/photo_film/simulate.py
git commit -m "Add simulate+save wrapper with natural default settings"
```

---

### Task 7: CLI orchestration + entry point

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/cli.py`
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/process.py`
- Test: `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_cli.py`

**Interfaces:**
- Consumes: `Config`/`load_config` (Task 2), `detect_format`/`output_path_for` (Task 3), `scan_inbox`/`ScanResult` (Task 4), `load_for_simulation` (Task 5), `simulate_and_save` (Task 6).
- Produces: `run(inbox_dir: Path, config: Config, load_fn=load_for_simulation, simulate_fn=simulate_and_save) -> dict[str, int]` (summary dict with keys `processed`, `already_done`, `unsupported`, `failed`), and `main() -> None` as the process entry point. `load_fn`/`simulate_fn` are dependency-injected so tests can substitute fakes without touching spektrafilm.

- [ ] **Step 1: Write the failing test**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/tests/test_cli.py`:

```python
from pathlib import Path

from photo_film.cli import run
from photo_film.config import Config


def _fake_load(path, image_format):
    return "fake-image-array", "sRGB", True


def _fake_simulate(
    image, input_color_space, input_cctf_decoding, film_profile, print_profile,
    output_bit_depth, output_path,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"fake tiff bytes")


def test_run_processes_pending_files_and_reports_summary(tmp_path):
    inbox = tmp_path / "raw_inbox"
    inbox.mkdir()
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    (inbox / "new_photo.jpg").write_bytes(b"fake jpeg bytes")
    (inbox / "notes.txt").write_text("not an image")

    config = Config(
        film_profile="kodak_portra_400",
        print_profile="kodak_portra_endura",
        output_directory=output_dir,
        output_bit_depth=16,
    )

    summary = run(inbox, config, load_fn=_fake_load, simulate_fn=_fake_simulate)

    assert summary == {"processed": 1, "already_done": 0, "unsupported": 1, "failed": 0}
    assert (output_dir / "new_photo_kodak_portra_400_kodak_portra_endura.tif").exists()


def test_run_continues_after_one_file_fails(tmp_path):
    inbox = tmp_path / "raw_inbox"
    inbox.mkdir()
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    (inbox / "good.jpg").write_bytes(b"fake jpeg bytes")
    (inbox / "bad.jpg").write_bytes(b"fake jpeg bytes")

    def _flaky_simulate(
        image, input_color_space, input_cctf_decoding, film_profile, print_profile,
        output_bit_depth, output_path,
    ):
        if "bad" in output_path.name:
            raise RuntimeError("boom")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake tiff bytes")

    config = Config(
        film_profile="kodak_portra_400",
        print_profile="kodak_portra_endura",
        output_directory=output_dir,
        output_bit_depth=16,
    )

    summary = run(inbox, config, load_fn=_fake_load, simulate_fn=_flaky_simulate)

    assert summary == {"processed": 1, "already_done": 0, "unsupported": 0, "failed": 1}
    assert (output_dir / "good_kodak_portra_400_kodak_portra_endura.tif").exists()
    assert not (output_dir / "bad_kodak_portra_400_kodak_portra_endura.tif").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_cli.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'photo_film.cli'`

- [ ] **Step 3: Write the implementation**

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/src/photo_film/cli.py`:

```python
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from photo_film.config import Config, load_config
from photo_film.loading import load_for_simulation
from photo_film.naming import detect_format, output_path_for
from photo_film.scanning import scan_inbox
from photo_film.simulate import simulate_and_save

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INBOX_DIR = REPO_ROOT / "raw_inbox"
CONFIG_PATH = REPO_ROOT / "config.toml"


def process_file(
    path: Path,
    config: Config,
    load_fn=load_for_simulation,
    simulate_fn=simulate_and_save,
) -> Path:
    image_format = detect_format(path)
    if image_format is None:
        raise ValueError(f"Unsupported file extension: {path.suffix}")

    image, input_color_space, input_cctf_decoding = load_fn(path, image_format)
    output_path = output_path_for(
        path, config.output_directory, config.film_profile, config.print_profile
    )
    simulate_fn(
        image,
        input_color_space,
        input_cctf_decoding,
        config.film_profile,
        config.print_profile,
        config.output_bit_depth,
        output_path,
    )
    return output_path


def run(
    inbox_dir: Path,
    config: Config,
    load_fn=load_for_simulation,
    simulate_fn=simulate_and_save,
) -> dict[str, int]:
    scan = scan_inbox(
        inbox_dir, config.output_directory, config.film_profile, config.print_profile
    )

    for path in scan.unsupported:
        print(f"SKIP (unsupported format): {path.name}")

    for path in scan.already_done:
        print(f"SKIP (already processed): {path.name}")

    processed = 0
    failed = 0
    for path in scan.pending:
        try:
            output_path = process_file(path, config, load_fn=load_fn, simulate_fn=simulate_fn)
            print(f"OK: {path.name} -> {output_path}")
            processed += 1
        except Exception as exc:
            print(f"FAILED: {path.name}: {exc}")
            traceback.print_exc()
            failed += 1

    summary = {
        "processed": processed,
        "already_done": len(scan.already_done),
        "unsupported": len(scan.unsupported),
        "failed": failed,
    }
    print(
        f"\nDone. processed={summary['processed']} "
        f"already_done={summary['already_done']} "
        f"unsupported={summary['unsupported']} "
        f"failed={summary['failed']}"
    )
    return summary


def main() -> None:
    config = load_config(CONFIG_PATH)
    INBOX_DIR.mkdir(exist_ok=True)
    summary = run(INBOX_DIR, config)
    if summary["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

Create `/Users/aryakrishnagiri/Downloads/ph/photo_film/process.py`:

```python
#!/usr/bin/env python3
from photo_film.cli import main

if __name__ == "__main__":
    main()
```

```bash
chmod +x /Users/aryakrishnagiri/Downloads/ph/photo_film/process.py
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/test_cli.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Run the full test suite**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests pass (9 total across config/naming/scanning/loading/cli)

- [ ] **Step 6: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add src/photo_film/cli.py process.py tests/test_cli.py
git commit -m "Add CLI orchestration and process.py entry point"
```

---

### Task 8: setup.sh + README

**Files:**
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/setup.sh`
- Create: `/Users/aryakrishnagiri/Downloads/ph/photo_film/README.md`

**Interfaces:**
- None (docs/scaffolding only).

- [ ] **Step 1: Create `setup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

uv venv --python 3.13 .venv
uv pip install --python .venv -e ".[dev]"

echo ""
echo "Setup complete."
echo "Drop RAW/JPEG/TIFF files into raw_inbox/, then run:"
echo "  .venv/bin/python process.py"
```

```bash
chmod +x /Users/aryakrishnagiri/Downloads/ph/photo_film/setup.sh
```

- [ ] **Step 2: Create `README.md`**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
git add setup.sh README.md
git commit -m "Add setup script and README"
```

---

### Task 9: End-to-end manual verification

**Files:** none created; this task exercises the whole pipeline for real.

**Interfaces:** none — this is verification, not a new interface.

- [ ] **Step 1: Copy the already-validated JPEG into the inbox**

```bash
cp /Users/aryakrishnagiri/Downloads/ph/DSCF0892.jpg /Users/aryakrishnagiri/Downloads/ph/photo_film/raw_inbox/
```

- [ ] **Step 2: Run the processor**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python process.py
```

Expected: prints `OK: DSCF0892.jpg -> /Users/aryakrishnagiri/Downloads/DSCF0892_kodak_portra_400_kodak_portra_endura.tif`, ends with `Done. processed=1 already_done=0 unsupported=0 failed=0`

- [ ] **Step 3: Confirm the output file exists in Downloads**

```bash
ls -la /Users/aryakrishnagiri/Downloads/DSCF0892_kodak_portra_400_kodak_portra_endura.tif
```

Expected: file exists, non-trivial size (tens of MB, matching the 16-bit TIFF produced manually earlier this session)

- [ ] **Step 4: Confirm rerun-safety (skip-if-already-done)**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python process.py
```

Expected: prints `SKIP (already processed): DSCF0892.jpg`, ends with `Done. processed=0 already_done=1 unsupported=0 failed=0`

- [ ] **Step 5: If a real Fuji `.RAF` file is available, repeat steps 1-3 with it to validate the RAW code path**

```bash
cp /path/to/some_photo.RAF /Users/aryakrishnagiri/Downloads/ph/photo_film/raw_inbox/
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
.venv/bin/python process.py
```

Expected: `OK: some_photo.RAF -> ...` and the resulting TIFF opens correctly (spot check with `file <output>.tif` and/or opening it in Preview/an image viewer).

---

### Task 10: Create the private GitHub repo and push

**Files:** none.

**Interfaces:** none.

- [ ] **Step 1: Create the private repo and push**

```bash
cd /Users/aryakrishnagiri/Downloads/ph/photo_film
gh repo create photo_film --private --source=. --remote=origin --push
```

Expected: repo created under the `aryakr4` account, `origin` remote added, `main` branch pushed.

- [ ] **Step 2: Verify**

```bash
gh repo view photo_film --json name,visibility,url
```

Expected: JSON showing `"name": "photo_film"`, `"visibility": "PRIVATE"`, and a `url` you can later clone from.
