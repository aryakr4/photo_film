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
