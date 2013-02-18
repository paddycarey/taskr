# stdlib imports
import json
import logging

# third-party imports
from google.appengine.api import urlfetch
from google.appengine.api import users

# local imports
from handlers.base import TemplateHandler
from models.auth import User
from utils.errors import AccessTokenRefreshError
from utils.errors import UnauthorisedError


class AuthedTemplateHandler(TemplateHandler):

    """
    All template handlers which require authorisation as
    a user should subclass this one and implemet the
    handle_get method (ignore the name, it works just
    fine with POST handlers too)
    """

    def update_profile(self, user_email=None):

        """
        Update a user's profile by calling the Google UserInfo API
        """

        # API endpoint URL
        url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        # set request headers
        headers = {'Authorization': 'OAuth %s' % self.user_entity.access_token}
        # make API request
        response = urlfetch.fetch(url, headers=headers)
        # check if we got an unauthorised response
        if response.status_code in [401, 403]:
            raise UnauthorisedError
        # load JSON response content
        response_json = json.loads(response.content)
        # set user properties from response
        self.user_entity.user_id = response_json['id']
        self.user_entity.given_name = response_json['given_name']
        self.user_entity.family_name = response_json['family_name']
        self.user_entity.profile_link = response_json['link']
        # set user's email address if passed
        if user_email is not None:
            self.user_entity.user_email = user_email
        # store user entity
        return self.user_entity.put()

    def get(self, *args, **kwargs):

        # make sure user is logged in
        user = users.get_current_user()
        if user is None:
            # redirect user to login page if not logged in
            login_url = users.create_login_url(self.request.path_qs)
            return self.redirect(login_url)

        # get or create user entity in datastore
        user_key = 'user-' + user.user_id()
        self.user_entity = User.get_or_insert(user_key)

        # check if the user entity has credentials
        if not self.user_entity.has_credentials():
            # create flow to begin oauth dance
            flow = self.user_entity.get_flow()
            flow.params['state'] = self.request.path_qs
            # get oauth2 redirect url
            auth_url = flow.step1_get_authorize_url()
            # redirect to El Goog
            return self.redirect(auth_url)

        # check if the user has a fully populated profile
        if not self.user_entity.has_profile:
            try:
                # attempt to update profile
                self.update_profile(user_email=user.email())
            except UnauthorisedError:
                try:
                    # refresh the auth token if not authorised
                    self.user_entity.refresh_auth()
                except AccessTokenRefreshError:
                    # log access token refresh error
                    logging.warning('Unable to refresh access token for user')
                else:
                    self.update_profile(user_email=user.email())

        # return our actual handler method
        return self.handle_get(*args, **kwargs)


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
