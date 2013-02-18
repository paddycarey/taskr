# stdlib imports
import datetime

# third-party imports
import webapp2
from google.appengine.ext import ndb

# local imports
from models.base import BaseModel


class History(BaseModel):

    """
    A very simple comment model used to
    allow users to comment on tasks.
    """

    # relationship to object that was changed
    entity = ndb.KeyProperty()
    # relationship to user that made change
    user = ndb.KeyProperty()
    # text property for comment body
    description = ndb.StringProperty(indexed=False)

    @property
    def when(self):

        """
        Returns a timedelta indicating how old this comment
        is. Can be used to display relative times in the UI.
        """

        # current UTC time
        now = datetime.datetime.utcnow()
        # calculate timedelta and return
        return now - self.creation_time

    @property
    def who(self):
        user = self.user.get()
        return user.given_name + ' ' + user.family_name

    def what(self):
        entity = self.entity.get()
        entity_name = entity.name
        entity_link = webapp2.uri_for('task-view', task_id=entity.key.urlsafe())
        return {'name': entity_name, 'link': entity_link}


def add_to_history(task, user, description):
    task_key = task.key
    user_key = user.key
    history = History(parent=task.key)
    history.entity = task_key
    history.user = user_key
    history.description = description
    history.put()
