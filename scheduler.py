import os
import json
import datetime
import argparse
from notification import send_notification, send_upcoming_notifications

def load_settings():
    """Load settings from settings.json"""
    with open("settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    return settings

def save_settings(settings):
    """Save settings to settings.json"""
    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def load_personnel():
    """Load personnel data from personnel.json"""
    with open("personnel.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return [p for p in data["personnel"] if p["isActive"]]

def check_upcoming_notifications():
    """Check if notifications need to be sent for upcoming duties"""
    settings = load_settings()
    email_settings = settings.get('email_settings', {})
    
    if not email_settings.get('notifications_enabled', False):
        print("Email notifications are disabled in settings.")
        return False
    
    days_in_advance = email_settings.get('reminder_days', 7)
    print(f"Checking for duties starting in {days_in_advance} days...")
    send_upcoming_notifications(days_in_advance)
    return True

def advance_rotation():
    """Advance the rotation order automatically
    
    This function is designed to be called every Monday at 00:00 AM to automatically
    rotate the order so that current person becomes previous and upcoming becomes current.
    If a specific person was chosen by admin, it will rotate from that person while
    maintaining alphabetical sequence.
    """
    settings = load_settings()
    
    # Skip if rotation is paused
    if settings.get('paused', False):
        print("Rotation is currently paused. Not advancing.")
        return False
    
    # Load personnel and get existing custom order (if any)
    all_personnel = load_personnel()
    current_custom_order = settings.get('custom_order', [])
    
    # If we have no personnel, just return
    if not all_personnel:
        print("No active personnel found. Order maintained as empty.")
        settings['custom_order'] = []
        save_settings(settings)
        return True
        
    # Check if we have a specific starting person (custom order) set by admin
    if current_custom_order and len(current_custom_order) > 0:
        # Rotate the custom order by moving the first person to the end
        new_order = current_custom_order[1:] + [current_custom_order[0]]
        print(f"Rotating order: Moving {current_custom_order[0]} to the end.")
    else:
        # If no custom order, create a new one based on alphabetical order
        sorted_personnel = sorted(all_personnel, key=lambda x: x["name"].lower())
        new_order = [p["id"] for p in sorted_personnel]
        print("No custom order found. Using alphabetical order.")
    
    # Update the settings with the new order
    settings['custom_order'] = new_order
    save_settings(settings)
    
    if new_order:
        print(f"Rotation advanced successfully. New rotation starts with ID: {new_order[0]}")
    else:
        print("No active personnel found. Order maintained as empty.")
    
    return True

def send_schedule_summary():
    """Send a schedule summary to all personnel"""
    from app import get_person_for_week
    
    settings = load_settings()
    email_settings = settings.get('email_settings', {})
    
    if not email_settings.get('notifications_enabled', False):
        print("Email notifications are disabled in settings.")
        return False
    
    personnel = load_personnel()
    current = get_person_for_week(0)
    upcoming = get_person_for_week(1)
    
    # Create schedule summary message
    today = datetime.date.today()
    
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get email settings
    smtp_server = email_settings.get("smtp_server", "")
    smtp_port = email_settings.get("smtp_port", 587)
    sender_email = email_settings.get("sender_email", "")
    sender_password = email_settings.get("sender_password", "")
    cc_emails = email_settings.get("cc_emails", [])
    
    # If email settings are not configured, return without sending
    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        print("Email settings not configured. Please update settings.json")
        return False
    
    success_count = 0
    
    for person in personnel:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = person['email']
        if cc_emails:
            msg['Cc'] = ", ".join(cc_emails)
        
        msg['Subject'] = f"Maintenance Support Schedule Update ({today.strftime('%Y-%m-%d')})"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Maintenance Support Schedule Update</h2>
            <p>Hello {person['name']},</p>
            <p>Here is the current maintenance support schedule:</p>
            
            <div style="background-color: #e0e7ef; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h3>Current Week ({current['week_start']} to {current['week_end']})</h3>
                <p><strong>{current['name']}</strong> ({current['email']})</p>
            </div>
            
            <div style="background-color: #f1f5fb; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h3>Upcoming Week ({upcoming['week_start']} to {upcoming['week_end']})</h3>
                <p><strong>{upcoming['name']}</strong> ({upcoming['email']})</p>
            </div>
            
            <p>You can view the full schedule on the <a href="http://localhost:8000">Maintenance Support Scheduler</a> website.</p>
            
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
            
            # Prepare recipient list (including CC)
            all_recipients = [person['email']] + cc_emails
            
            # Send email
            server.send_message(msg)
            success_count += 1
            
            print(f"Sent schedule summary to {person['name']} <{person['email']}>")
            
        except Exception as e:
            print(f"Failed to send email to {person['email']}: {e}")
        
    if server:
        server.quit()
        
    print(f"Schedule summary sent to {success_count} out of {len(personnel)} personnel.")
    return success_count > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Maintenance App Scheduled Tasks')
    parser.add_argument('--check-reminders', action='store_true', 
                      help='Check and send reminders for upcoming support duties')
    parser.add_argument('--send-summary', action='store_true',
                      help='Send schedule summary to all personnel')
    parser.add_argument('--advance-rotation', action='store_true',
                      help='Update the rotation order alphabetically (typically run every Monday)')
    
    args = parser.parse_args()
    
    if args.check_reminders:
        check_upcoming_notifications()
    elif args.send_summary:
        send_schedule_summary()
    elif args.advance_rotation:
        advance_rotation()
    else:
        parser.print_help()
