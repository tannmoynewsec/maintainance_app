import re

# Define the corrected function with proper indentation
corrected_function = """def get_person_for_week(week_offset=0):
    # First, sort personnel alphabetically by name (this is the default order)
    personnel = sorted(load_personnel(), key=lambda x: x["name"].lower())
    holidays = load_holidays()
    # Extract just the dates from the holiday objects for easier comparison
    holiday_dates = [h['date'] for h in holidays]
    settings = load_settings()
    paused = settings.get("paused", False)
    custom_order = settings.get("custom_order", [])
    
    # If a custom order is set by admin (e.g., to specify a starting member),
    # re-sort the personnel according to that custom order
    if custom_order and len(custom_order) == len(personnel):
        personnel = sorted(personnel, key=lambda x: custom_order.index(x["id"]))
    if paused:
        week_offset = 0
    
    # Start from today and move forward/backward, skipping holidays
    base_date = datetime.date.today()
    last_valid_start = base_date.strftime("%Y-%m-%d")
    last_valid_end = (base_date + datetime.timedelta(days=6)).strftime("%Y-%m-%d")
    last_valid_number = base_date.isocalendar()[1]
    idx = 0
    week = 0
    
    if week_offset >= 0:
        current_date = base_date
        while week <= week_offset:
            week_start = current_date - datetime.timedelta(days=current_date.weekday())
            week_end = week_start + datetime.timedelta(days=6)
            week_number = week_start.isocalendar()[1]
            date_str = week_start.strftime("%Y-%m-%d")
            if date_str not in holiday_dates:
                last_valid_start = date_str
                last_valid_end = week_end.strftime("%Y-%m-%d")
                last_valid_number = week_number
                week += 1
            idx += 1
            current_date = base_date + datetime.timedelta(weeks=idx)
        pos = (idx-1) % len(personnel)
    else:
        current_date = base_date
        while week <= abs(week_offset):
            week_start = current_date - datetime.timedelta(days=current_date.weekday())
            week_end = week_start + datetime.timedelta(days=6)
            week_number = week_start.isocalendar()[1]
            date_str = week_start.strftime("%Y-%m-%d")
            if date_str not in holiday_dates:
                last_valid_start = date_str
                last_valid_end = week_end.strftime("%Y-%m-%d")
                last_valid_number = week_number
                week += 1
            idx -= 1
            current_date = base_date + datetime.timedelta(weeks=idx)
        pos = idx % len(personnel)
    
    return {
        **personnel[pos],
        "week_number": last_valid_number,
        "week_start": last_valid_start,
        "week_end": last_valid_end
    }"""

# Read app.py file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the existing get_person_for_week function and replace it
pattern = r'def get_person_for_week\(week_offset=0\):.*?return \{.*?\}$'
new_content = re.sub(pattern, corrected_function, content, flags=re.DOTALL | re.MULTILINE)

# Write the fixed content back to app.py
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Function fix completed.")
