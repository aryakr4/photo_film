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
    assert result == Path("/tmp/downloads/DSCF0892_RAF_kodak_portra_400_kodak_portra_endura.tif")


def test_output_path_for_distinguishes_raw_and_jpeg_with_same_stem():
    raw_output = output_path_for(
        Path("/tmp/inbox/DSCF0892.RAF"),
        Path("/tmp/downloads"),
        "kodak_portra_400",
        "kodak_portra_endura",
    )
    jpeg_output = output_path_for(
        Path("/tmp/inbox/DSCF0892.JPG"),
        Path("/tmp/downloads"),
        "kodak_portra_400",
        "kodak_portra_endura",
    )
    assert raw_output != jpeg_output
