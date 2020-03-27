from sqlalchemy.ext.declarative import DeclarativeMeta
from json import JSONEncoder as BaseJSONEncoder
from datetime import datetime
from decimal import Decimal


class JSONEncoder(BaseJSONEncoder):
    """
    JSONEncoder used throughout the application.
    Handle Decimal, datetime and JSONizable objects.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S%z")
        return BaseJSONEncoder.default(self, obj)


def new_alchemy_encoder():
    _visited_objs = []

    class AlchemyEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj.__class__, DeclarativeMeta):
                # don't re-visit self
                if obj in _visited_objs:
                    return None
                _visited_objs.append(obj)

                # an SQLAlchemy class
                fields = {}
                for field in [
                        x for x in dir(obj)
                        if not x.startswith('_') and x != 'metadata'
                ]:
                    fields[field] = obj.__getattribute__(field)
                # a json-encodable dict
                return fields

            return JSONEncoder.default(self, obj)

    return AlchemyEncoder
