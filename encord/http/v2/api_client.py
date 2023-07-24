import platform
from pathlib import Path
from typing import Optional, Type, TypeVar
from urllib.parse import urljoin

import requests
from requests import Response

from encord._version import __version__ as encord_version
from encord.configs import UserConfig
from encord.exceptions import RequestException
from encord.http.common import (
    HEADER_CLOUD_TRACE_CONTEXT,
    HEADER_USER_AGENT,
    RequestContext,
)
from encord.http.utils import create_new_session
from encord.http.v2.error_utils import handle_error_response
from encord.http.v2.request_signer import sign_request
from encord.orm.base_dto import BaseDTO, BaseDTOInterface

T = TypeVar("T", bound=BaseDTOInterface)


class ApiClient:
    def __init__(self, config: UserConfig):
        self._config = config
        self._domain = self._config.domain
        self._base_path = Path("v2/public/")

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

    @staticmethod
    def _user_agent():
        return f"encord-sdk-python/{encord_version} python/{platform.python_version()}"

    def _bulid_url(self, path: Path) -> str:
        return urljoin(self._domain, str(self._base_path / path))

    def _headers(self):
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            HEADER_USER_AGENT: self._user_agent(),
        }

    def get(self, path: Path, params: Optional[BaseDTO], result_type: Type[T]) -> T:
        params_dict = params.to_dict() if params is not None else None
        req = requests.Request(
            method="GET", url=self._bulid_url(path), headers=self._headers(), params=params_dict
        ).prepare()

        req = sign_request(req, self._config.public_key_hex, self._config.private_key)

        timeouts = (self._config.write_timeout, self._config.read_timeout)
        req_settings = self._config.requests_settings
        with create_new_session(
            max_retries=req_settings.max_retries, backoff_factor=req_settings.backoff_factor
        ) as session:
            res = session.send(req, timeout=timeouts)
            context = self._exception_context_from_response(res)

            if res.status_code != 200:
                self._handle_error(res, context)

            try:
                res_json = res.json()
            except Exception as e:
                raise RequestException(f"Error parsing JSON response: {res.text}", context=context) from e

            return result_type.from_dict(res_json)

    @staticmethod
    def _handle_error(response: Response, context: RequestContext):
        try:
            description = response.json()
            handle_error_response(response.status_code, context=context, message=description["message"])
        except Exception:
            handle_error_response(response.status_code, context=context)
