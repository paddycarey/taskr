# stdlib imports
import os
import sys

# local imports
import settings

# Add lib directory to path
sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, 'lib'))
appstats_CALC_RPC_COSTS = True


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
