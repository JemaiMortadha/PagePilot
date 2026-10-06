"""
image_composer.py — Generate a background image via Pollinations.ai (free, no key)
then composite the rewritten text onto it in the exact style of style.jpeg.

Style analysis of style.jpeg:
  • Dark teal/space background with glowing 3D scientific illustration
  • Circular inset image (top-right corner)
  • Topic tag pill (white bg, bold black uppercase text) — middle-left
  • Headline text block at bottom (~40% of image height):
      - Key phrase in BOLD YELLOW
      - Rest of words in BOLD WHITE
  • Small "FOLLOW @PageName" footer in white/grey
  • Thin yellow/gold border around the entire image
"""
import io
import logging
import os
import textwrap
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config

log = logging.getLogger(__name__)

# ── Colour palette (from style.jpeg) ────────────────────────
CLR_BG_OVERLAY        = (0, 20, 30, 200)   # dark teal overlay on bottom third
CLR_YELLOW            = (255, 210, 0)       # headline accent yellow
CLR_WHITE             = (255, 255, 255)
CLR_TAG_BG            = (255, 255, 255)
CLR_TAG_TEXT          = (0, 0, 0)
CLR_BORDER            = (180, 150, 0)      # gold border
CLR_FOOTER            = (255, 255, 255)  # white — clean and sharp on dark band
CLR_SHADOW            = (0, 0, 0, 160)
# Colour sampled from Pollinations.ai watermark background (dark near-black teal)
CLR_COVER_BAND        = (9, 18, 25)        # covers the Pollinations watermark

BORDER_PX   = 8
TAG_PAD     = 12                            # padding inside topic tag pill
TAG_RADIUS  = 6

W = config.IMAGE_WIDTH
H = config.IMAGE_HEIGHT

