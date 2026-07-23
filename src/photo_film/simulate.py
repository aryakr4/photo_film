from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from spektrafilm import init_params, simulate
from spektrafilm.utils.io import save_image_oiio


def simulate_and_save(
    image: np.ndarray,
    input_color_space: str,
    input_cctf_decoding: bool,
    film_profile: str,
    print_profile: str,
    output_bit_depth: int,
    output_path: Path,
) -> None:
    params = init_params(film_profile=film_profile, print_profile=print_profile)

    params.io.input_color_space = input_color_space
    params.io.input_cctf_decoding = input_cctf_decoding

    params.camera.auto_exposure = True
    params.camera.exposure_compensation_ev = 0.0

    params.enlarger.y_filter_shift = 0.0
    params.enlarger.m_filter_shift = 0.0
    params.enlarger.print_exposure = 1.0

    params.io.scan_film = False
    params.io.upscale_factor = 1.0
    params.io.output_color_space = "sRGB"
    params.io.output_cctf_encoding = True

    result = simulate(image, params)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f".{output_path.stem}.tmp{output_path.suffix}")
    save_image_oiio(
        str(temp_path),
        result,
        bit_depth=output_bit_depth,
        color_space="sRGB",
        cctf_encoding=True,
    )
    os.replace(temp_path, output_path)
