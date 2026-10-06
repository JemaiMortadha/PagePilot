"""
publisher.py — Publish a composed image to your Facebook Page via Graph API.
Completely free; uses your own Page Access Token.

Endpoint used: POST /{page-id}/photos
  → publishes the image directly to the page timeline.
"""
import logging
import mimetypes
from pathlib import Path
from typing import Optional

import requests

import config

log = logging.getLogger(__name__)

FB_API_BASE = "https://graph.facebook.com/v19.0"


def publish_to_facebook(
    image_path: Path,
    caption: str,
) -> Optional[str]:
    """
    Upload an image to the Facebook Page and publish it with a caption.
    Uses the 2-step method to guarantee it appears on the main timeline feed
    (fixing the issue where New Pages Experience hides them in the Photos tab).

    Returns the new post ID string on success, or None on failure.
    """
    if not config.FB_PAGE_ACCESS_TOKEN:
        raise ValueError("FB_PAGE_ACCESS_TOKEN is not set in .env")
    if not config.FB_PAGE_ID:
        raise ValueError("FB_PAGE_ID is not set in .env")

    # Step 1: Upload the photo (unpublished) to get a photo ID
    url_photos = f"{FB_API_BASE}/{config.FB_PAGE_ID}/photos"
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if mime_type is None:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as f:
        files = {"source": (image_path.name, f, mime_type)}
        data_upload = {
            "access_token": config.FB_PAGE_ACCESS_TOKEN,
            "published": "false",
        }
        try:
            resp1 = requests.post(url_photos, files=files, data=data_upload, timeout=60)
            resp1.raise_for_status()
            photo_id = resp1.json().get("id")
            if not photo_id:
                log.error("Failed to get photo ID from upload response.")
                return None
        except Exception as e:
            log.error(f"Failed to upload photo (step 1): {e}")
            return None

    # Step 2: Publish a feed post with the photo attached
    import json
    url_feed = f"{FB_API_BASE}/{config.FB_PAGE_ID}/feed"
    data_feed = {
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
        "message": caption,
        "attached_media": json.dumps([{"media_fbid": photo_id}])
    }
    
    try:
        resp2 = requests.post(url_feed, data=data_feed, timeout=60)
        resp2.raise_for_status()
        post_id = resp2.json().get("id")
        log.info(f"Published to Facebook Feed ✓  post_id={post_id}")
        return post_id
    except requests.HTTPError as e:
        log.error(f"Facebook API error on step 2: {e.response.status_code} — {e.response.text}")
    except Exception as e:
        log.error(f"Publish step 2 failed: {e}")

    return None
