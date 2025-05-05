import os
import logging
import app

if __name__ == '__main__':
    # Configure detailed logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('app').setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    logging.getLogger('flask').setLevel(logging.DEBUG)
    
    # Enable debug mode for detailed error messages
    app.app.debug = True
    app.app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    
    # Set admin credentials for testing
    os.environ['ADMIN_USERNAME'] = 'admin'
    os.environ['ADMIN_PASSWORD'] = 'admin123'
    
    # Print out the current configuration
    print("Admin username:", os.environ.get('ADMIN_USERNAME'))
    print("Admin password:", os.environ.get('ADMIN_PASSWORD'))
    print("Secret key:", app.app.secret_key)
    
    # Run the app
    app.app.run(host='127.0.0.1', port=8000)
