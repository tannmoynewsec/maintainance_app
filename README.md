# Maintenance Support Scheduler App

A flexible maintenance support scheduler for teams that need to manage support rotation. This project has been streamlined for deployment to Azure App Service Free tier.

> **Note:** The application has been fully cleaned up and is ready for deployment. All required files are included in the root directory.
> 
> **Note:** If you see a `clean_deployment` directory, it can be safely deleted. It was used during the cleanup process but is no longer needed.

## Features

- **Personnel Rotation Tracking**: Automatically rotates through team members for support duties based on alphabetical order
- **Holiday Awareness**: Skips holiday weeks in the rotation
- **Custom Order**: Set priority or custom rotation order
- **Web Interface**: Easy-to-use browser interface to view and manage schedules
- **Admin Dashboard**: Comprehensive admin tools for managing personnel and settings
- **Email Notifications**: Automated reminders for upcoming support duties
- **Calendar Integration**: Generate calendar invites to add to personal calendars
- **Dark Mode**: Toggle between light and dark themes
- **Export Functionality**: Export schedule to CSV or iCalendar formats
- **Mobile Responsive**: Works well on mobile devices

## Project Structure

This is a simplified, cleaned-up version of the project with only the essential files needed for deployment:

### Core Application Files
- `app.py`: Main Flask application
- `wsgi.py`: WSGI entry point for Azure App Service
- `main.py`: Command-line version of the scheduler
- `admin.py`: Command-line administration tools
- `scheduler.py`: Scheduled tasks and reminders
- `notification.py`: Email notification functionality 
- `calendar_util.py`: Calendar integration utilities
- `export.py`: Export functionality

### Data Files
- `personnel.json`: Personnel information storage
- `holidays.json`: Holiday dates storage
- `settings.json`: Application settings storage

### Azure Deployment Files
- `requirements.txt`: Python dependencies
- `runtime.txt`: Specifies Python 3.10
- `.oryx_confi.json`: Oryx build system configuration
- `web.config`: IIS configuration for Python applications
- `startup.txt`: Defines the startup command
- `app.config.py`: Python application marker for Oryx
- `buildinfo.yml`: Build configuration information

## Getting Started

### Local Development

1. Ensure you have Python 3.10+ installed on your system.
2. Install required dependencies:
```
pip install -r requirements.txt
```
3. Run the application:
```
python wsgi.py
```
4. Open your browser and navigate to: `http://localhost:8000`

### Azure App Service Deployment

This application is specifically optimized for deployment to Azure App Service Free tier (F1):

#### Automated Deployment Script

Use the provided PowerShell deployment script to automatically deploy to Azure App Service Free tier:

```
.\deploy_to_azure.ps1
```

This script:
1. Creates a resource group if it doesn't exist
2. Creates an App Service Plan with **explicitly configured F1 (Free) tier**
3. Creates a web app within the free tier plan
4. Configures all necessary settings
5. Deploys the application code
6. Validates that the Free tier is being used

> **Note:** The script requires Azure CLI to be installed and you to be logged in.

#### Manual Deployment

If you prefer manual deployment:

1. Create an Azure App Service with Python 3.10 runtime on **F1 (Free) tier**
2. Add these app settings:
   - PYTHON_VERSION=3.10
   - SCM_DO_BUILD_DURING_DEPLOYMENT=true
   - ENABLE_ORYX_BUILD=true
   - ORYX_PLATFORM=python
   - WEBSITES_PORT=8000
   - APP_SERVICE_PLAN_TIER=Free
3. Deploy the code to the App Service

#### Free Tier Limitations

Be aware of these Free tier (F1) limitations:
- 1 GB disk space
- 60 minutes compute per day
- Shared infrastructure
- No scaling capability
- No custom domains

## Admin Features

### Web-based Admin Panel (Recommended)

You can manage personnel and holidays directly from your browser when the app is running (locally or on Azure):

1. Go to `http://localhost:8000/admin` (or your Azure URL `/admin`)
2. Login with:
   - **Username:** `admin`
   - **Password:** `admin123`
3. Use the dashboard to add/remove personnel and holidays.

> **Change the default admin password in `app.py` before deploying to production!**

### Command Line Admin (Advanced)

You can also use the command line for advanced management:

```
python admin.py list-personnel
python admin.py add-person "Name" "email@example.com"
python admin.py edit-person <id> --name "New Name"
python admin.py remove-person <id>
python admin.py list-holidays
python admin.py add-holiday 2025-12-24 "Christmas Eve"
python admin.py pause-order
python admin.py resume-order
python admin.py reset-order
```

> **Note:** Command-line admin is only available on your local machine or via Azure Kudu/SSH.

## Rotation Order

By default, personnel are rotated alphabetically by name. Administrators can:

1. Set a specific person as the starting point in the rotation (while maintaining the alphabetical sequence)
2. Reset the rotation to pure alphabetical order
3. Pause the rotation schedule when needed

These settings can be managed through the Admin Dashboard or using the command-line tools.
