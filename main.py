import json
import datetime
import os
import logging
import sys
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Check if running in Azure
IN_AZURE = os.environ.get('WEBSITE_SITE_NAME') is not None

# Define paths based on environment
if IN_AZURE:
    # In Azure, use the deployment path
    BASE_PATH = os.environ.get('HOME', '') + '/site/wwwroot'
    PERSONNEL_FILE = os.path.join(BASE_PATH, "personnel.json")
    HOLIDAYS_FILE = os.path.join(BASE_PATH, "holidays.json")
    SETTINGS_FILE = os.path.join(BASE_PATH, "settings.json")
    logger.info(f"Using Azure path for data files: {BASE_PATH}")
else:
    # Local development path
    PERSONNEL_FILE = "personnel.json"
    HOLIDAYS_FILE = "holidays.json"
    SETTINGS_FILE = "settings.json"
    logger.info("Using local path for data files")

def load_personnel() -> List[Dict]:
    try:
        with open(PERSONNEL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded personnel data from {PERSONNEL_FILE}")
        return [p for p in data["personnel"] if p["isActive"]]
    except Exception as e:
        logger.error(f"Error loading personnel data: {str(e)}")
        # Return empty list as fallback
        return []

def load_holidays() -> List[str]:
    try:
        with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded holidays data from {HOLIDAYS_FILE}")
        return [h["date"] for h in data["holidays"]]
    except Exception as e:
        logger.error(f"Error loading holidays data: {str(e)}")
        # Return empty list as fallback
        return []

def load_settings() -> Dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        logger.info(f"Successfully loaded settings data from {SETTINGS_FILE}")
        return settings
    except Exception as e:
        logger.error(f"Error loading settings data: {str(e)}")
        # Return default settings as fallback
        return {
            "ui_settings": {"dark_mode": False, "show_week_numbers": True},
            "custom_order": []
        }

def get_week_dates(reference: datetime.date = None):
    today = reference or datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    return start

def get_person_for_week(week_offset=0) -> Dict:
    # First, sort personnel alphabetically by name (this is the default order)
    personnel = sorted(load_personnel(), key=lambda x: x["name"].lower())
    holidays = load_holidays()
    settings = load_settings()
    paused = settings.get("paused", False)
    custom_order = settings.get("custom_order", [])
    
    # If a custom order is set by admin (e.g., to specify a starting member),
    # re-sort the personnel according to that custom order
    if custom_order and len(custom_order) == len(personnel):
        # Use custom order if set
        personnel = sorted(personnel, key=lambda x: custom_order.index(x["id"]))
    if paused:
        # If paused, always show the current week as the same as last week
        week_offset = 0
    week_start = get_week_dates() + datetime.timedelta(weeks=week_offset)
    # Count only non-holiday weeks
    idx = 0
    week = 0
    while week <= abs(week_offset):
        date_str = (get_week_dates() + datetime.timedelta(weeks=idx)).strftime("%Y-%m-%d")
        if date_str not in holidays:
            week += 1
        idx += 1 if week_offset >= 0 else -1
    pos = (idx-1) % len(personnel) if week_offset >= 0 else (idx) % len(personnel)
    return personnel[pos]

def show_dashboard():
    print("\n=== Maintenance Support Scheduler Dashboard ===\n")
    current = get_person_for_week(0)
    previous = get_person_for_week(-1)
    upcoming = get_person_for_week(1)
    print(f"Previous Week: {previous['name']} ({previous['email']})")
    print(f"Current Week:  {current['name']} ({current['email']})")
    print(f"Upcoming Week: {upcoming['name']} ({upcoming['email']})")

if __name__ == "__main__":
    show_dashboard()
