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
    ext_tag = input_path.suffix.lstrip(".").upper()
    return output_dir / f"{stem}_{ext_tag}_{film_profile}_{print_profile}.tif"
