"""
scraper.py — Monitor competitor Facebook pages for new image posts.
Uses Apify's Facebook Posts Scraper (free $5/mo credits, batched).
All 8 competitor pages are scraped in a single Apify run to maximize quota efficiency.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from apify_client import ApifyClient

import config

log = logging.getLogger(__name__)

# Phrases that indicate Apify free tier is exhausted for the month
APIFY_LIMIT_PHRASES = [
    "monthly usage hard limit exceeded",
    "usage limit",
    "hard limit",
    "payment required",
]


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
    seen[post_id] = datetime.now(timezone.utc).isoformat()
    seen[f"last_post_{page_url}"] = post_id
    _save_seen(seen)


def _is_new(page_url: str, post_id: str, seen: dict) -> bool:
    """Return True if this post has not been processed before."""
    if post_id in seen:
        return False
    if seen.get(f"last_post_{page_url}") == post_id:
        return False
    return True


def fetch_new_image_posts() -> list[dict]:
    """
    Scrape all competitor pages in a single batched Apify run.
    Returns a list of new image posts found across all pages.
    """
    if not config.APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN is not set in .env")

    client = ApifyClient(config.APIFY_API_TOKEN)
    seen = _load_seen()
    new_posts: list[dict] = []

    start_urls = [{"url": url} for url in config.COMPETITOR_PAGES]
    log.info(f"Scraping {len(start_urls)} competitor pages in a single batch run...")

    try:
        run_input = {
            "startUrls": start_urls,
            "resultsLimit": config.POSTS_TO_CHECK,  # Apify applies this PER PAGE
            "scrapeAbout": False,
            "scrapeReviews": False,
            "scrapeServices": False,
            "scrapePosts": True,
        }

        # Use call() which synchronously starts and waits for the run.
        # This prevents double-billing!
        log.info("Starting Apify run and waiting for results...")
        try:
            run = client.actor("apify/facebook-posts-scraper").call(run_input=run_input)
        except KeyboardInterrupt:
            log.warning("Interrupted! Note: The Apify run may still be processing in the background.")
            raise  # Re-raise so main loop handles the exit cleanly

        if run is None:
            log.error("Actor run returned None.")
            return new_posts

        if isinstance(run, dict):
            dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")
        else:
            dataset_id = run.default_dataset_id

        if not dataset_id:
            log.error("Could not get dataset ID from Apify run.")
            return new_posts

        dataset = client.dataset(dataset_id)

        for item in dataset.iterate_items():
            post_id   = str(item.get("postId") or item.get("id", ""))
            page_url  = item.get("pageUrl") or item.get("url", "").split("/posts/")[0]
            media     = item.get("media") or []
            caption   = item.get("text") or item.get("message") or ""
            posted_at = item.get("time") or item.get("timestamp") or ""

            if not media:
                continue

            img_url = ""
            first = media[0]
            if isinstance(first, dict):
                photo_image = first.get("photo_image") or {}
                img_url = photo_image.get("uri") or first.get("thumbnail") or ""
                typename = first.get("__typename", "Photo")
                if typename not in ("Photo", ""):
                    continue
            else:
                img_url = str(first)

            if not img_url or not img_url.startswith("http"):
                continue

            if not page_url.startswith("http"):
                author = item.get("author", {})
                if isinstance(author, dict) and author.get("url"):
                    page_url = author.get("url").split("?")[0]
                else:
                    page_url = "unknown_page"

            if _is_new(page_url, post_id, seen):
                new_posts.append({
                    "post_id":   post_id,
                    "page_url":  page_url,
                    "image_url": img_url,
                    "caption":   caption,
                    "posted_at": posted_at,
                })

        new_posts.reverse()

    except Exception as e:
        error_str = str(e).lower()
        if any(phrase in error_str for phrase in APIFY_LIMIT_PHRASES):
            log.warning(
                "⚠️  Apify monthly free-tier limit reached. "
                "The pipeline will resume automatically when credits reset on the 1st of next month."
            )
        else:
            log.error(f"Scrape failed: {e}")

    log.info(f"Found {len(new_posts)} new image post(s)")
    return new_posts
