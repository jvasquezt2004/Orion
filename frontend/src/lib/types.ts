export type ColorPaletteEntry = {
  hex_code: string
  rgb: { r: number; g: number; b: number }
  oklab: { l: number; a: number; b: number }
}

export type ImageAnalysis = {
  color_palette: Array<ColorPaletteEntry>
  mean_luminance: number | null
  kelvin_value: number | null
  temperature: string | null
  visual_density: string | null
}

export type Reference = {
  id: string
  type: string
  media: string
  original_name: string
  stored_name: string
  object_path: string
  bucket: string
  is_processed: boolean
  created_at: string
  description: string | null
  title: string | null
  thumbnail_url: string | null
  content_type: string | null
  original_url: string | null
  final_url: string | null
  provider: string | null
  embed_url: string | null
  image_analysis: ImageAnalysis | null
}
