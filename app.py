from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import json
import datetime
import base64
import os
import sys
import logging
import uuid
from dotenv import load_dotenv
from flask_apscheduler import APScheduler
from scheduler import advance_rotation

# Set up logging
log_level = logging.DEBUG if os.environ.get('DEBUG', 'False').lower() == 'true' else logging.INFO
logging.basicConfig(level=log_level, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting Maintainance Support Scheduler")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

# Load environment variables from .env file if it exists
load_dotenv()

# Check if we're running in Azure
IN_AZURE = os.environ.get('WEBSITE_SITE_NAME') is not None
if IN_AZURE:
    logger.info("Running in Azure environment")

# Configure paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
logger.debug(f"Base path: {BASE_PATH}")

# Admin credentials - in production, set via environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Set up data paths - check both in data directory and root directory
DATA_DIR = os.path.join(BASE_PATH, 'data')
if os.path.isdir(DATA_DIR):
    logger.info(f"Using data directory: {DATA_DIR}")
    PERSONNEL_FILE = os.path.join(DATA_DIR, 'personnel.json')
    SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
else:
    logger.info("Data directory not found, using root directory")
    PERSONNEL_FILE = os.path.join(BASE_PATH, 'personnel.json')
    SETTINGS_FILE = os.path.join(BASE_PATH, 'settings.json')

# Set up logo path
# Logo path removed as per requirements

# Initialize Flask app
app = Flask(__name__, static_url_path='/assets', static_folder='assets')
app.secret_key = os.environ.get('SECRET_KEY', 'default_dev_key_change_in_production')

# Simplify session configuration - use the default, in-memory session
# This is more reliable than filesystem for admin login functionality
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)  # Session lasts for 1 day

# Set up application logging level to debug to help diagnose issues
logging.getLogger('app').setLevel(logging.DEBUG)

# Initialize scheduler
scheduler = APScheduler()
# Configure scheduler with proper settings
scheduler.api_enabled = False
scheduler.init_app(app)
# Set scheduler configuration
scheduler.scheduler.configure(timezone='UTC')

# Schedule the rotation to happen every Monday at 00:00 AM
@scheduler.task('cron', id='rotate_schedule', day_of_week='mon', hour=0, minute=0, misfire_grace_time=3600)
def scheduled_rotation():
    """Advances the rotation order automatically every Monday at midnight"""
    logger.info("Scheduled task: Advancing rotation order")
    try:
        with app.app_context():
            # Run the rotation within the app context
            result = advance_rotation()
            if result:
                logger.info("Rotation order advanced successfully")
            else:
                logger.warning("Failed to advance rotation order or rotation is paused")
            return result
    except Exception as e:
        logger.error(f"Error in scheduled rotation: {str(e)}")
        return False

# Start the scheduler
scheduler.start()
logger.info("APScheduler started successfully")
logger.info(f"Next run time for rotation task: {scheduler.get_job('rotate_schedule').next_run_time}")

# Logo loading removed as per requirements

# Helper functions for data loading/saving
def safe_load_json(file_path):
    """Safely load a JSON file with error handling"""
    try:
        logger.debug(f"Loading JSON file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            # Create empty file with default structure
            if "personnel" in file_path.lower():
                default_data = {"personnel": []}
            elif "holiday" in file_path.lower():
                default_data = {"holidays": []}
            elif "setting" in file_path.lower():
                default_data = {"custom_order": [], "ui_settings": {"dark_mode": False, "show_week_numbers": True}}
            else:
                default_data = {}
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Create the file with default data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)
            
            logger.info(f"Created new file with default structure: {file_path}")
            return default_data
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        raise

def safe_save_json(file_path, data):
    """Safely save a JSON file with error handling"""
    try:
        logger.debug(f"Saving JSON file: {file_path}")
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {str(e)}")
        raise

# Holiday functionality has been removed

def load_personnel():
    """Load personnel from the personnel.json file"""
    try:
        with open(PERSONNEL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [p for p in data["personnel"] if p["isActive"]]
    except FileNotFoundError as e:
        logger.error(f"Could not find personnel file: {PERSONNEL_FILE}")
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir(os.path.dirname(PERSONNEL_FILE))}")
        return []