# ── Font loading ─────────────────────────────────────────────
def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font; fall back gracefully if not found."""
    candidates = []
    if bold:
        candidates = [
            config.FONTS_DIR / "Roboto-Black.ttf",
            config.FONTS_DIR / "Roboto-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        ]
    else:
        candidates = [
            config.FONTS_DIR / "Roboto-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            continue
    return ImageFont.load_default()


# ── Pollinations.ai download ─────────────────────────────────
def _generate_background(prompt: str, retries: int = 3) -> Optional[Image.Image]:
    """
    Request an image from Pollinations.ai (completely free, no API key).
    Returns a PIL Image or None on failure.
    """
    encoded = urllib.parse.quote(prompt)
    url = config.POLLINATIONS_URL.format(
        prompt=encoded, w=W, h=H
    )
    log.info(f"Generating background via Pollinations.ai…")
    log.debug(f"URL: {url}")

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            img = img.resize((W, H), Image.LANCZOS)
            log.info("Background image generated ✓")
            return img
        except Exception as e:
            log.warning(f"Pollinations attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return None


# ── Text splitting: first ~40% yellow, rest white ────────────
def _split_headline(text: str) -> tuple[str, str]:
    """
    Split the headline so roughly the first meaningful phrase is yellow
    and the remainder is white — mimicking the style.jpeg pattern.
    """
    words = text.split()
    # Try to break after ~35-45% of words, but at a natural word boundary
    split_at = max(2, len(words) * 2 // 5)
    yellow_part = " ".join(words[:split_at])
    white_part  = " ".join(words[split_at:])
    return yellow_part, white_part


# ── Draw wrapped mixed-colour headline ───────────────────────
def _draw_mixed_text(
    draw: ImageDraw.ImageDraw,
    text_yellow: str,
    text_white: str,
    font: ImageFont.FreeTypeFont,
    x: int, y: int, max_width: int,
    line_spacing: int = 8,
) -> int:
    """
    Draws yellow then white text as a continuous block, word-wrapped.
    Returns the Y position after the last line.
    """
    # Wrap the full combined text
    full_text = f"{text_yellow} {text_white}".strip()
    avg_char_w = font.getbbox("A")[2]
    chars_per_line = max(10, max_width // avg_char_w)
    lines = textwrap.wrap(full_text, width=chars_per_line)

    yellow_words = set(text_yellow.upper().split())
    cur_y = y

    for line in lines:
        words = line.split()
        cur_x = x
        line_h = font.getbbox(line)[3] - font.getbbox(line)[1]

        for word in words:
            # Draw shadow
            clean = word.upper()
            draw.text((cur_x + 2, cur_y + 2), clean + " ", font=font,
                      fill=(0, 0, 0, 160))
            # Colour: yellow if word is in the yellow section, else white
            colour = CLR_YELLOW if clean.rstrip(".,!?:;") in yellow_words else CLR_WHITE
            draw.text((cur_x, cur_y), clean + " ", font=font, fill=colour)
            cur_x += font.getbbox(clean + " ")[2]

        cur_y += line_h + line_spacing

    return cur_y


# ── Draw the topic tag pill ───────────────────────────────────
def _draw_tag(draw: ImageDraw.ImageDraw, tag: str, font: ImageFont.FreeTypeFont,
              x: int, y: int) -> None:
    bbox  = font.getbbox(tag)
    # bbox = (left, top, right, bottom) — top offset can be > 0 for many fonts
    bx0, by0, bx1, by1 = bbox
    tw = bx1 - bx0
    th = by1 - by0
    rx0 = x
    ry0 = y
    rx1 = x + tw + TAG_PAD * 2
    ry1 = y + th + TAG_PAD
    draw.rounded_rectangle([(rx0, ry0), (rx1, ry1)], radius=TAG_RADIUS,
                            fill=CLR_TAG_BG)
    # Vertically centre by subtracting the font's top offset (by0)
    text_x = rx0 + TAG_PAD
    text_y = ry0 + TAG_PAD // 2 - by0
    draw.text((text_x, text_y), tag, font=font, fill=CLR_TAG_TEXT)


# ── Main composer ─────────────────────────────────────────────
def compose_image(
    image_prompt: str,
    rewritten_text: str,
    topic_tag: str,
    page_name: str = config.PAGE_NAME,
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """
    Full pipeline:
      1. Generate background (Pollinations.ai)
      2. Apply dark overlay on the bottom ~45%
      3. Draw topic tag, headline, footer watermark, border
      4. Save and return the path

    Returns the path to the saved image, or None on failure.
    """
    # 1. Generate background
    bg = _generate_background(image_prompt)
    if bg is None:
        log.error("Could not generate background image")
        return None

    # 2. Convert to RGBA for compositing
    canvas = bg.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # Dark gradient overlay on bottom 48% of image
    overlay_top = int(H * 0.52)
    draw_ov.rectangle(
        [(0, overlay_top), (W, H)],
        fill=(0, 15, 25, 220),
    )
    # Softer gradient just above the text block
    for i in range(80):
        alpha = int(220 * i / 80)
        draw_ov.rectangle(
            [(0, overlay_top - 80 + i), (W, overlay_top - 79 + i)],
            fill=(0, 15, 25, alpha),
        )

    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # ── 3. Load fonts ───────────────────────────────────────
    font_headline = _get_font(62, bold=True)
    font_tag      = _get_font(30, bold=True)
    font_footer   = _get_font(24, bold=False)

    # ── 4. Topic tag (positioned ~52% down, left side) ──────
    tag_x = BORDER_PX + 28
    tag_y = int(H * 0.52) + 26
    _draw_tag(draw, topic_tag, font_tag, tag_x, tag_y)

    # ── 5. Headline ─────────────────────────────────────────
    yellow_part, white_part = _split_headline(rewritten_text)
    text_x     = BORDER_PX + 28
    text_y     = tag_y + 60
    text_width = W - BORDER_PX * 2 - 56

    # Dynamically scale font down if it overflows
    font_size = 62
    font_headline = _get_font(font_size, bold=True)
    
    # Calculate height before drawing
    def _measure_text_y():
        full_text = f"{yellow_part} {white_part}".strip()
        avg_char_w = font_headline.getbbox("A")[2]
        chars_per_line = max(10, text_width // avg_char_w)
        lines = __import__('textwrap').wrap(full_text, width=chars_per_line)
        cur_y = text_y
        for line in lines:
            line_h = font_headline.getbbox(line)[3] - font_headline.getbbox(line)[1]
            cur_y += line_h + 10
        return cur_y

    while font_size > 20 and _measure_text_y() > H - BORDER_PX - 80:
        font_size -= 4
        font_headline = _get_font(font_size, bold=True)

    end_y = _draw_mixed_text(
        draw, yellow_part, white_part,
        font_headline,
        text_x, text_y, text_width,
        line_spacing=10,
    )

    # ── 6. Cover band — hides Pollinations.ai watermark ─────
    # Pollinations places a small watermark in the bottom-right corner.
    # We paint a full-width solid band over the bottom 70px using the exact
    # same background colour so the watermark becomes invisible, and gives
    # the footer text more room to sit higher up.
    COVER_H = 70  # px
    draw.rectangle(
        [(0, H - COVER_H), (W, H)],
        fill=CLR_COVER_BAND,
    )

    # ── 7. Footer watermark (drawn ON TOP of the cover band) ─
    footer_text = f"FOLLOW @{page_name}"
    fw = draw.textlength(footer_text, font=font_footer)
    # Centre the footer vertically within the cover band
    footer_y = H - COVER_H + (COVER_H - 24) // 2
    draw.text(
        ((W - fw) // 2, footer_y),
        footer_text,
        font=font_footer,
        fill=CLR_FOOTER,
    )

    # ── 8. Gold border ───────────────────────────────────────
    draw.rectangle(
        [(BORDER_PX // 2, BORDER_PX // 2),
         (W - BORDER_PX // 2, H - BORDER_PX // 2)],
        outline=CLR_BORDER, width=BORDER_PX,
    )

    # ── 8. Save ──────────────────────────────────────────────
    final = canvas.convert("RGB")
    if output_path is None:
        ts = int(time.time())
        output_path = config.OUTPUT_DIR / f"post_{ts}.jpg"

    final.save(str(output_path), "JPEG", quality=95)
    log.info(f"Composed image saved → {output_path}")
    return output_path
