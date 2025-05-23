import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

def load_settings():
    """Load email settings from settings.json"""
    # Check if we're running in Azure or local environment
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try data subdirectory first (local development)
    settings_path = os.path.join(base_dir, "data", "settings.json")
    
    # If not found, try the app root directory (Azure deployment)
    if not os.path.exists(settings_path):
        settings_path = os.path.join(base_dir, "settings.json")
    
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    return settings

def send_notification(recipient_name, recipient_email, week_start, week_end, week_number, is_reminder=False):
    """Send an email notification to the upcoming support person"""
    settings = load_settings()
    
    # Get email settings from settings.json, or use defaults
    email_settings = settings.get("email_settings", {})
    smtp_server = email_settings.get("smtp_server", "")
    smtp_port = email_settings.get("smtp_port", 587)
    sender_email = email_settings.get("sender_email", "")
    sender_password = email_settings.get("sender_password", "")
    
    # If email settings are not configured, return without sending
    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        print("Email settings not configured. Please update settings.json")
        return False
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    if is_reminder:
        msg['Subject'] = f"REMINDER: Your Maintenance Support Duty Starts Soon (Week {week_number})"
        body = f"""
        <html>
        <body>
            <h2>Maintenance Support Reminder</h2>
            <p>Hello {recipient_name},</p>
            <p>This is a friendly reminder that you are scheduled for maintenance support duty for Week {week_number}.</p>
            <p><strong>Period:</strong> {week_start} to {week_end}</p>
            <p>Please ensure you are prepared to handle support requests during this period.</p>
            <p>Thank you for your service!</p>
            <p>Best regards,<br>
            Maintenance Support System</p>
        </body>
        </html>
        """
    else:
        msg['Subject'] = f"You Are Scheduled for Maintenance Support (Week {week_number})"
        body = f"""
        <html>
        <body>
            <h2>Maintenance Support Schedule Notification</h2>
            <p>Hello {recipient_name},</p>
            <p>You have been scheduled for maintenance support duty for Week {week_number}.</p>
            <p><strong>Period:</strong> {week_start} to {week_end}</p>
            <p>Please mark this in your calendar and ensure you are available during this period.</p>
            <p>Thank you for your service!</p>
            <p>Best regards,<br>
            Maintenance Support System</p>
        </body>
        </html>
        """
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        # Establish connection with the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_upcoming_notifications(days_in_advance=7):
    """
    Check if anyone needs to be notified about upcoming support duty
    This function should be called daily by a scheduler
    """
    import datetime
    import importlib
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Import app dynamically to avoid circular import issues
    app_module = importlib.import_module('app')
    get_person_for_week = getattr(app_module, 'get_person_for_week')
    
    # Calculate the date that is days_in_advance days from now
    target_date = datetime.date.today() + datetime.timedelta(days=days_in_advance)
    logger.info(f"Checking notifications for target date: {target_date}")
    
    # Loop through the next few weeks to find whose duty starts near the target date
    for offset in range(1, 4):  # Check next 3 weeks
        person = get_person_for_week(offset)
        if not person:
            logger.warning(f"No person found for week offset {offset}")
            continue
            
        week_start = datetime.datetime.strptime(person['week_start'], "%Y-%m-%d").date()
        
        # If this person's duty starts on the target date, send a reminder
        if week_start == target_date:
            logger.info(f"Sending reminder to {person['name']} for week {person['week_number']}")
            send_notification(
                person['name'],
                person['email'],
                person['week_start'],
                person['week_end'],
                person['week_number'],
                is_reminder=True
            )
            break

if __name__ == "__main__":
    # This allows running the script directly to send test emails
    import sys
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == "send_reminders":
        print("Starting to send reminders...")
        send_upcoming_notifications()
        print("Finished sending reminders")
    else:
        print("Usage: python notification.py send_reminders")
