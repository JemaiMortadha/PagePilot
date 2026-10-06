"""
main.py — Orchestrator for the FB Page Automation pipeline.

Full flow:
  1. Scrape competitor pages → new image posts   (scraper.py)
  2. OCR + AI rewrite + image prompt generation  (ai_processor.py)
  3. Generate & compose final image              (image_composer.py)
  4. Publish to your Facebook page               (publisher.py)

Run manually:   python3 main.py
(Runs continuously checking every hour)
"""
import logging
import sys
import time
import traceback
from pathlib import Path

from config import OUTPUT_DIR, PAGE_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/automation.log", mode="a"),
    ],
)

log = logging.getLogger("main")

# Ensure log directory exists
Path("logs").mkdir(exist_ok=True)


def run_pipeline() -> None:
    # ── Import here so logging is configured first ────────────
    from scraper        import fetch_new_image_posts, mark_post_seen
    from ai_processor   import process_post
    from image_composer import compose_image
    from publisher      import publish_to_facebook

    log.info("=" * 60)
    log.info("FB Page Automation — checking for new posts")
    log.info("=" * 60)

    # ── Step 1: Scrape ───────────────────────────────────────
    try:
        posts = fetch_new_image_posts()
    except Exception as e:
        log.error(f"Scraping failed: {e}")
        return

    if not posts:
        log.info("No new image posts found. Done.")
        return

    published_count = 0

    for post in posts:
        log.info(f"\n── Processing post {post['post_id']} from {post['page_url']}")

        # ── Step 2: AI OCR + rewrite ─────────────────────────
        try:
            ai_result = process_post(post)
        except Exception as e:
            log.error(f"AI processing failed: {e}")
            continue

        if ai_result is None:
            log.warning("Skipping post (AI returned no result). Marking as seen to prevent infinite retry.")
            mark_post_seen(post['page_url'], post['post_id'])
            continue

        log.info(f"Topic: {ai_result['topic_tag']}")
        log.info(f"Rewritten: {ai_result['rewritten_text'][:80]}…")

        # ── Step 3: Generate + compose image ─────────────────
        try:
            image_path = compose_image(
                image_prompt   = ai_result["image_prompt"],
                rewritten_text = ai_result["rewritten_text"],
                topic_tag      = ai_result["topic_tag"],
                page_name      = PAGE_NAME,
            )
        except Exception as e:
            log.error(f"Image composition failed: {e}")
            continue

        if image_path is None:
            log.warning("Skipping post (image generation failed). Marking as seen to prevent infinite retry.")
            mark_post_seen(post['page_url'], post['post_id'])
            continue

        # ── Step 4: Publish ───────────────────────────────────
        caption = (
            f"{ai_result['rewritten_text']}\n\n"
            f"💡 Follow @{PAGE_NAME} for more amazing facts!\n"
            f"#knowledge #facts #{ai_result['topic_tag'].replace(' ', '').lower()}"
        )

        try:
            post_id = publish_to_facebook(image_path, caption)
        except Exception as e:
            log.error(f"Publishing failed: {e}")
            continue

        if post_id:
            log.info(f"✅ Published successfully! FB post ID: {post_id}")
            # IMPORTANT: Only mark as seen AFTER successful publish
            mark_post_seen(post['page_url'], post['post_id'])
            published_count += 1
        else:
            log.error("❌ Publish returned no post ID")

        # Polite delay between posts to avoid rate limits
        if len(posts) > 1:
            log.info("Waiting 30s before next post…")
            time.sleep(30)

    log.info(f"\n✅ Done — published {published_count}/{len(posts)} posts")


def main_loop():
    """
    Bullet-proof loop that runs indefinitely.
    Checks for new posts every 1 hour.
    """
    CHECK_INTERVAL_SECONDS = 3600  # 1 hour
    
    log.info("Starting FB Page Automation as a continuous background service.")
    log.info(f"The pipeline will wake up every {CHECK_INTERVAL_SECONDS/3600} hour(s) to check for updates.")
    
    while True:
        try:
            run_pipeline()
        except KeyboardInterrupt:
            log.info("Process interrupted by user. Exiting safely.")
            break
        except Exception as e:
            # Catch absolute worst-case errors so the loop never dies
            log.error(f"CRITICAL ERROR in main loop: {e}")
            log.debug(traceback.format_exc())
            
        log.info(f"Sleeping for 1 hour until the next check...")
        try:
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            log.info("Process interrupted by user during sleep. Exiting safely.")
            break

if __name__ == "__main__":
    main_loop()
