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
