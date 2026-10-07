import json
import logging
from datetime import datetime, timezone
import config

log = logging.getLogger(__name__)

USAGE_FILE = config.BASE_DIR / "usage_stats.json"

# Limits based on free tiers
GEMINI_DAILY_LIMIT = 1500
# Apify is $5/mo. If a run costs $0.005, that's 1000 runs. 
# We'll use 1000 as a rough warning threshold.
APIFY_MONTHLY_LIMIT = 1000 

def _load_usage() -> dict:
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save_usage(data: dict):
    USAGE_FILE.write_text(json.dumps(data, indent=2))

def record_gemini_calls(count=1):
    """Call this when Gemini is used (e.g., 4 calls per processed post)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = _load_usage()
    if "gemini" not in data: data["gemini"] = {}
    data["gemini"][today] = data["gemini"].get(today, 0) + count
    _save_usage(data)

def record_apify_runs(count=1):
    """Call this when Apify scrapes a page."""
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    data = _load_usage()
    if "apify" not in data: data["apify"] = {}
    data["apify"][month] = data["apify"].get(month, 0) + count
    _save_usage(data)

def get_usage_report() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    data = _load_usage()
    gemini_today = data.get("gemini", {}).get(today, 0)
    apify_month = data.get("apify", {}).get(month, 0)
    
    now = datetime.now(timezone.utc)
    
    # Project Gemini (Daily)
    hours_passed_today = now.hour + (now.minute / 60.0)
    if hours_passed_today < 0.1: hours_passed_today = 0.1
    gemini_projected = (gemini_today / hours_passed_today) * 24
    gemini_status = "✅ Safe" if gemini_projected < GEMINI_DAILY_LIMIT else "⚠️ WARNING"
    
    # Project Apify (Monthly)
    days_passed_this_month = now.day + (now.hour / 24.0)
    if days_passed_this_month < 0.1: days_passed_this_month = 0.1
    apify_projected = (apify_month / days_passed_this_month) * 30
    apify_status = "✅ Safe" if apify_projected < APIFY_MONTHLY_LIMIT else "⚠️ WARNING"
    
    # Max Usage Scenario Analysis
    import config
    C = len(config.COMPETITOR_PAGES)
    max_gemini_daily = C * 4 * 4  # 4 checks per day * C pages * 4 AI calls per post
    
    # We check 4 times a day (every 6 hours). 
    # Max posts fetched per month = C pages * POSTS_TO_CHECK * 4 checks/day * 30 days
    max_apify_monthly = C * config.POSTS_TO_CHECK * 4 * 30
    
    # Calculate how many more competitors can be safely added
    apify_headroom = max(0, APIFY_MONTHLY_LIMIT - max_apify_monthly)
    competitors_can_add = int(apify_headroom / (config.POSTS_TO_CHECK * 4 * 30)) if config.POSTS_TO_CHECK > 0 else 0
    
    report = (
        f"📊 API QUOTA REPORT\n"
        f"-------------------\n\n"
        f"🧠 GEMINI (Resets Daily)\n"
        f" - Used Today: {gemini_today} / {GEMINI_DAILY_LIMIT} requests\n"
        f" - Projected by EOD: {int(gemini_projected)} requests\n"
        f" - Status: {gemini_status}\n\n"
        f"🕷️ APIFY (Resets Monthly)\n"
        f" - Used This Month: {apify_month} / ~{APIFY_MONTHLY_LIMIT} runs\n"
        f" - Projected by EOM: {int(apify_projected)} runs\n"
        f" - Status: {apify_status}\n\n"
        f"🔮 CAPACITY ANALYSIS (Worst-Case Scenario)\n"
        f" - If every page posted a new image every hour for 24h:\n"
        f"   Gemini would use: {max_gemini_daily} / {GEMINI_DAILY_LIMIT} (Daily)\n"
        f"   Apify would use:  {max_apify_monthly} / ~{APIFY_MONTHLY_LIMIT} (Monthly)\n"
        f" - You can safely track {competitors_can_add} MORE competitor page(s) at your current 1-hour interval.\n"
    )
    return report
