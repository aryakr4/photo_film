from pathlib import Path

import pytest

from photo_film.loading import load_for_simulation


def test_load_for_simulation_rejects_unknown_format():
    with pytest.raises(ValueError):
        load_for_simulation(Path("whatever.xyz"), "unknown")
