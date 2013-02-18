# stdlib imports
import datetime

# third-party imports
from google.appengine.ext import ndb

# local imports
from models.base import BaseModel


class Comment(BaseModel):

    """
    A very simple comment model used to
    allow users to comment on tasks.
    """

    # relationships to task and user models
    task = ndb.KeyProperty()
    user = ndb.KeyProperty()
    # text property for comment body
    comment = ndb.StringProperty(indexed=False)

    def age(self):

        """
        Returns a timedelta indicating how old this comment
        is. Can be used to display relative times in the UI.
        """

        # current UTC time
        now = datetime.datetime.utcnow()
        # calculate timedelta and return
        return now - self.creation_time

    def put(self, *args, **kwargs):
        super(Comment, self).put(*args, **kwargs)
        # save associated task to datastore
        task = self.task.get()
        task.put()
