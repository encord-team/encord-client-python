#
# Copyright (c) 2020 Cord Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import datetime
import json

from collections import OrderedDict


class BaseORM(dict):
    """ Base ORM for all database objects. """

    DB_FIELDS = OrderedDict()
    NON_UPDATABLE_FIELDS = {}

    def __init__(self, dic):
        """
        Construct client ORM compatible database object from dict object, ensures strict type and attribute name check
        The real k,v is stored in inner dict
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
                        types = types,
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
            logging.error("Error init", exc_info=True)
            raise Exception("Convert failed {}".format(str(e)))

    def __getattr__(self, name):
        """
        Override attribute method for easy access of field value in business logic instead of ["attr"]
        Return None if there is no such attribute
        :param name:
        :return:
        """
        if name in self:
            try:
                return self[name]
            except KeyError as e:
                return None
        else:
            raise AttributeError("Attribute does not exist: {}".format(name))

    def __setattr__(self, name, value):
        """
        Strict attribute name and type check
        :param name:
        :param value:
        :return:
        """
        if name in self.DB_FIELDS and (value is None or isinstance(value, self.DB_FIELDS[name])):
            self[name] = value
        else:
            raise AttributeError("Attribute name or type not match: {}".format(name))

    def __delattr__(self, name):
        if name in self and name in self.DB_FIELDS:
            del self[name]
        else:
            super().__delattr__(self, name)

    @staticmethod
    def from_db_row(row, db_field):
        """
        Static method for conveniently converting db row to client object
        :param row:
        :param db_field:
        :return:
        """
        temp_dict = {}
        for i, attribute in enumerate(db_field):
            temp_dict[attribute] = row[i]
        return temp_dict

    def to_dic(self, time_str=True):
        """
        Conveniently set client object as dict
        Only considers the dict items, no other object attr will be counted
        :param time_str: time_str, if set to True, will convert datetime field to str with format %Y-%m-%d %H:%M:%S
        If False, will keep the original datetime type. By default will be True.
        :return:
        """
        res = {}
        for k, v in self.items():
            if isinstance(v, datetime.datetime) and time_str is True:
                v = v.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(v, dict):
                v = json.dumps(v)
            res[k] = v

        return res

    def updatable_fields(self):
        for k, v in self.items():
            if k not in self.NON_UPDATABLE_FIELDS and v is not None:
                yield k, v