def load_settings():
    """Load settings from the settings.json file"""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error(f"Could not find settings file: {SETTINGS_FILE}")
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir(os.path.dirname(SETTINGS_FILE))}")
        return {}

def load_holidays():
    """Holiday logic has been removed, returning empty list for compatibility"""
    return []

def get_week_dates(reference=None):
    today = reference or datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    week_number = start.isocalendar()[1]
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), week_number

def get_person_for_week(week_offset=0):
    # First, sort personnel alphabetically by name (this is the default order)
    personnel = sorted(load_personnel(), key=lambda x: x["name"].lower())
    settings = load_settings()
    paused = settings.get("paused", False)
    custom_order = settings.get("custom_order", [])
    
    # If a custom order is set by admin (e.g., to specify a starting member),
    # re-sort the personnel according to that custom order
    if custom_order and len(custom_order) == len(personnel):
        personnel = sorted(personnel, key=lambda x: custom_order.index(x["id"]))
    if paused:
        week_offset = 0
      
    # Start from today and move forward/backward
    base_date = datetime.date.today()
    
    # Calculate the week dates directly
    current_date = base_date + datetime.timedelta(weeks=week_offset)
    week_start = current_date - datetime.timedelta(days=current_date.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_number = week_start.isocalendar()[1]
      # Calculate position based on week offset
    pos = week_offset % len(personnel) if personnel else 0
    
    if not personnel:
        # Return empty data if no personnel
        return {
            "id": "0",
            "name": "No personnel available",
            "email": "",
            "isActive": True,
            "week_number": week_number,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d")
        }
    
    return {
        **personnel[pos],
        "week_number": week_number,
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": week_end.strftime("%Y-%m-%d")
    }

# Helper function to get the logo as a base64 string
# Logo functionality has been removed as per requirements

# Define the HTML template
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" {% if dark_mode %}class="dark"{% endif %}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maintainance Support Scheduler</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient-light: linear-gradient(120deg, #f8fafc 0%, #e0e7ef 100%);
            --bg-gradient-dark: linear-gradient(120deg, #0f172a 0%, #1e293b 100%);
            --container-bg-light: #fff;
            --container-bg-dark: #1e293b;
            --card-bg-light: #f1f5fb;
            --card-bg-dark: #334155;
            --current-card-bg-light: #e0e7ef;
            --current-card-bg-dark: #475569;
            --heading-color-light: #2a4365;
            --heading-color-dark: #e2e8f0;
            --card-heading-light: #2563eb;
            --card-heading-dark: #60a5fa;
            --text-color-light: #22223b;
            --text-color-dark: #f1f5f9;
            --meta-color-light: #64748b;
            --meta-color-dark: #94a3b8;
            --footer-color-light: #888;
            --footer-color-dark: #94a3b8;
            --shadow-light: 0 4px 24px rgba(0,0,0,0.08);
            --shadow-dark: 0 4px 24px rgba(0,0,0,0.25);
            --card-shadow-light: 0 2px 8px rgba(44, 62, 80, 0.04);
            --card-shadow-dark: 0 2px 8px rgba(0, 0, 0, 0.2);
            --card-shadow-hover-light: 0 6px 24px rgba(44, 62, 80, 0.10);
            --card-shadow-hover-dark: 0 6px 24px rgba(0, 0, 0, 0.3);
        }
        
        body {
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            background: var(--bg-gradient-light);
            min-height: 100vh;
            transition: background 0.3s ease;
        }
        
        .dark body {
            background: var(--bg-gradient-dark);
        }
        
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: var(--container-bg-light);
            border-radius: 16px;
            box-shadow: var(--shadow-light);
            padding: 2em 2.5em 1.5em 2.5em;
            transition: background 0.3s ease, box-shadow 0.3s ease;
        }
        
        .dark .container {
            background: var(--container-bg-dark);
            box-shadow: var(--shadow-dark);
        }
        
        .header-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 1.5em;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            margin-bottom: 0.5em;
        }
        
        .logo {
            height: 30px;
            margin-right: 10px;
        }
        
        .bias-name {
            font-size: 2.2em;
            font-weight: 700;
            color: var(--heading-color-light);
            transition: color 0.3s ease;
        }
        
        .dark .bias-name {
            color: var(--heading-color-dark);
        }
        
        h1 {
            text-align: center;
            color: var(--heading-color-light);
            margin: 0.2em 0 0.5em 0;
            font-size: 1.8em;
            font-weight: 700;
            letter-spacing: 0.5px;
            transition: color 0.3s ease;
        }
        
        .dark h1 {
            color: var(--heading-color-dark);
        }
        
        .card {
            background: var(--card-bg-light);
            border-radius: 12px;
            padding: 1.2em 1.5em;
            margin-bottom: 1em;
            color: var(--text-color-light);
            box-shadow: var(--card-shadow-light);
            transition: box-shadow 0.2s, background 0.3s ease;
        }
        
        .dark .card {
            background: var(--card-bg-dark);
            box-shadow: var(--card-shadow-dark);
        }
        
        .card.current {
            background: linear-gradient(120deg, #4ade80 0%, #22c55e 100%);
            color: white;
        }
        
        .dark .card.current {
            background: linear-gradient(120deg, #22c55e 0%, #16a34a 100%);
            color: white;
        }
        
        .card:hover {
            box-shadow: var(--card-shadow-hover-light);
        }
        
        .dark .card:hover {
            box-shadow: var(--card-shadow-hover-dark);
        }
        
        h2 {
            margin-top: 0;
            color: var(--card-heading-light);
            font-size: 1.2em;
            letter-spacing: 0.5px;
            transition: color 0.3s ease;
        }
        
        .dark h2 {
            color: var(--card-heading-dark);
        }
        
        .card.current h2 {
            color: rgba(255, 255, 255, 0.9);
        }
        
        .person {
            font-size: 1.1em;
            font-weight: 500;
            margin: 0.6em 0;
        }
        
        .email {
            font-weight: normal;
            font-size: 0.9em;
            color: var(--meta-color-light);
            transition: color 0.3s ease;
        }
        
        .dark .email {
            color: var(--meta-color-dark);
        }
        
        .card.current .email {
            color: rgba(255, 255, 255, 0.8);
        }
        
        .meta {
            color: var(--meta-color-light);
            font-size: 0.9em;
            transition: color 0.3s ease;
        }
        
        .dark .meta {
            color: var(--meta-color-dark);
        }
        
        .card.current .meta {
            color: rgba(255, 255, 255, 0.8);
        }
        
        footer {
            margin-top: 2em;
            color: var(--footer-color-light);
            text-align: center;
            font-size: 0.95em;
            transition: color 0.3s ease;
        }
        
        .dark footer {
            color: var(--footer-color-dark);
        }
        
        .toggle-container {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 1em;
        }
        
        .toggle-mode {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.2em;
            padding: 5px 10px;
            color: var(--meta-color-light);
            transition: color 0.3s ease;
        }
        
        .dark .toggle-mode {
            color: var(--meta-color-dark);
        }
        
        .calendar-button {
            display: inline-block;
            margin-top: 0.5em;
            text-decoration: none;
            background: #2563eb;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        
        .calendar-button:hover {
            background: #1d4ed8;
        }
        
        .dark .calendar-button {
            background: #3b82f6;
        }
        
        .dark .calendar-button:hover {
            background: #2563eb;
        }
        
        /* Responsive design */
        @media (max-width: 650px) {
            .container {
                margin: 20px 15px;
                padding: 1.5em;
                border-radius: 12px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="toggle-container">
            <form method="get" action="{{ url_for('toggle_theme') }}">
                <button type="submit" class="toggle-mode">
                    {% if dark_mode %}☀️{% else %}🌙{% endif %}
                </button>
            </form>
        </div>
          <div class="header-container">
            <div class="logo-container">
                <span class="bias-name">BIAS</span>
            </div>
            <h1>Maintainance Support Scheduler</h1>
        </div>
        
        <div class="card">
            <h2>Previous Week</h2>
            <div class="person">
                {{ previous['name'] }} 
                <span class="email">({{ previous['email'] }})</span>
            </div>
            {% if show_week_numbers %}
            <div class="meta">Week {{ previous['week_number'] }}: {{ previous['week_start'] }} to {{ previous['week_end'] }}</div>
            {% else %}
            <div class="meta">{{ previous['week_start'] }} to {{ previous['week_end'] }}</div>
            {% endif %}
        </div>
        
        <div class="card current">
            <h2>Current Week</h2>
            <div class="person">
                {{ current['name'] }} 
                <span class="email">({{ current['email'] }})</span>
            </div>
            {% if show_week_numbers %}
            <div class="meta">Week {{ current['week_number'] }}: {{ current['week_start'] }} to {{ current['week_end'] }}</div>
            {% else %}
            <div class="meta">{{ current['week_start'] }} to {{ current['week_end'] }}</div>
            {% endif %}
            <a href="{{ url_for('generate_ical', person_id=current['id']) }}" class="calendar-button">📅 Add to Calendar</a>
        </div>
        
        <div class="card">
            <h2>Upcoming Week</h2>
            <div class="person">
                {{ upcoming['name'] }} 
                <span class="email">({{ upcoming['email'] }})</span>
            </div>
            {% if show_week_numbers %}
            <div class="meta">Week {{ upcoming['week_number'] }}: {{ upcoming['week_start'] }} to {{ upcoming['week_end'] }}</div>
            {% else %}
            <div class="meta">{{ upcoming['week_start'] }} to {{ upcoming['week_end'] }}</div>
            {% endif %}
            <a href="{{ url_for('generate_ical', person_id=upcoming['id']) }}" class="calendar-button">📅 Add to Calendar</a>
        </div>
        
        <footer>
            &copy; 2025 Maintainance Support Scheduler | <a href="/admin" style="color:inherit;">Admin</a>
        </footer>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Add any client-side JavaScript functionality here
        });
    </script>
</body>
</html>
'''

# Helper function for admin authentication
def is_logged_in():
    try:
        # Debug full session contents
        logger.debug(f"Session contents: {dict(session)}")
        
        logged_in = session.get('logged_in', False)
        login_time = session.get('login_time', None)
        logger.debug(f"Session check - logged_in: {logged_in}, login_time: {login_time}")
        
        # Check if the session contains all required values
        if logged_in and login_time:
            logger.debug("Valid session found")
            return True
        
        # If we reached here, the session is not valid
        logger.debug("Invalid session - missing required values")
        return False
    except Exception as e:
        logger.error(f"Error checking login status: {str(e)}")
        return False

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    logger.debug("Admin login page accessed")
    logger.debug(f"Expected credentials - Username: {ADMIN_USERNAME}, Password: {ADMIN_PASSWORD[:2]}***")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug(f"Admin login attempt: {username} with password length {len(password) if password else 0}")
        
        # Log expected vs. provided credentials for debugging
        match_user = username == ADMIN_USERNAME
        match_pwd = password == ADMIN_PASSWORD
        logger.debug(f"Username match: {match_user}, Password match: {match_pwd}")
        
        if match_user and match_pwd:
            session.clear()  # Clear any old session
            session['logged_in'] = True
            session['login_time'] = datetime.datetime.now().isoformat()
            session.permanent = True  # Make session permanent
            logger.info(f"Admin login successful for user: {username}")
            # Use absolute URL for redirect to avoid potential issues
            return redirect(url_for('admin_dashboard', _external=True))
        else:
            logger.warning(f"Failed admin login attempt for user: {username}")
            flash('Invalid credentials', 'danger')
    return render_template_string('''
    <form method="post" style="max-width:350px;margin:60px auto;padding:2em 2em 1em 2em;background:#fff;border-radius:10px;box-shadow:0 2px 12px #0001;">
        <h2 style="text-align:center;color:#2563eb;">Admin Login</h2>
        <input name="username" placeholder="Username" class="form-control" style="width:100%;margin-bottom:1em;padding:0.7em;border-radius:6px;border:1px solid #ccc;" required>
        <input name="password" type="password" placeholder="Password" class="form-control" style="width:100%;margin-bottom:1em;padding:0.7em;border-radius:6px;border:1px solid #ccc;" required>
        <button type="submit" style="width:100%;background:#2563eb;color:#fff;padding:0.7em;border:none;border-radius:6px;font-weight:600;">Login</button>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div style="margin-top:1em;">
              {% for category, message in messages %}
                <div style="color:red;">{{ message }}</div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}
    </form>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    logger.debug("Admin dashboard accessed")
    logged_in = is_logged_in()
    if not logged_in:
        logger.warning("Unauthorized access attempt to admin dashboard")
        return redirect(url_for('admin_login'))
    personnel = load_personnel()
    settings = load_settings()
    
    # For set start person
    msg = None
    if request.method == 'POST':
        if 'set_start_person' in request.form:
            start_id = request.form.get('start_person_id')
            ids = [p['id'] for p in personnel]
            if start_id in ids:
                idx = ids.index(start_id)
                new_order = ids[idx:] + ids[:idx]
                # Save to settings.json
                settings['custom_order'] = new_order
                safe_save_json(SETTINGS_FILE, settings)
                msg = 'Schedule will now start with: ' + next((p['name'] for p in personnel if p['id'] == start_id), '')
            else:
                msg = 'Invalid selection.'
        
        # Save email settings
        elif 'save_email_settings' in request.form:
            if 'email_settings' not in settings:
                settings['email_settings'] = {}
            settings['email_settings']['smtp_server'] = request.form.get('smtp_server', '')
            settings['email_settings']['smtp_port'] = int(request.form.get('smtp_port', 587))
            settings['email_settings']['sender_email'] = request.form.get('sender_email', '')
            settings['email_settings']['sender_password'] = request.form.get('sender_password', '')
            settings['email_settings']['notifications_enabled'] = 'notifications_enabled' in request.form
            settings['email_settings']['reminder_days'] = int(request.form.get('reminder_days', 7))
            cc_emails = request.form.get('cc_emails', '')
            settings['email_settings']['cc_emails'] = [email.strip() for email in cc_emails.split(',') if email.strip()]
            safe_save_json(SETTINGS_FILE, settings)
            msg = 'Email settings saved successfully.'
        
        # Send test email
        elif 'send_test_email' in request.form:
            test_email = request.form.get('test_email', '')
            from notification import send_notification
            
            now = datetime.datetime.now()
            week_start = now.strftime('%Y-%m-%d')
            week_end = (now + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            
            try:
                success = send_notification("Test User", test_email, week_start, week_end, 
                                      now.isocalendar()[1], is_reminder=False)
                
                if success:
                    msg = f"Test email sent successfully to {test_email}"
                else:
                    msg = f"Failed to send test email. Please check email settings."
            except Exception as e:
                logger.error(f"Error sending test email: {str(e)}")
                msg = f"Error sending test email: {str(e)}"
      # BIAS logo removed as per requirements
    bias_logo = None
    
    return render_template_string('''
    <div style="max-width:700px;margin:40px auto;padding:2em 2.5em 1.5em 2.5em;background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <div style="display:flex;flex-direction:column;align-items:center;margin-bottom:1em;">            <div style="display:flex;align-items:center;margin-bottom:0.5em;">
                <span style="font-size:2em;font-weight:700;">BIAS</span>
            </div>
            <h1 style="text-align:center;color:#2a4365;margin:0.5em 0;">Admin Dashboard</h1>
        </div>
        <a href="{{ url_for('admin_logout') }}" style="float:right;color:#2563eb;">Logout</a>
        <a href="{{ url_for('dashboard') }}" style="float:right;color:#2563eb;margin-right:15px;">Dashboard</a>
        {% if msg %}<div style="color:green;margin-bottom:1em;">{{ msg }}</div>{% endif %}
        <h2>Personnel</h2>
        <table style="width:100%;border-collapse:collapse;margin-bottom:1.5em;">
            <tr style="background:#e0e7ef;"><th>Name</th><th>Email</th><th>Status</th><th>Action</th></tr>
            {% for p in personnel %}
            <tr>
                <td>{{ p['name'] }}</td>
                <td>{{ p['email'] }}</td>
                <td>{{ 'Active' if p['isActive'] else 'Inactive' }}</td>
                <td><a href="{{ url_for('remove_personnel', pid=p['id']) }}" style="color:red;">Remove</a></td>
            </tr>
            {% endfor %}
        </table>
        <form method="post" action="{{ url_for('add_personnel') }}">
            <h3>Add Personnel</h3>
            <input name="name" placeholder="Name" required style="margin-right:1em;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            <input name="email" placeholder="Email" required style="margin-right:1em;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            <button type="submit" style="background:#2563eb;color:#fff;padding:0.5em 1.2em;border:none;border-radius:5px;">Add</button>
        </form>
        
        <form method="post" style="margin-top:2em;">
            <h3>Set Schedule Start Person</h3>
            <p style="color:#64748b;margin-bottom:1em;">The schedule follows alphabetical order by default. Use this option to select which person should be first in the rotation.</p>
            <select name="start_person_id" style="padding:0.5em;border-radius:5px;border:1px solid #ccc;">
                {% for p in personnel %}
                <option value="{{ p['id'] }}">{{ p['name'] }}</option>
                {% endfor %}
            </select>
            <button type="submit" name="set_start_person" style="background:#2563eb;color:#fff;padding:0.5em 1.2em;border:none;border-radius:5px;">Set as Start</button>
        </form>

        <form method="post" action="{{ url_for('reset_order') }}" style="margin-top:1em;">
            <button type="submit" style="background:#d1d5db;color:#374151;padding:0.4em 0.9em;border:none;border-radius:5px;">Reset to Alphabetical Order</button>
        </form>
          <!-- Holiday section removed -->
        
        <h2 style="margin-top:2em;">System Settings</h2>
        <form method="post" action="{{ url_for('admin_dashboard') }}">
            <h3>Email Configuration</h3>
            <div style="margin-bottom:1em;">
                <input type="checkbox" id="notifications_enabled" name="notifications_enabled" {% if settings.get('email_settings', {}).get('notifications_enabled', False) %}checked{% endif %}>
                <label for="notifications_enabled">Enable Email Notifications</label>
            </div>
            <div style="margin-bottom:1em;">
                <label for="smtp_server">SMTP Server:</label><br>
                <input id="smtp_server" name="smtp_server" value="{{ settings.get('email_settings', {}).get('smtp_server', '') }}" style="width:100%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            </div>
            <div style="margin-bottom:1em;">
                <label for="smtp_port">SMTP Port:</label><br>
                <input id="smtp_port" name="smtp_port" type="number" value="{{ settings.get('email_settings', {}).get('smtp_port', 587) }}" style="width:100%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            </div>
            <div style="margin-bottom:1em;">
                <label for="sender_email">Sender Email:</label><br>
                <input id="sender_email" name="sender_email" value="{{ settings.get('email_settings', {}).get('sender_email', '') }}" style="width:100%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            </div>
            <div style="margin-bottom:1em;">
                <label for="sender_password">Password:</label><br>
                <input id="sender_password" name="sender_password" type="password" value="{{ settings.get('email_settings', {}).get('sender_password', '') }}" style="width:100%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            </div>
            <div style="margin-bottom:1em;">
                <label for="cc_emails">CC Emails (comma separated):</label><br>
                <input id="cc_emails" name="cc_emails" value="{{ settings.get('email_settings', {}).get('cc_emails', [])|join(',') }}" style="width:100%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            </div>
            <div style="margin-bottom:1em;">
                <label for="reminder_days">Send reminders this many days before duty:</label><br>
                <input id="reminder_days" name="reminder_days" type="number" value="{{ settings.get('email_settings', {}).get('reminder_days', 7) }}" style="width:100%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
            </div>
            <button type="submit" name="save_email_settings" style="background:#2563eb;color:#fff;padding:0.5em 1.2em;border:none;border-radius:5px;">Save Email Settings</button>
            
            <h3 style="margin-top:2em;">Test Email</h3>
            <div style="margin-bottom:1em;">
                <input id="test_email" name="test_email" placeholder="Email address for test" style="width:70%;padding:0.5em;border-radius:5px;border:1px solid #ccc;">
                <button type="submit" name="send_test_email" style="background:#2563eb;color:#fff;padding:0.5em 1.2em;border:none;border-radius:5px;">Send Test</button>
            </div>
        </form>
    </div>
    ''', personnel=personnel, settings=settings, msg=msg, bias_logo=bias_logo)

@app.route('/admin/add_personnel', methods=['POST'])
def add_personnel():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name or not email:
        flash('Name and email are required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    data = safe_load_json(PERSONNEL_FILE)
    
    # Generate new ID
    new_id = str(int(max([p['id'] for p in data['personnel']], default=0)) + 1)
    
    # Add new person
    data['personnel'].append({
        'id': new_id,
        'name': name,
        'email': email,
        'isActive': True
    })
    
    safe_save_json(PERSONNEL_FILE, data)
    
    flash('Personnel added successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_personnel/<pid>')
def remove_personnel(pid):
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    
    data = safe_load_json(PERSONNEL_FILE)
    for i, person in enumerate(data['personnel']):
        if person['id'] == pid:
            data['personnel'][i]['isActive'] = False
            break
    
    safe_save_json(PERSONNEL_FILE, data)
    
    flash('Personnel removed successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_holiday', methods=['POST'])
def add_holiday():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    
    # Holiday functionality removed
    flash('Holiday functionality has been removed from the system', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_holiday/<date>')
def remove_holiday(date):
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    
    # Holiday functionality removed
    flash('Holiday functionality has been removed from the system', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset_order', methods=['POST'])
def reset_order():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    
    # Reset the custom order in settings
    settings = safe_load_json(SETTINGS_FILE)
    settings['custom_order'] = []
    safe_save_json(SETTINGS_FILE, settings)
    
    flash('Schedule reset to alphabetical order', 'success')
    return redirect(url_for('admin_dashboard'))

# Main routes
@app.route("/")
def dashboard():
    current = get_person_for_week(0)
    previous = get_person_for_week(-1)
    upcoming = get_person_for_week(1)
    settings = load_settings()
    ui_settings = settings.get('ui_settings', {'dark_mode': False, 'show_week_numbers': True})
    
    # Get theme preference from cookie or default to settings
    theme_cookie = request.cookies.get('theme')
    dark_mode = theme_cookie == 'dark' if theme_cookie else ui_settings.get('dark_mode', False)
    
    # BIAS logo removed as per requirements
    bias_logo = None
    
    return render_template_string(TEMPLATE, 
                                current=current, 
                                previous=previous, 
                                upcoming=upcoming,
                                dark_mode=dark_mode,
                                show_week_numbers=ui_settings.get('show_week_numbers', True),
                                bias_logo=bias_logo)

@app.route("/toggle-theme")
def toggle_theme():
    """Toggle between light and dark mode"""
    current_theme = request.cookies.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    
    response = redirect(url_for('dashboard'))
    response.set_cookie('theme', new_theme, max_age=31536000)  # 1 year
    
    return response

@app.route("/calendar/<person_id>")
def generate_ical(person_id):
    """Generate and return an iCalendar file for the person's duty"""
    from calendar_util import generate_ical_for_person
    
    # Determine if this is for current or upcoming week
    current = get_person_for_week(0)
    upcoming = get_person_for_week(1)
    
    week_offset = 0
    if person_id == current['id']:
        week_offset = 0
    elif person_id == upcoming['id']:
        week_offset = 1
    else:
        # Try to find by ID without offset
        week_offset = 0
        
    ical_data = generate_ical_for_person(person_id, week_offset)
    
    if ical_data:
        from flask import Response
        response = Response(ical_data, mimetype='text/calendar')
        response.headers['Content-Disposition'] = f'attachment; filename=maintenance_duty_{person_id}.ics'
        return response
    else:
        flash('Could not generate calendar file.')
        return redirect(url_for('dashboard'))

@app.route('/health')
def health():
    """Simple health check for Azure"""
    return '{"status": "ok"}'

@app.route('/.well-known/microsoft-health-check')
def ms_health_check():
    """Azure App Service health check endpoint"""
    return '{"status": "healthy"}'

# This will only run when this script is executed directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
