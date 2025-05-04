### Python detection marker file
# This file helps Oryx correctly identify this as a Python application
# The presence of this file along with requirements.txt ensures Python detection

# Python version
PYTHON_VERSION = "3.10"

# Application type
APP_TYPE = "Flask"

# Required files
REQUIRED_FILES = [
    "requirements.txt",
    "wsgi.py",
    "app.py"
]

# Middleware
MIDDLEWARE = []

# Static files configuration
STATIC_ROOT = "static"
STATIC_URL = "/static/"
