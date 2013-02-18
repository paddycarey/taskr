"""
taskr!

this is our main wsgi entry point so any
initial setup should happen here
"""
# stdlib imports
import os
import sys

# third-party imports
import webapp2

# local imports
import settings
import routes

# Add lib directory to path
sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, 'lib'))

# Define our WSGI app so GAE can run it
wsgi = webapp2.WSGIApplication(
    routes.ROUTES,
    debug=settings.DEBUG,
    config=settings.WSGI_CONFIG
)
