import io
import base64
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageFont

from vision.core.schemas import DetectedBean
from vision.core.detection.config import DEFAULT_JPEG_QUALITY
from vision.core.detection.labels import CLASS_COLORS

def get_annotation_style(image_size: Tuple[int, int]) -> Tuple[ImageFont.ImageFont, int]:
    w, h = image_size
    font_size = max(14, int(min(w, h) * 0.02))
    stroke_width = max(2, int(min(w, h) * 0.003))

    for font_path in (
        "arial.ttf", "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(font_path, font_size), stroke_width
        except (OSError, IOError):
            continue

    try:
        return ImageFont.load_default(size=font_size), stroke_width
    except TypeError:
        return ImageFont.load_default(), stroke_width

def annotate_image(
    pil_img: Image.Image,
    detected_beans: List[DetectedBean],
    jpeg_quality: int = DEFAULT_JPEG_QUALITY
) -> str:
    annotated = pil_img.copy()
    draw = ImageDraw.Draw(annotated)
    font, stroke_w = get_annotation_style(pil_img.size)

    for bean in detected_beans:
        coords = [bean.box.x1, bean.box.y1, bean.box.x2, bean.box.y2]
        color = CLASS_COLORS.get(bean.category, (220, 38, 38))
        draw.rectangle(coords, outline=color, width=stroke_w)

        tag = f"{bean.class_name} {bean.confidence:.0%}"
        text_bb = draw.textbbox((0, 0), tag, font=font)
        tw = text_bb[2] - text_bb[0]
        th = text_bb[3] - text_bb[1]

        lx = max(0, min(int(coords[0]), pil_img.width - tw - 6))
        ly = max(0, int(coords[1]) - th - 6)
        draw.rectangle([lx, ly, lx + tw + 6, ly + th + 4], fill=color)
        draw.text((lx + 3, ly + 2), tag, fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    annotated.save(buf, format="JPEG", quality=jpeg_quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
