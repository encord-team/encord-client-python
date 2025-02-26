import datetime
import json
import logging
from collections import OrderedDict, abc

logger = logging.getLogger(__name__)


class BaseORM(dict):
    """Base ORM for all database objects."""

    DB_FIELDS: OrderedDict = OrderedDict()
    NON_UPDATABLE_FIELDS: set = set()

    def __init__(self, dic):
        """Construct client ORM compatible database object from dict object.
        Ensures strict type and attribute name check.
        The real k,v is stored in inner dict.
        :param dic:
        """
        try:
            if not isinstance(dic, dict):
                raise TypeError("Need dict object")
            value = {}
            for k, v in dic.items():
                if k in self.DB_FIELDS:
                    types = self.DB_FIELDS[k]
                    # Convert all types to tuple
                    if not isinstance(types, tuple):
                        types = (types,)
                    # None value is allowed for some cases
                    if v is None:
                        value[k] = v
                    # Normal cases where type matches required types
                    elif isinstance(v, types):
                        value[k] = v
                    # Bool value is same as 0,1 in db
                    elif v in (0, 1) and bool in types:
                        value[k] = v
                    # Datetime type but actually a datetime str is provided
                    elif datetime.datetime in types:
                        real_v = datetime.datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                        value[k] = real_v
                    elif dict in types:
                        value[k] = v
            super().__init__(**value)
        except Exception as e:
            logger.error("Error init", exc_info=True)
            raise Exception(f"Convert failed {e}")

    def __getattr__(self, name):
        """Override attribute method for easy access of field value.
        To be used instead of ["attr"].
        Return None if there is no such attribute
        :param name:
        :return:
        """
        if name in self:
            try:
                return self[name]
            except KeyError:
                return None
        else:
            raise AttributeError(f"Attribute does not exist: {name}")

    def __setattr__(self, name, value):
        """Strict attribute name and type check.
        :param name:
        :param value:
        :return:
        """
        if name in self.DB_FIELDS and (value is None or isinstance(value, self.DB_FIELDS[name])):
            self[name] = value
        else:
            raise AttributeError(f"Attribute name or type not match: {name}")

    def __delattr__(self, name):
        if name in self and name in self.DB_FIELDS:
            del self[name]
        else:
            super().__delattr__(name)


class BaseListORM(list):
    """A wrapper for a list of objects of a specific ORM."""

    BASE_ORM_TYPE = BaseORM

    def __init__(self, iter_):
        if not isinstance(iter_, abc.Iterable):
            raise Exception("Convert failed. The object is not an iterable.")

        values = []
        for item in iter_:
            try:
                v = self.BASE_ORM_TYPE(item)
                values.append(v)
            except Exception as e:
                logger.error("Error init", exc_info=True)
                raise Exception(f"Convert failed {e}")
        super().__init__(values)
