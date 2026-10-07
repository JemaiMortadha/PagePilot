"""
ai_processor.py — OCR + AI content reformulation using Gemini 2.5 Flash (free tier).

Steps for each post:
 1. Download the competitor's image
 2. Send it to Gemini Vision → extract all visible text
 3. Ask Gemini to rewrite the text: simple, clear, engaging
 4. Ask Gemini to generate a visual image-generation prompt (background only)
 5. Return structured result
"""
import io
import logging
import re
import urllib.request
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

import config

log = logging.getLogger(__name__)

# ── Initialise Gemini (new google-genai SDK) ─────────────────
_client = genai.Client(api_key=config.GEMINI_API_KEY)
GEMINI_MODEL = "gemini-3.5-flash-lite"   # Using lite version for higher free-tier limits


# ── Universal style prompt (matches style.jpeg) ──────────────
UNIVERSAL_STYLE_SUFFIX = (
    "ultra-realistic digital art, dark deep teal space-like background with subtle "
    "bokeh light particles, 3D translucent glowing subject as the central focus, "
    "vibrant cyan and gold accent lighting, cinematic quality, highly detailed, "
    "4K, professional infographic style, portrait orientation 4:5, "
    "smooth gradient overlay at the bottom third for text placement, "
    "no text in the image, no watermarks"
)

# ── System instructions ──────────────────────────────────────
REWRITE_SYSTEM = (
    "You are an expert social-media content writer for a knowledge page "
    "(facts, history, science, psychology, engineering, stories). "
    "Rewrite the given text so that: it is simple and clear for everyone, "
    "sounds original, is engaging and shareable, keeps the core fact intact, "
    "and the ENTIRE text is extremely concise (STRICTLY under 25 words total). Do NOT include any body paragraphs, just the main engaging fact. "
    "Output ONLY the rewritten text — no explanations, no formatting, no quotes."
)

IMAGE_PROMPT_SYSTEM = (
    "You are an AI art director for an educational social-media page. "
    "Given a knowledge fact, generate a vivid descriptive image-generation prompt "
    "for the BACKGROUND ILLUSTRATION ONLY (no text in the image). "
    "The subject must visually represent the SPECIFIC topic of the fact (e.g., if it's about bone broth, feature a glowing cup of broth; if it's about space, feature planets, etc). "
    "Describe this central subject clearly. Keep it under 60 words. "
    "Output ONLY the image prompt — no explanations."
)


def _download_image(url: str) -> Optional[Image.Image]:
    """Download an image from a URL and return a PIL Image."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        log.error(f"Failed to download image {url}: {e}")
        return None


def _pil_to_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


import time

def _gemini_vision(image: Image.Image, prompt: str) -> str:
    """Send image + prompt to Gemini Vision, return text response with retry."""
    time.sleep(15)  # Enforce hard rate limit spacing
    img_bytes = _pil_to_bytes(image)
    for attempt in range(10):
        try:
            response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
            )
            import quota_tracker
            quota_tracker.record_gemini_calls(1)
            return response.text.strip()
        except Exception as e:
            from google.genai.errors import APIError
            is_rate_limit = False
            if isinstance(e, APIError) and (e.code == 429 or e.code == 503):
                is_rate_limit = True
            elif "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "503" in str(e):
                is_rate_limit = True
            
            if is_rate_limit:
                log.warning(f"Gemini rate limit or overload. Waiting 60s...")
                time.sleep(60)
            else:
                raise e
    raise Exception("Gemini vision failed after 10 retries due to rate limits.")


def _gemini_text(system: str, user: str) -> str:
    """Send a text-only prompt to Gemini, return response with retry."""
    time.sleep(15)  # Enforce hard rate limit spacing
    for attempt in range(10):
        try:
            response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{system}\n\n{user}" if system else user,
            )
            import quota_tracker
            quota_tracker.record_gemini_calls(1)
            return response.text.strip()
        except Exception as e:
            from google.genai.errors import APIError
            is_rate_limit = False
            if isinstance(e, APIError) and (e.code == 429 or e.code == 503):
                is_rate_limit = True
            elif "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "503" in str(e):
                is_rate_limit = True
            
            if is_rate_limit:
                log.warning(f"Gemini rate limit or overload. Waiting 60s...")
                time.sleep(60)
            else:
                raise e
    raise Exception("Gemini text failed after 10 retries due to rate limits.")


def process_post(post: dict) -> Optional[dict]:
    """
    Full pipeline for one post:
      post → OCR → rewrite → image prompt
    Returns dict with original_text, rewritten_text, image_prompt, topic_tag
    or None on failure.
    """
    log.info(f"Processing post {post['post_id']}")

    # 1. Download competitor image
    img = _download_image(post["image_url"])
    if img is None:
        return None

    # 2. OCR — extract text from the image
    try:
        ocr_prompt = (
            "Extract ALL visible text from this image exactly as it appears. "
            "Include headlines, body text, captions, and any labels. "
            "Return only the raw text, nothing else."
        )
        original_text = _gemini_vision(img, ocr_prompt)
        log.debug(f"OCR result: {original_text[:120]}…")
    except Exception as e:
        log.error(f"Gemini OCR failed: {e}")
        return None

    # Use caption as fallback if image text is sparse
    combined_source = original_text
    if post.get("caption") and len(post["caption"]) > len(original_text):
        combined_source = post["caption"]

    if len(combined_source.strip()) < 10:
        log.warning("Extracted text too short, skipping post")
        return None

    # 3. Detect topic tag
    try:
        tag_prompt = (
            f"Based on this content, choose ONE topic tag from: "
            f"HEALTH, SCIENCE, HISTORY, PSYCHOLOGY, ENGINEERING, NATURE, SPACE, RANDOM FACT, STORY.\n\n"
            f"Content: {combined_source}\n\n"
            f"Reply with ONLY the tag word(s), nothing else."
        )
        topic_tag = _gemini_text("", tag_prompt).upper().strip()
        topic_tag = re.sub(r"[^A-Z ]", "", topic_tag)[:20]
    except Exception:
        topic_tag = "FACT"

    # 4. Rewrite the content
    try:
        rewritten_text = _gemini_text(REWRITE_SYSTEM, combined_source)
        log.debug(f"Rewritten: {rewritten_text[:120]}…")
    except Exception as e:
        log.error(f"Gemini rewrite failed: {e}")
        return None

    # 5. Generate image background prompt
    try:
        raw_img_prompt = _gemini_text(IMAGE_PROMPT_SYSTEM, rewritten_text)
        full_image_prompt = f"{raw_img_prompt}, {UNIVERSAL_STYLE_SUFFIX}"
        log.debug(f"Image prompt: {full_image_prompt[:120]}…")
    except Exception as e:
        log.error(f"Gemini image prompt failed: {e}")
        return None

    return {
        "original_text":  original_text,
        "rewritten_text": rewritten_text,
        "image_prompt":   full_image_prompt,
        "topic_tag":      topic_tag,
    }
