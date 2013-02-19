# third-party imports
from google.appengine.api import users

# local imports
from handlers.template.base import TemplateHandler
from models.auth import User


class AuthedTemplateHandler(TemplateHandler):

    """
    Base template handler providing authorisation support
    """

    def dispatch(self):

        """
        Override dispatch() to provide simple auth support
        """

        # make sure user is logged in
        user = users.get_current_user()
        if user is None:
            # redirect user to login page if not logged in
            redirect_url = users.create_login_url(self.request.path_qs)
            return self.redirect(redirect_url)

        # get user entity from datastore
        user_entity_id = 'user-' + user.user_id()
        user_entity = User.get_by_id(user_entity_id)

        # ensure user entity exists and has complete profile
        if user_entity is None or not user_entity.has_profile:
            redirect_url = self.uri_for('update-profile')
            return self.redirect(redirect_url)

        # we have valid auth so lets make the user_entity available class-wide
        self.user_entity = user_entity

        # Dispatch the request.
        TemplateHandler.dispatch(self)


class CallbackHandler(TemplateHandler):

    """
    OAuth2 Callback handler that stores
    credentials in the datastore
    """

    def get(self):

        # make sure user is logged in
        user = users.get_current_user()
        if user is None:
            self.abort(401)

        # make sure this is a valid oauth2 callback
        code = self.request.get('code', default_value=None)
        if code is None:
            return self.abort(400, detail='Not a valid OAuth2 callback')

        # pull user entity from datastore and set credentials
        user_key = 'user-' + user.user_id()
        user_entity = User.get_by_id(user_key)
        user_entity.set_credentials(code)

        # redirect to specified URL
        redirect_url = self.request.get('state')
        return self.redirect(redirect_url)
