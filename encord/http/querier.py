import dataclasses
import logging
import re
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, Type, TypeVar, Union

import orjson
import requests
import requests.exceptions
from requests import Session
from requests.adapters import HTTPAdapter, Retry

from encord.configs import BaseConfig
from encord.exceptions import RequestException, ResourceNotFoundError
from encord.http.common import (
    HEADER_CLOUD_TRACE_CONTEXT,
    RequestContext,
)
from encord.http.error_utils import check_error_response
from encord.http.query_methods import QueryMethods
from encord.http.request import Request, UIDType
from encord.orm.base_dto import BaseDTO
from encord.orm.formatter import Formatter

logger = logging.getLogger(__name__)


class Querier:
    """Querier for DB get/post requests."""

    T = TypeVar("T")
    PayloadType = Union[None, Dict[str, Any], BaseDTO, Sequence[Dict[str, Any]], Sequence[BaseDTO]]

    def __init__(self, config: BaseConfig, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        self._config = config
        self.resource_type = resource_type
        self.resource_id = resource_id

    def basic_getter(
        self, response_type: Type[T], uid: UIDType = None, payload: PayloadType = None, retryable=True
    ) -> T:
        """Single DB object getter."""
        request = self._request(
            QueryMethods.GET, self._route(response_type), uid, self._config.read_timeout, payload=payload
        )
        res, context = self._execute(request, retryable=retryable)
        if res:
            return self._parse_response(response_type, res)
        else:
            raise ResourceNotFoundError("Resource not found.", context=context)

    def get_multiple(
        self,
        response_type: Type[T],
        uid: UIDType = None,
        payload: PayloadType = None,
        retryable=True,
        query_type: Optional[Type[Any]] = None,
    ) -> List[T]:
        return self._request_multiple(
            QueryMethods.GET, response_type, uid, payload, retryable=retryable, query_type=query_type
        )

    def post_multiple(
        self, response_type: Type[T], uid: UIDType = None, payload: PayloadType = None, retryable=False
    ) -> List[T]:
        return self._request_multiple(QueryMethods.POST, response_type, uid, payload)

    def put_multiple(
        self, response_type: Type[T], uid: UIDType = None, payload: PayloadType = None, retryable=False
    ) -> List[T]:
        return self._request_multiple(QueryMethods.PUT, response_type, uid, payload)

    def _request_multiple(
        self,
        method: QueryMethods,
        response_type: Type[T],
        uid: UIDType,
        payload: PayloadType = None,
        retryable=False,
        query_type: Optional[Type[Any]] = None,
    ) -> List[T]:
        request = self._request(
            method, self._route(response_type, query_type), uid, self._config.read_timeout, payload=payload
        )
        result, context = self._execute(request, retryable=retryable)

        if result is not None:
            return [self._parse_response(response_type, item) for item in result]
        else:
            raise ResourceNotFoundError(
                f"[{response_type}] not found for query with uid=[{uid}] and payload=[{payload}]",
                context=context,
            )

    @staticmethod
    def _parse_response(response_type: Type[T], item: Dict[str, Any]) -> T:
        if issubclass(response_type, BaseDTO):
            return response_type.from_dict(item)  # type: ignore
        if issubclass(response_type, Formatter):
            return response_type.from_dict(item)  # type: ignore
        elif dataclasses.is_dataclass(response_type):
            return response_type(**item)  # type: ignore
        else:
            return response_type(item)  # type: ignore

    @staticmethod
    def _serialise_payload(payload: PayloadType) -> Union[None, Dict[str, Any], List[Dict[str, Any]]]:
        if isinstance(payload, BaseDTO):
            return payload.to_dict()
        elif isinstance(payload, Sequence) and all(isinstance(x, BaseDTO) for x in payload):
            return [x.to_dict() for x in payload]  # type: ignore
        else:
            return payload  # type: ignore

    def basic_delete(self, query_type: Type[T], uid: UIDType = None, retryable=False):
        """Single DB object getter."""
        request = self._request(
            QueryMethods.DELETE,
            self._route(query_type),
            uid,
            self._config.read_timeout,
        )

        res, _ = self._execute(request, retryable=retryable)
        return res

    def basic_setter(self, query_type: Type[T], uid: UIDType, payload: PayloadType, retryable=False):
        """Single DB object setter."""
        request = self._request(
            QueryMethods.POST,
            self._route(query_type),
            uid,
            self._config.write_timeout,
            payload=payload,
        )

        res, context = self._execute(request, retryable=retryable)

        if res is not None:
            return res
        else:
            raise RequestException(f"Setting {query_type} with uid {uid} failed.", context=context)

    def basic_put(self, query_type, uid, payload: PayloadType, retryable: bool = True, enable_logging: bool = True):
        """Single DB object put request."""
        request = self._request(
            QueryMethods.PUT,
            self._route(query_type),
            uid,
            self._config.write_timeout,
            payload=payload,
        )

        res, context = self._execute(request, retryable=retryable, enable_logging=enable_logging)

        if res:
            return res
        else:
            raise RequestException(f"Setting {query_type} with uid {uid} failed.", context=context)

    def _exception_context(self, request: requests.PreparedRequest) -> RequestContext:
        try:
            domain: Optional[str] = _domain_from_endpoint(self._config.endpoint)
        except Exception:
            domain = None
        try:
            x_cloud_trace_context = request.headers.get(HEADER_CLOUD_TRACE_CONTEXT)
            if x_cloud_trace_context is None:
                return RequestContext(domain=domain)

            x_cloud_trace_context = x_cloud_trace_context.split(";")[0]
            trace_id, span_id = (x_cloud_trace_context.split("/") + [None, None])[:2]
            return RequestContext(trace_id=trace_id, span_id=span_id, domain=domain)
        except Exception:
            return RequestContext(domain=domain)

    @staticmethod
    def _route(default_type: Type[T], query_type: Optional[Type[Any]] = None) -> str:
        """Resolve the backend routing key from a class name.

        By default, the request routes to the handler named after `default_type` (the response
        parse target for read requests, or the object type for writes). Pass `query_type` to
        route elsewhere — e.g. parse a response into a subclass while routing to the base
        class's handler.
        """
        return (query_type or default_type).__name__.lower()

    def _request(
        self,
        method: QueryMethods,
        query_type: str,
        uid: UIDType,
        timeout: int,
        payload: PayloadType = None,
    ):
        request = Request(
            method,
            query_type,
            uid,
            timeout,
            self._config.connect_timeout,
            self._serialise_payload(payload),
        )

        request.headers = self._config.define_headers(
            resource_id=self.resource_id, resource_type=self.resource_type, data=request.data
        )
        return request

    def _execute(self, request: Request, retryable=False, enable_logging: bool = True) -> Tuple[Any, RequestContext]:
        """Execute a request."""
        if enable_logging:
            logger.info("Request: %s", (request.data[:100] + "..") if len(request.data) > 100 else request.data)

        req = requests.Request(
            method=str(request.http_method),
            url=self._config.endpoint,
            headers=request.headers,
            data=request.data,
        ).prepare()

        context = self._exception_context(req)

        timeouts = (request.connect_timeout, request.timeout)

        req_settings = self._config.requests_settings
        with create_new_session(
            max_retries=req_settings.max_retries if retryable else 0,
            backoff_factor=req_settings.backoff_factor,
            connect_retries=req_settings.connection_retries,
        ) as session:
            try:
                res = session.send(req, timeout=timeouts)
            except Exception as e:
                raise RequestException(f"Request session.send failed {req.method=} {req.url=}", context=context) from e

            try:
                res_json = orjson.loads(res.content)
            except Exception as e:
                raise RequestException(f"Error parsing JSON response: {res.text.strip()}", context=context) from e

        # pylint: disable-next=no-member
        if res_json.get("status") != requests.codes.ok:
            response = res_json.get("response")
            extra_payload = res_json.get("payload")
            check_error_response(response, context, extra_payload)

        return res_json.get("response"), context


@contextmanager
def create_new_session(
    max_retries: Optional[int], backoff_factor: float, connect_retries: int, backoff_jitter: float = 0.0
) -> Generator[Session, None, None]:
    retry_policy = Retry(
        connect=connect_retries,
        read=max_retries,
        status=max_retries,  # type: ignore
        other=max_retries,  # type: ignore
        allowed_methods=["POST", "PUT", "GET"],  # type: ignore  # post is there since we use it for idempotent ops too.
        status_forcelist=[413, 429, 500, 502, 503],
        backoff_factor=backoff_factor,
        backoff_jitter=backoff_jitter,
        raise_on_status=False,
    )

    with Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=retry_policy))
        session.mount("https://", HTTPAdapter(max_retries=retry_policy))

        yield session


def _domain_from_endpoint(endpoint: str) -> str:
    return re.sub(r"(https?://[^/]+/).*", r"\1", endpoint)
