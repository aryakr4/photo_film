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
    assert (output_dir / "new_photo_JPG_kodak_portra_400_kodak_portra_endura.tif").exists()


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
    assert (output_dir / "good_JPG_kodak_portra_400_kodak_portra_endura.tif").exists()
    assert not (output_dir / "bad_JPG_kodak_portra_400_kodak_portra_endura.tif").exists()
