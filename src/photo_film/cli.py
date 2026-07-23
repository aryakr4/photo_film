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
