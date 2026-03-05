# utils/image_generator.py

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

from core.config import TEMPLATE_PATH
from utils.logger import logger


COLOR_TINTA = "#0B1E38"


def generate_generic_image(text_lines, footer_text=""):
    """
    Genera una imagen con texto sobre la plantilla base.
    
    Args:
        text_lines: Lista de tuplas (texto, y_position)
        footer_text: Texto opcional para el footer
    """
    try:
        if not os.path.exists(TEMPLATE_PATH):
            logger.error(f"ERROR: No se encuentra la plantilla en: {TEMPLATE_PATH}")
            return None

        img = Image.open(TEMPLATE_PATH).convert("RGBA")
        W, H = img.size
    except Exception as e:
        logger.error(f"Error al abrir la imagen plantilla: {e}")
        return None

    draw = ImageDraw.Draw(img)

    try:
        font_path = "arial.ttf" if os.name == 'nt' else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_lg = ImageFont.truetype(font_path, int(H * 0.032))
        font_sm = ImageFont.truetype(font_path, int(H * 0.021))
    except OSError:
        font_lg = font_sm = ImageFont.load_default()

    for text, y_pos in text_lines:
        draw.text((W / 2, y_pos), text, fill=COLOR_TINTA, anchor="mm", font=font_lg)

    if footer_text:
        footer_y = H * 0.77
        draw.text((W / 2, footer_y), footer_text, fill=COLOR_TINTA, anchor="mm", font=font_sm)

    bio = io.BytesIO()
    img_rgb = img.convert('RGB')
    img_rgb.save(bio, 'JPEG', quality=85, optimize=True)
    bio.seek(0)

    size_kb = len(bio.getvalue()) / 1024
    logger.info(f"Imagen generada: {size_kb:.1f} KB")

    return bio
