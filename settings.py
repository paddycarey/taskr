"""
Non-confidential project settings
"""
# slib imports
import os

# local imports
import secrets

# Convenience property to allow modules to quickly
# reference the project's root directory from anywhere
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Set debug mode based on whether we're running locally or not
DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development')

# Extra WSGI config
WSGI_CONFIG = {
    'webapp2_extras.sessions': {
        'secret_key': secrets.SESSION_KEY,
    }
}
