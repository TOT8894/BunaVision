from typing import Tuple
import numpy as np
from PIL import Image, ImageOps

from vision.core.detection.config import DEFAULT_IMG_SIZE

# Letterbox metadata: (orig_w, orig_h, scale, pad_left, pad_top)
LetterboxMeta = Tuple[int, int, float, int, int]

def prepare_image(pil_img: Image.Image) -> Image.Image:
    # Rotate using EXIF orientation tags and convert to RGB
    return ImageOps.exif_transpose(pil_img).convert("RGB")

def preprocess_for_onnx(
    pil_img: Image.Image,
    target_size: int = DEFAULT_IMG_SIZE
) -> Tuple[np.ndarray, LetterboxMeta]:
    # Letterbox resize maintaining aspect ratio with neutral gray padding (114, 114, 114)
    orig_w, orig_h = pil_img.size
    scale = min(target_size / orig_w, target_size / orig_h)
    new_w = int(round(orig_w * scale))
    new_h = int(round(orig_h * scale))

    pad_left = (target_size - new_w) // 2
    pad_top = (target_size - new_h) // 2

    resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (target_size, target_size), color=(114, 114, 114))
    canvas.paste(resized, (pad_left, pad_top))

    img_arr = np.array(canvas, dtype=np.float32) / 255.0
    tensor = np.expand_dims(img_arr.transpose(2, 0, 1), axis=0)
    meta: LetterboxMeta = (orig_w, orig_h, scale, pad_left, pad_top)

    return tensor, meta
