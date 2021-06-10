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

import requests
from requests import Session, Timeout
from requests.adapters import HTTPAdapter
import requests.exceptions
from requests.packages.urllib3.util import Retry

from cord.exceptions import *
from cord.http.error_utils import check_error_response
from cord.http.query_methods import QueryMethods
from cord.http.request import Request


class Querier:
    """ Querier for DB get/post requests. """
    def __init__(self, config):
        self._config = config

    def basic_getter(self, db_object_type, uid=None):
        """ Single DB object getter. """
        request = self.request(
            QueryMethods.GET,
            db_object_type,
            uid,
            self._config.read_timeout,
        )
        res = self.execute(request)
        if res:
            return db_object_type(res)
        else:
            raise ResourceNotFoundError("Resource not found.")

    def basic_setter(self, db_object_type, uid, payload):
        """ Single DB object setter. """
        request = self.request(
            QueryMethods.POST,
            db_object_type,
            uid,
            self._config.write_timeout,
            payload=payload,
        )

        res = self.execute(request)

        if res:
            return res
        else:
            raise RequestException("Setting %s with uid %s failed." % (db_object_type, uid))

    def basic_put(self, db_object_type, uid, payload):
        """ Single DB object put request. """
        request = self.request(
            QueryMethods.PUT,
            db_object_type,
            uid,
            self._config.write_timeout,
            payload=payload,
        )

        res = self.execute(request)

        if res:
            return res
        else:
            raise RequestException("Setting %s with uid %s failed." % (db_object_type, uid))

    def request(self, method, db_object_type, uid, timeout, payload=None):
        """ Request object constructor. """
        return Request(
            method,
            db_object_type,
            uid,
            self._config.headers,
            timeout,
            self._config.connect_timeout,
            payload,
        )

    def execute(self, request):
        """ Execute a request. """
        logging.info("Request: %s", (request.data[:100] + '..') if len(request.data) > 100 else request.data)

        session = Session()
        session.mount("https://", HTTPAdapter(max_retries=Retry(connect=0)))

        req = requests.Request(
            method=request.http_method,
            url=self._config.endpoint,
            headers=request.headers,
            data=request.data,
        ).prepare()

        timeouts = (request.connect_timeout, request.timeout)

        try:
            res = session.send(req, timeout=timeouts)
        except Timeout as e:
            raise TimeOutError(str(e))
        except RequestException as e:
            raise RequestException(str(e))
        except Exception as e:
            raise UnknownException(str(e))

        try:
            res_json = res.json()
        except Exception:
            raise CordException("Error parsing JSON response: %s" % res.text)

        if res_json.get("status") != requests.codes.ok:
            response = res_json.get("response")
            extra_payload = res_json.get("payload")
            check_error_response(response, extra_payload)

        session.close()

        return res_json.get("response")
