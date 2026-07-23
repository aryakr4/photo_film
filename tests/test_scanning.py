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

    (output_dir / "already_done_JPG_kodak_portra_400_kodak_portra_endura.tif").write_bytes(b"fake tiff")

    result = scan_inbox(inbox, output_dir, "kodak_portra_400", "kodak_portra_endura")

    assert result.pending == [inbox / "new_photo.RAF"]
    assert result.already_done == [inbox / "already_done.jpg"]
    assert result.unsupported == [inbox / "notes.txt"]
