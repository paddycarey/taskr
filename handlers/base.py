"""
Base handlers
"""
# stdlib imports
import json
import logging
import sys

# third-party imports
import webapp2
from babel.dates import format_timedelta
from google.appengine.api import users
from httplib import HTTPException
from raven import Client
from webapp2_extras import jinja2
from webapp2_extras import sessions

# local imports
import secrets
from models.auth import User

# check if sentry enabled
client = Client(secrets.SENTRY_DSN)


class TemplateHandler(webapp2.RequestHandler):

    """
    Base handler for all handlers that require templating support
    """

    def dispatch(self):

        """
        Override dispatch() to provide session support
        """

        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    def default_context(self):

        """
        Returns a dictionary containing default
        context for all render calls
        """

        context = {}
        # func to get uri by name
        context['uri_for'] = self.uri_for
        # current request object
        context['request'] = self.request
        # len built-in
        context['len'] = len
        # current session object
        context['session'] = self.session
        # format_timedelta func for i18n formatting of times
        context['format_timedelta'] = format_timedelta
        # check if user is logged in
        user = users.get_current_user()
        if user is not None:
            # get user from datastore
            user_key = 'user-' + user.user_id()
            user_entity = User.get_by_id(user_key)
            # add user to context
            context['user'] = user_entity
            # check if user is admin
            is_local_admin = user_entity.is_admin
            is_app_admin = users.is_current_user_admin()
            is_admin = is_local_admin or is_app_admin
        else:
            # add user to context
            context['user'] = user
            is_admin = False
        # add admin status to context
        context['is_admin'] = is_admin
        # return default context
        return context

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, context):

        """
        Renders a template and writes the result to the response.
        """

        # update context with default context
        context.update(self.default_context())
        # render template
        rv = self.jinja2.render_template(_template, **context)
        # write rendered template to response
        return self.response.write(rv)

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
        super(TemplateHandler, self).handle_exception(exception, debug)


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
