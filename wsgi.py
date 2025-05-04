#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("wsgi")

# Log startup information
logger.info(f"Starting WSGI application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {sys.path}")

try:
    # Find and log environmental variables that might affect the port
    for env_var in ['PORT', 'WEBSITES_PORT', 'HTTP_PLATFORM_PORT']:
        logger.info(f"{env_var}: {os.environ.get(env_var, 'Not set')}")
    # Import the Flask application
    from app import app as application
    logger.info("Successfully imported app.py")
    
    # Also make the app available as 'app' for gunicorn to find it
    app = application
    
    # Add a simple health check endpoint directly in WSGI for fallback
    @application.route('/wsgi-health')
    def wsgi_health():
        logger.info("WSGI health check called")
        return '{"status": "healthy", "from": "wsgi"}', 200, {'Content-Type': 'application/json'}
    
except Exception as e:
    logger.error(f"Error importing app.py: {str(e)}")
    logger.error(f"PYTHONPATH: {sys.path}")
    logger.error(f"Contents of directory: {os.listdir('.')}")
    # Re-raise to ensure proper error reporting
    raise

# Run the app when script is executed directly
if __name__ == '__main__':
    # Get port from various environment variables that Azure might set
    port = int(os.environ.get('WEBSITES_PORT', os.environ.get('PORT', 8000)))
    logger.info(f"Starting application on port {port}")
    application.run(host='0.0.0.0', port=port)
