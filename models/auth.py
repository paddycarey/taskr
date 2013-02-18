# stdlib imports
import datetime
import hashlib
import json
import urllib

# third-party imports
import webapp2
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from oauth2client.client import OAuth2WebServerFlow

# local imports
import secrets
from models.base import BaseModel
from utils.appinfo import application_url
from utils.errors import AccessTokenRefreshError


class User(BaseModel):

    """
    This model stores all user profile data
    and has helper functions to aid in retrieving
    and managing oauth credentials.
    """

    # User profile data (scraped from G+ profile)
    user_id = ndb.StringProperty()
    user_email = ndb.StringProperty()
    given_name = ndb.StringProperty()
    family_name = ndb.StringProperty()
    profile_link = ndb.StringProperty()

    # does this user have admin access?
    is_admin = ndb.BooleanProperty(default=False)

    @property
    def has_profile(self):

        """
        Returns a boolean indicating whether this user
        has a complete profile.  Usually used to decide
        whether to update the profile from the Google
        userinfo API.
        """

        profile_keys = ['given_name',
                        'family_name',
                        'profile_link',
                        'user_email',
                        'user_id']
        if None in (getattr(self, x) for x in profile_keys):
            return False
        return True

    @property
    def gravatar(self):

        """
        Returns a URL to the user's Gravatar, with
        a configurable default
        """

        # get hash of email address
        email_hash = hashlib.md5(self.user_email.lower()).hexdigest()
        # extra url parameters (image size, etc.)
        url_params = urllib.urlencode({'s': str(48)})
        # construct the url
        gravatar_url = "//www.gravatar.com/avatar/"
        gravatar_url = gravatar_url + email_hash + "?"
        gravatar_url += url_params
        # return image url
        return gravatar_url

    #########################################
    # OAuth2 related methods and properties #
    #########################################

    # OAuth2 credentials
    access_token = ndb.StringProperty()
    access_token_expiry_time = ndb.DateTimeProperty()
    refresh_token = ndb.StringProperty()

    # OAuth2 helper methods/properties
    pickled_flow = ndb.PickleProperty()

    def get_flow(self):

        """
        Returns a flow object to initiate the OAuth2 dance.
        Creates if required and stores in the datastore for easy retrieval.
        """

        # return flow from datastore if present
        if self.pickled_flow is not None:
            return self.pickled_flow
        # flow not stored so we need to build one
        self.pickled_flow = OAuth2WebServerFlow(
            client_id=secrets.GDATA_CLIENT_ID,
            client_secret=secrets.GDATA_CLIENT_SECRET,
            scope='https://www.googleapis.com/auth/userinfo.profile',
            redirect_uri=application_url() + webapp2.uri_for('oauth-callback'),
            approval_prompt='force'
        )
        # force save the model so as to store the flow
        self.put()
        return self.pickled_flow

    def set_credentials(self, code):

        """
        Takes an auth code and converts it to an
        access token, saving it on the model.
        """

        # swap code for token using oauth2client lib
        credentials = self.get_flow().step2_exchange(code)
        # set credentials props
        self.access_token = credentials.access_token
        self.refresh_token = credentials.refresh_token
        self.access_token_expiry_time = datetime.datetime.utcnow()
        # store model
        self.put()

    def has_credentials(self):

        """
        Naive check to see if this user's access
        token and refresh token have been set.
        """

        if self.access_token is None:
            return False
        if self.refresh_token is None:
            return False
        return True

    def refresh_auth(self):

        """
        Refresh this user's access token
        """

        # url to get new token
        token_uri = 'https://accounts.google.com/o/oauth2/token'
        # build required url params
        body = urllib.urlencode({
            'grant_type': 'refresh_token',
            'client_id': secrets.GDATA_CLIENT_ID,
            'client_secret': secrets.GDATA_CLIENT_SECRET,
            'refresh_token': self.refresh_token})
        # set required request headers
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        # make HTTP call to refresh token
        response = urlfetch.fetch(token_uri,
            method='POST',
            payload=body,
            headers=headers)
        # check if response was successful
        if response.status_code == 200:
            # load json content
            response_json = json.loads(response.content)
            # parse access token from response
            self.access_token = response_json['access_token']
            # store the model and return None
            return self.put()

        # raise an access token error if request failed
        raise AccessTokenRefreshError
