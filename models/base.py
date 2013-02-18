"""
Simple base model to provide common
functions/properties for all our datastore entities.
"""
# stdlib imports
import json

# third-party imports
from google.appengine.ext import ndb

# local imports
from utils.encoder import ModelEncoder as ModelEnc


class BaseModel(ndb.Model):

    # record creation and modification times of entity
    creation_time = ndb.DateTimeProperty(auto_now_add=True)
    modification_time = ndb.DateTimeProperty(auto_now=True)

    def to_json(self, skipkeys=False):
        return json.dumps(self.to_dict(), cls=ModelEnc, skipkeys=skipkeys)
