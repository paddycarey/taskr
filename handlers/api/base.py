"""
Base handlers
"""
# stdlib imports
import json
import logging
import sys

# third-party imports
import webapp2
from httplib import HTTPException
from raven import Client

# local imports
import secrets

# check if sentry enabled
client = Client(secrets.SENTRY_DSN)


class JsonHandler(webapp2.RequestHandler):

    """
    Simple webapp2 base handler to return JSON data from API endpoints
    """

    def render_response(self, context):

        """
        Accepts a JSON encoded string or object which can be serialised to
        JSON and outputs it to the response as a JSON encoded string.
        """

        # if object is a string just return as is
        if isinstance(context, basestring):
            self.response.write(context)
        # else attempt to serialise and return
        else:
            context = json.dumps(context)
            self.response.write(context)
        # set the right content-type header
        self.response.headers['Content-Type'] = 'application/json'

    def handle_exception(self, exception, debug):

        """
        Override handle_exception() to send errors to our sentry
        server when not in DEBUG mode.
        """

        # build our error report
        error_report = {
            'method': self.request.method,
            'url': self.request.path_url,
            'query_string': self.request.query_string,
            # 'data': environ.get('wsgi.input'),
            'headers': dict(self.request.headers),
            'env': dict((
                    ('REMOTE_ADDR', self.request.environ['REMOTE_ADDR']),
                    ('SERVER_NAME', self.request.environ['SERVER_NAME']),
                    ('SERVER_PORT', self.request.environ['SERVER_PORT']),
                )),
            }
        interface = 'sentry.interfaces.Http'

        try:
            client.captureException(data={interface: error_report})
        except HTTPException:
            logging.warning('Unable to contact sentry server')

        # Log the exception
        logging.exception(exception)

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
            status_code = exception.code
        else:
            self.response.set_status(500)
            status_code = 500

        # collect our error data
        exc_info = sys.exc_info()

        # Set a custom message.
        if status_code == 500:
            self.render_response({'error': 'A server error has occurred'})
        # otherwise return the error message's value
        else:
            self.render_response({'error': str(exc_info[1])})
