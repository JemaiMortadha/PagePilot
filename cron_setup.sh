#!/bin/bash
# cron_setup.sh — Install a cron job to run the automation every 4 hours
# Run once: bash cron_setup.sh

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3)
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

CRON_CMD="0 */4 * * * cd \"$PROJECT_DIR\" && $PYTHON main.py >> \"$LOG_DIR/cron.log\" 2>&1"

# Check if already installed
(crontab -l 2>/dev/null | grep -q "FB-Page-Automation/main.py") && {
    echo "✓ Cron job already installed."
    exit 0
}

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
echo "✅ Cron job installed — automation will run every 4 hours."
echo ""
echo "Cron entry:"
echo "  $CRON_CMD"
echo ""
echo "To view cron jobs:   crontab -l"
echo "To remove cron job:  crontab -e  (then delete the line)"
