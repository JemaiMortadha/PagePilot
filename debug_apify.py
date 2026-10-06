"""
debug_apify.py — Print the raw structure of the first Apify result
so we can find where the actual CDN image URLs are.
Run once: python3 debug_apify.py
"""
import json
from apify_client import ApifyClient
from dotenv import load_dotenv
import os

load_dotenv()
client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Use the first competitor page
from dotenv import dotenv_values
env = dotenv_values(".env")
pages = [p.strip() for p in env.get("COMPETITOR_PAGES","").split(",") if p.strip()]
page_url = pages[0]
print(f"Scraping: {page_url}\n")

run = client.actor("apify/facebook-posts-scraper").call(run_input={
    "startUrls": [{"url": page_url}],
    "resultsLimit": 2,
})
dataset = client.dataset(run.default_dataset_id)

for i, item in enumerate(dataset.iterate_items()):
    print(f"=== ITEM {i} ===")
    print(json.dumps(item, indent=2, default=str))
    print()
    if i >= 1:
        break
