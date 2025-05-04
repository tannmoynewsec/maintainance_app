#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script serves as an entry point for the Azure App Service to run
the Flask application using WSGI.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run")

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    logger.info(f"Added {current_dir} to Python path")

try:
    from wsgi import app as application
    logger.info("Successfully imported wsgi module")
except ImportError as e:
    logger.error(f"Error importing wsgi module: {e}")
    sys.exit(1)

if __name__ == '__main__':
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting application on port {port}")
    application.run(host='0.0.0.0', port=port)
