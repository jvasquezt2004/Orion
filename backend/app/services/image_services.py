import asyncio
import math
from typing import Tuple

import colour
import cv2
import numpy as np
from colorthief import ColorThief

from app.core.config import config
from app.db.reference import Color, MediaKind, Reference, ReferenceType
from app.models.image_models import RGB, ColorPalette, ImageAnalysis, OkLab


class ImageServices:
    def __init__(
        self, img_path: str, original_name: str, stored_name: str, object_path: str
    ) -> None:
        self.img_path = img_path
        self.original_name = original_name
        self.stored_name = stored_name
        self.object_path = object_path
        self.image_analysis: ImageAnalysis = ImageAnalysis()

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

    def __extract_palette(self) -> list[tuple[int, int, int]]:
        color_thief = ColorThief(self.img_path)
        return color_thief.get_palette(color_count=5, quality=10)

    async def __detect_colors(self) -> None:
        palette = await asyncio.to_thread(self.__extract_palette)
        final_palette = []
        for color in palette:
            validated_color = RGB(r=color[0], g=color[1], b=color[2])
            hex_color = self.__rgb_to_hex(
                validated_color.r, validated_color.g, validated_color.b
            )
            oklab_colors = self.__rgb_to_oklab(
                validated_color.r, validated_color.g, validated_color.b
            )

            l, a, b = oklab_colors

            validated_oklab = OkLab(l=l, a=a, b=b)

            existing_color = await Color.find_one(Color.hex_code == hex_color)

            if existing_color:
                final_palette.append(
                    ColorPalette(
                        hex_code=existing_color.hex_code,
                        rgb=existing_color.rgb,
                        oklab=existing_color.oklab,
                    )
                )
                continue

            color = Color(
                hex_code=hex_color, rgb=validated_color, oklab=validated_oklab
            )
            await color.insert()

            final_palette.append(
                ColorPalette(
                    hex_code=hex_color, rgb=validated_color, oklab=validated_oklab
                )
            )

        self.image_analysis.color_palette = final_palette

    def __classify_image_temperature(self) -> None:
        self.classification: str = ""
        bgr_image = cv2.imread(self.img_path)
        if bgr_image is None:
            raise FileNotFoundError(f"Could not read image: {self.img_path}")
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

        avg_rgb = np.mean(rgb_image, axis=(0, 1)) / 255.0

        XYZ = colour.sRGB_to_XYZ(avg_rgb)

        cct, _ = colour.temperature.XYZ_to_CCT_Ohno2013(XYZ)

        if cct < 5000:
            classification = "Warm"
        elif cct <= 6500:
            classification = "Neutral"
        else:
            classification = "Cold"

        self.image_analysis.kelvin_value = cct
        self.image_analysis.temperature = classification

    async def __save_reference(self) -> None:
        await Reference(
            original_name=self.original_name,
            stored_name=self.stored_name,
            bucket=config.minio_bucket,
            object_path=self.object_path,
            is_processed=True,
            type=ReferenceType.REFERENCE,
            media=MediaKind.IMAGE,
            image_analysis=self.image_analysis,
        ).insert()

    async def __call__(self) -> None:
        await self.__detect_colors()
        self.__classify_image_temperature()
        await self.__save_reference()
