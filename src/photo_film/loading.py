from __future__ import annotations

from pathlib import Path

import numpy as np

from spektrafilm.utils.io import load_image_oiio


def load_for_simulation(path: Path, image_format: str) -> tuple[np.ndarray, str, bool]:
    """Load an image and return (pixels, input_color_space, input_cctf_decoding)
    ready to feed into spektrafilm's RuntimePhotoParams.io settings."""

    if image_format == "raw":
        from spektrafilm.utils.raw_file_processor import load_and_process_raw_file

        image = load_and_process_raw_file(
            path,
            white_balance="as_shot",
            output_colorspace="ProPhoto RGB",
            output_cctf_encoding=False,
        )
        return image, "ProPhoto RGB", False

    if image_format == "jpeg":
        image = load_image_oiio(str(path))
        return image, "sRGB", True

    if image_format == "tiff":
        image = load_image_oiio(str(path))
        return image, "ProPhoto RGB", False

    raise ValueError(f"Unsupported image format: {image_format!r}")
