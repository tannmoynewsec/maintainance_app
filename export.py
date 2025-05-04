import csv
import json
import datetime
import os

def load_personnel():
    """Load personnel data from personnel.json"""
    with open("personnel.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return [p for p in data["personnel"] if p["isActive"]]

def load_settings():
    """Load settings from settings.json"""
    with open("settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    return settings

def get_week_dates(reference=None):
    """Get start and end dates for a week"""
    today = reference or datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    week_number = start.isocalendar()[1]
    return start, end, week_number

def generate_schedule(weeks_ahead=12):
    """Generate schedule for the specified number of weeks ahead"""
    from app import get_person_for_week
    
    schedule = []
    
    # Add current and previous week
    schedule.append(get_person_for_week(-1))
    schedule.append(get_person_for_week(0))
    
    # Add future weeks
    for i in range(1, weeks_ahead + 1):
        schedule.append(get_person_for_week(i))
    
    return schedule

def export_to_csv(filename=None, weeks=12):
    """Export schedule to CSV file"""
    schedule = generate_schedule(weeks)
    
    if filename is None:
        today = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"maintenance_schedule_{today}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['week_number', 'week_start', 'week_end', 'name', 'email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for week in schedule:
            writer.writerow({
                'week_number': week['week_number'],
                'week_start': week['week_start'],
                'week_end': week['week_end'],
                'name': week['name'],
                'email': week['email']
            })
    
    return filename

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export maintenance schedule')
    parser.add_argument('--output', '-o', help='Output file name')
    parser.add_argument('--weeks', '-w', type=int, default=12, help='Number of weeks ahead to export')
    
    args = parser.parse_args()
    
    filename = export_to_csv(args.output, args.weeks)
    print(f"Schedule exported to {filename}")
