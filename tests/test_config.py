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
