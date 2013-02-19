# third-party imports
from google.appengine.api import users

# local imports
from handlers.template.base import TemplateHandler


class IndexHandler(TemplateHandler):

    """
    Serves the index page shown to all unauthenticated users
    """

    def get(self):

        # redirect to projects page if already logged in
        if users.get_current_user() is not None:
            redirect_url = self.uri_for('projects')
            return self.redirect(redirect_url)

        # render and return login page
        return self.render_response('login.html', {})
