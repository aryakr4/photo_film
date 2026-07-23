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


VALID_BIT_DEPTHS = {8, 16, 32}


def load_config(config_path: Path) -> Config:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    profiles = data["profiles"]
    output = data["output"]

    bit_depth = int(output["bit_depth"])
    if bit_depth not in VALID_BIT_DEPTHS:
        raise ValueError(
            f"output.bit_depth must be one of {sorted(VALID_BIT_DEPTHS)}, got {bit_depth}"
        )

    return Config(
        film_profile=profiles["film"],
        print_profile=profiles["print"],
        output_directory=Path(output["directory"]).expanduser(),
        output_bit_depth=bit_depth,
    )
