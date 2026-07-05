import math
from os.path import exists
from typing import Tuple

import cv2
from attrs import validate
from colorthief import ColorThief
from PIL.ImageQt import rgb

from app.models.image_models import RGB, OkLab, PaletteColor


class ImageServices:
    def __init__(self, img_path) -> None:
        self.img_path = img_path

    def __rgb_to_oklab(
        self, r: float, g: float, b: float
    ) -> Tuple[float, float, float]:
        rgb_linear = [
            c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            for c in (r, g, b)
        ]
        M1 = (
            (0.4122214708, 0.5363325363, 0.0514459929),
            (0.2119034982, 0.6806995451, 0.1073969566),
            (0.0883024619, 0.2817188376, 0.6299787005),
        )
        lms = [sum(m * c for m, c in zip(row, rgb_linear)) for row in M1]
        lms_cube = [math.cbrt(val) for val in lms]

        M2 = (
            (0.2104542553, 0.7936177850, -0.0040720468),
            (1.9779984951, -2.4285922050, 0.4505937099),
            (0.2225045907, -0.9416262698, 0.7191216791),
        )

        l, a, b = (sum(m * c for m, c in zip(row, lms_cube)) for row in M2)

        return l, a, b

    def __rgb_to_hex(self, r, g, b) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    async def detect_colors(self) -> None:
        color_thief = ColorThief(self.img_path)
        palette = color_thief.get_palette(color_count=5, quality=1)
        for color in palette:
            validated_color = RGB(rgb=color)
            hex_color = self.__rgb_to_hex(
                validated_color.rgb[0], validated_color.rgb[1], validated_color.rgb[2]
            )
            oklab_colors = self.__rgb_to_oklab(
                validated_color.rgb[0], validated_color.rgb[1], validated_color.rgb[2]
            )
