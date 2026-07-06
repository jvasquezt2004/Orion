from typing import List, Optional

from pydantic import BaseModel


class RGB(BaseModel):
    r: int
    g: int
    b: int


class OkLab(BaseModel):
    l: float
    a: float
    b: float


class ColorPalette(BaseModel):
    hex_code: str
    rgb: RGB
    oklab: OkLab


class ImageAnalysis(BaseModel):
    color_palette: List[ColorPalette] = []
    mean_luminance: Optional[float] = None
    kelvin_value: float = 0.0
    temperature: str = ""
    visual_density: Optional[str] = None
