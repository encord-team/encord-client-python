#
# Copyright (c) 2023 Cord Technologies Limited
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
import dataclasses
import logging
import platform
import random
import uuid
from contextlib import contextmanager
from typing import Any, Generator, List, Tuple, Type, TypeVar

import requests
import requests.exceptions
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from encord._version import __version__ as encord_version
from encord.configs import BaseConfig
from encord.exceptions import *
from encord.http.common import (
    HEADER_CLOUD_TRACE_CONTEXT,
    HEADER_USER_AGENT,
    RequestContext,
)
from encord.http.error_utils import check_error_response
from encord.http.query_methods import QueryMethods
from encord.http.request import Request
from encord.orm.formatter import Formatter

logger = logging.getLogger(__name__)


class Querier:
    """Querier for DB get/post requests."""

    T = TypeVar("T")

    def __init__(self, config: BaseConfig):
        self._config = config

    def basic_getter(self, db_object_type: Type[T], uid=None, payload=None) -> T:
        """Single DB object getter."""
        request = self._request(QueryMethods.GET, db_object_type, uid, self._config.read_timeout, payload=payload)
        res, context = self._execute(request)
        if res:
            return self._parse_response(db_object_type, res)
        else:
            raise ResourceNotFoundError("Resource not found.", context=context)

    def get_multiple(self, object_type: Type[T], uid=None, payload=None) -> List[T]:
        return self._request_multiple(QueryMethods.GET, object_type, uid, payload)

    def post_multiple(self, object_type: Type[T], uid=None, payload=None) -> List[T]:
        return self._request_multiple(QueryMethods.POST, object_type, uid, payload)

    def put_multiple(self, object_type: Type[T], uid=None, payload=None) -> List[T]:
        return self._request_multiple(QueryMethods.PUT, object_type, uid, payload)

    def _request_multiple(self, method: QueryMethods, object_type: Type[T], uid: List[str], payload=None) -> List[T]:
        request = self._request(method, object_type, uid, self._config.read_timeout, payload=payload)
        result, context = self._execute(request)

        if result is not None:
            return [self._parse_response(object_type, item) for item in result]
        else:
            raise ResourceNotFoundError(
                f"[{object_type}] not found for query with uid=[{uid}] and payload=[{payload}]", context=context
            )

    @staticmethod
    def _parse_response(object_type: Type[T], item: dict) -> T:
        if issubclass(object_type, Formatter):
            return object_type.from_dict(item)  # type: ignore
        elif dataclasses.is_dataclass(object_type):
            return object_type(**item)  # type: ignore
        else:
            return object_type(item)  # type: ignore

    def basic_delete(self, db_object_type: Type[T], uid=None):
        """Single DB object getter."""
        request = self._request(
            QueryMethods.DELETE,
            db_object_type,
            uid,
            self._config.read_timeout,
        )

        res, _ = self._execute(request)
        return res

    def basic_setter(self, db_object_type: Type[T], uid, payload):
        """Single DB object setter."""
        request = self._request(
            QueryMethods.POST,
            db_object_type,
            uid,
            self._config.write_timeout,
            payload=payload,
        )

        res, context = self._execute(request)

        if res is not None:
            return res
        else:
            raise RequestException(f"Setting {db_object_type} with uid {uid} failed.", context=context)

    def basic_put(self, db_object_type, uid, payload, enable_logging=True):
        """Single DB object put request."""
        request = self._request(
            QueryMethods.PUT,
            db_object_type,
            uid,
            self._config.write_timeout,
            payload=payload,
        )

        res, context = self._execute(request, enable_logging)

        if res:
            return res
        else:
            raise RequestException(f"Setting {db_object_type} with uid {uid} failed.", context=context)

    @staticmethod
    def _user_agent():
        return f"encord-sdk-python/{encord_version} python/{platform.python_version()}"

    @staticmethod
    def _tracing_id() -> str:
        return f"{uuid.uuid4().hex}/{random.randint(1, 2**63 - 1)};o=1"

    @staticmethod
    def _exception_context_from_response(response: Response) -> RequestContext:
        try:
            x_cloud_trace_context = response.headers.get(HEADER_CLOUD_TRACE_CONTEXT)
            if x_cloud_trace_context is None:
                return RequestContext()

            x_cloud_trace_context = x_cloud_trace_context.split(";")[0]
            trace_id, span_id = (x_cloud_trace_context.split("/") + [None, None])[:2]
            return RequestContext(trace_id=trace_id, span_id=span_id)
        except Exception:
            return RequestContext()

    def _request(self, method: QueryMethods, db_object_type: Type[T], uid, timeout, payload=None):
        request = Request(method, db_object_type, uid, timeout, self._config.connect_timeout, payload)

        request.headers = self._config.define_headers(request.data)
        request.headers[HEADER_USER_AGENT] = self._user_agent()
        request.headers[HEADER_CLOUD_TRACE_CONTEXT] = self._tracing_id()

        return request

    def _execute(self, request: Request, enable_logging=True) -> Tuple[Any, RequestContext]:
        """Execute a request."""
        if enable_logging:
            logger.info("Request: %s", (request.data[:100] + "..") if len(request.data) > 100 else request.data)

        req = requests.Request(
            method=str(request.http_method),
            url=self._config.endpoint,
            headers=request.headers,
            data=request.data,
        ).prepare()

        timeouts = (request.connect_timeout, request.timeout)

        req_settings = self._config.requests_settings
        with create_new_session(
            max_retries=req_settings.max_retries, backoff_factor=req_settings.backoff_factor
        ) as session:
            res = session.send(req, timeout=timeouts)
            context = self._exception_context_from_response(res)

            try:
                res_json = res.json()
            except Exception as e:
                raise RequestException(f"Error parsing JSON response: {res.text}", context=context) from e

        # pylint: disable-next=no-member
        if res_json.get("status") != requests.codes.ok:
            response = res_json.get("response")
            extra_payload = res_json.get("payload")
            check_error_response(response, context, extra_payload)

        return res_json.get("response"), context


@contextmanager
def create_new_session(max_retries: Optional[int] = None, backoff_factor: float = 0) -> Generator[Session, None, None]:
    retry_policy = Retry(total=max_retries, connect=max_retries, read=max_retries, backoff_factor=backoff_factor)

    with Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=retry_policy))
        session.mount("https://", HTTPAdapter(max_retries=retry_policy))

        yield session
