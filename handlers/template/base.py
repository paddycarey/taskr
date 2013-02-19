"""
Base template handlers
"""
# stdlib imports
import logging

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
from utils.auth import is_admin

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

        context = {

            # add request and session objects to default context
            'request': self.request,
            'session': self.session,

            # helper funcs which can be used within templates
            'format_timedelta': format_timedelta,
            'is_admin': is_admin,
            'len': len,
            'uri_for': self.uri_for,

        }

        # check if user is logged in
        user = users.get_current_user()
        if user is not None:
            # get user from datastore
            user_key = 'user-' + user.user_id()
            user_entity = User.get_by_id(user_key)
            # add user to context
            context['user'] = user_entity
        else:
            context['user'] = None

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
