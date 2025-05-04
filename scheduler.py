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
    
    args = parser.parse_args()
    
    if args.check_reminders:
        check_upcoming_notifications()
    elif args.send_summary:
        send_schedule_summary()
    else:
        parser.print_help()
