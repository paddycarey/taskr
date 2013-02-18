# stdlib imports
import os

# third-party imports
from google.appengine.api import app_identity

# local imports
import settings


def application_id():

    """
    Get the current application's appengine id
    """

    # get the appengine id using the app_identity service
    return app_identity.get_application_id()


def application_url():

    """
    Get the application's current serving hostname by using the app_identity
    service.  Uses https:// by default for all appspot urls.

    URLs can be manually over-ridden by setting a URL_MAP value in settings.py
    URL_MAP = {'someapp.appspot.com': 'https://www.somedomain.com'}
    """

    # check if running on the dev server
    on_dev = os.environ['SERVER_SOFTWARE'].startswith('Development')

    # get URL_MAP value from settings.py
    URL_MAP = getattr(settings, 'URL_MAP', {})

    # use the app_identity service to get the app's default hostname
    hostname = app_identity.get_default_version_hostname()

    # check if the url has been mapped in settings
    if hostname in URL_MAP:
        app_url = URL_MAP[hostname]
    # use the appspot url over https://
    elif on_dev:
        app_url = 'http://' + hostname
    else:
        app_url = 'https://' + hostname

    # return this application's current url
    return app_url
