import datetime
from icalendar import Calendar, Event, vText
import uuid
import json
import os

def load_settings():
    """Load settings from settings.json"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    settings_file = os.path.join(base_path, "settings.json")
    with open(settings_file, "r", encoding="utf-8") as f:
        settings = json.load(f)
    return settings

def load_personnel():
    """Load personnel data from personnel.json"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    personnel_file = os.path.join(base_path, "personnel.json")
    with open(personnel_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["id"]: p for p in data["personnel"] if p["isActive"]}

def get_week_dates(reference=None):
    """Get start and end dates for a week"""
    today = reference or datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    week_number = start.isocalendar()[1]
    return start, end, week_number

def generate_ical_for_person(person_id, week_offset=0):
    """
    Generate an iCalendar file for a person's maintenance duty
    
    Args:
        person_id (str): The ID of the person
        week_offset (int): The week offset from current week
        
    Returns:
        bytes: The iCalendar file content
    """
    personnel_dict = load_personnel()
    
    # Check if person exists
    if person_id not in personnel_dict:
        return None
    
    person = personnel_dict[person_id]
    
    # Calculate week dates based on offset
    base_date = datetime.date.today()
    offset_date = base_date + datetime.timedelta(weeks=week_offset)
    week_start, week_end, week_number = get_week_dates(offset_date)
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//Maintenance Support Scheduler//mxm.dk//')
    cal.add('version', '2.0')
    
    # Create event
    event = Event()
    event.add('summary', f'Maintenance Support Duty - {person["name"]}')
    
    # Set start date (Monday)
    event_start = datetime.datetime.combine(week_start, datetime.time(9, 0))
    event.add('dtstart', event_start)
    
    # Set end date (Friday)
    event_end = datetime.datetime.combine(week_end, datetime.time(17, 0))
    event.add('dtend', event_end)
    
    event.add('dtstamp', datetime.datetime.now())
    event['uid'] = str(uuid.uuid4())
    
    description = (f"Maintenance Support Duty for Week {week_number}\n"
                   f"Person: {person['name']}\n"
                   f"Email: {person['email']}\n"
                   f"Duration: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    event.add('description', description)
    
    # Add to calendar
    cal.add_component(event)
    
    return cal.to_ical()
