"""
scraper.py — Monitor competitor Facebook pages for new image posts
Uses Apify's Facebook Posts Scraper (free $5/mo credits).
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from apify_client import ApifyClient

import config

log = logging.getLogger(__name__)


def _load_seen() -> dict:
    """Load the deduplication cache from disk."""
    if config.CACHE_FILE.exists():
        try:
            return json.loads(config.CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_seen(seen: dict) -> None:
    """Persist the deduplication cache."""
    config.CACHE_FILE.write_text(json.dumps(seen, indent=2))


def mark_post_seen(page_url: str, post_id: str) -> None:
    """
    Called by main.py AFTER a post is successfully published.
    Stores the latest processed post ID specifically for this page.
    """
    seen = _load_seen()
    
    # We store BOTH the post_id (for global dedup) AND the page URL (so we know the last post per page)
    seen[post_id] = datetime.now(timezone.utc).isoformat()
    seen[f"last_post_{page_url}"] = post_id
    
    _save_seen(seen)


def _is_new(page_url: str, post_id: str, seen: dict) -> bool:
    """Return True if this post has not been processed recently."""
    # If we already processed this exact post globally
    if post_id in seen:
        return False
        
    # If this post happens to be the EXACT last post we processed for this page
    if seen.get(f"last_post_{page_url}") == post_id:
        return False
        
    return True


def fetch_new_image_posts() -> list[dict]:
    """
    Scrape all competitor pages and return a list of NEW posts that contain
    at least one image.
    """
    if not config.APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN is not set in .env")

    client = ApifyClient(config.APIFY_API_TOKEN)
    seen   = _load_seen()
    new_posts: list[dict] = []

    for page_url in config.COMPETITOR_PAGES:
        log.info(f"Scraping: {page_url}")
        try:
            run_input = {
                "startUrls": [{"url": page_url}],
                "resultsLimit": config.POSTS_TO_CHECK,
                "scrapeAbout": False,
                "scrapeReviews": False,
                "scrapeServices": False,
                "scrapePosts": True,
            }

            run = client.actor("apify/facebook-posts-scraper").call(run_input=run_input)
            if run is None:
                log.error(f"Actor run returned None for {page_url}")
                continue
                
            if isinstance(run, dict):
                dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")
            else:
                dataset_id = run.default_dataset_id
                
            if not dataset_id:
                log.error(f"Could not get dataset ID for {page_url}")
                continue
                
            dataset = client.dataset(dataset_id)
            
            # We want to process only the newest unseen posts.
            # Apify returns them roughly newest-first. We collect all unseen ones.
            page_new_posts = []

            for item in dataset.iterate_items():
                post_id   = str(item.get("postId") or item.get("id", ""))
                media     = item.get("media") or []
                caption   = item.get("text") or item.get("message") or ""
                posted_at = item.get("time") or item.get("timestamp") or ""

                if not media:
                    continue

                img_url = ""
                first = media[0]
                if isinstance(first, dict):
                    photo_image = first.get("photo_image") or {}
                    img_url = (
                        photo_image.get("uri")
                        or first.get("thumbnail")
                        or ""
                    )
                    typename = first.get("__typename", "Photo")
                    if typename not in ("Photo", ""):
                        continue
                else:
                    img_url = str(first)

                if not img_url or not img_url.startswith("http"):
                    continue

                if _is_new(page_url, post_id, seen):
                    page_new_posts.append({
                        "post_id":   post_id,
                        "page_url":  page_url,
                        "image_url": img_url,
                        "caption":   caption,
                        "posted_at": posted_at,
                    })
            
            # Add this page's new posts to the global list
            # We process them from oldest to newest (by reversing) so that if there are 2 new posts,
            # we publish the older one first, then the newer one.
            new_posts.extend(reversed(page_new_posts))

        except Exception as e:
            log.error(f"Failed to scrape {page_url}: {e}")

    # Notice we DO NOT save 'seen' here anymore.
    # We wait for main.py to successfully publish them, then main.py calls mark_post_seen().

    log.info(f"Found {len(new_posts)} new image post(s)")
    return new_posts
