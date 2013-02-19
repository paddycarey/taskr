# stdlib imports
import json
import urlparse

# third-party imports
from google.appengine.api import urlfetch
from google.appengine.api import users

# local imports
from handlers.template.base import TemplateHandler
from models.auth import User
from utils.errors import UnauthorisedError


class UpdateProfileHandler(TemplateHandler):

    """
    Other handlers can redirect here if a user does not have
    a full profile and it will be forcibly updated
    """

    def call_api(self, access_token):

        """
        Make call to Google's userinfo API to retrieve user's profile info
        """

        # API endpoint URL
        url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        # set request headers
        headers = {'Authorization': 'OAuth %s' % access_token}

        # make API request
        response = urlfetch.fetch(url, headers=headers)
        # check if we got an unauthorised response
        if response.status_code in [401, 403]:
            raise UnauthorisedError

        # load JSON response content and return
        response_json = json.loads(response.content)
        return response_json

    def refresh_credentials(self, user_entity):

        """
        Force refesh a user's OAuth2 credentials
        """
        return user_entity.refresh_auth()

    def update_profile(self, user_entity, profile, email):

        """
        Update a user's profile and save to datastore
        """

        # set user properties from response
        user_entity.user_id = profile['id']
        user_entity.given_name = profile['given_name']
        user_entity.family_name = profile['family_name']
        user_entity.profile_link = profile['link']
        # set user's email address
        user_entity.user_email = email
        # store user entity
        return user_entity.put()

    def get(self, *args, **kwargs):

        # get url to redirect to after updating
        next_url = self.request.get('next_url', default_value='/')
        # check if next_url is relative or absolute
        if bool(urlparse.urlparse(next_url).scheme):
            # abort if absolute url is given
            return self.abort(400, detail="Only relative URLs allowed")

        # make sure user is logged in
        user = users.get_current_user()
        if user is None:
            # redirect user to login page if not logged in
            login_url = users.create_login_url(self.request.path_qs)
            return self.redirect(login_url)

        # get or create user entity in datastore
        user_key = 'user-' + user.user_id()
        user_entity = User.get_or_insert(user_key)

        # check if the user entity has credentials
        if not user_entity.has_credentials():
            # create flow to begin oauth dance
            flow = user_entity.get_flow()
            flow.params['state'] = self.request.path_qs
            # get oauth2 redirect url
            auth_url = flow.step1_get_authorize_url()
            # redirect to El Goog
            return self.redirect(auth_url)

        # check if the user has a fully populated profile
        if not user_entity.has_profile:
            try:
                profile = self.call_api(user_entity.access_token)
            except UnauthorisedError:
                # refresh the auth token if not authorised
                user_entity.refresh_auth()
                profile = self.call_api(user_entity.access_token)
            # save profile to user model
            self.update_profile(user_entity, profile, user.email())

        # check if the user has a fully populated profile after updating, if
        # not we'll dump the user out to a page telling them we couldn't
        # authorise or retrieve their profile
        if not user_entity.has_profile:
            redirect_url = self.uri_for('profile-update-error')
            return self.redirect(redirect_url)

        # return to the url we came here from initially
        return self.redirect(next_url)
