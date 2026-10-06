#!/usr/bin/env python3
"""
test_pipeline.py — Test the image-generation + text-overlay pipeline
WITHOUT needing any API keys or internet (except Pollinations.ai).

Uses the bundled style.jpeg as a reference image and generates a
sample post so you can see the visual output before going live.

Run: python3 test_pipeline.py
Output: output/test_sample.jpg
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("test")

# ── Sample data — simulates what the AI processor would return ─
SAMPLE_AI_RESULT = {
    "topic_tag":      "SCIENCE",
    "rewritten_text": (
        "Research finds that drinking bone broth during winter "
        "nourishes the body with minerals and amino acids that "
        "can strengthen immunity"
    ),
    "image_prompt": (
        "translucent glowing human anatomy drinking from a bowl, "
        "warm broth flowing through digestive system, circular food "
        "inset in top right corner"
    ),
}

def main():
    log.info("Running pipeline test…")
    log.info("Step 1: Running font setup (if needed)…")
    import setup  # noqa: F401 — runs the setup

    log.info("Step 2: Composing test image via Pollinations.ai…")
    from image_composer import compose_image
    import config

    output_path = config.OUTPUT_DIR / "test_sample.jpg"

    result = compose_image(
        image_prompt   = SAMPLE_AI_RESULT["image_prompt"],
        rewritten_text = SAMPLE_AI_RESULT["rewritten_text"],
        topic_tag      = SAMPLE_AI_RESULT["topic_tag"],
        page_name      = "TestPage",
        output_path    = output_path,
    )

    if result:
        log.info(f"✅ Test image saved → {result}")
        log.info("Open it to verify the style looks correct.")
    else:
        log.error("❌ Test failed — image was not generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
