# stdlib imports
import datetime
import json

# third-party imports
from google.appengine.ext import db


class ModelEncoder(json.JSONEncoder):

    """
    Custom JSON encoder allowing easy encoding
    of appengine db entities to JSON.
    """

    def default(self, obj):

        # output dates/times in iso8601 format
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

        # convert GeoPt values to a simple dict
        if isinstance(obj, db.GeoPt):
            return {'lat': obj.lat, 'lon': obj.lon}

        return super(ModelEncoder, self).default(obj)
