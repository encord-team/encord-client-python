"""
---
title: "Configs"
slug: "sdk-ref-configs"
hidden: false
metadata:
  title: "Configs"
  description: "Encord SDK Configs classes."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, ssh

import encord.exceptions
from encord.constants.string_constants import ALL_RESOURCE_TYPES
from encord.exceptions import ResourceNotFoundError
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS, RequestsSettings

ENCORD_DOMAIN = "https://api.encord.com"
ENCORD_PUBLIC_PATH = "/public"
ENCORD_PUBLIC_USER_PATH = "/public/user"
ENCORD_ENDPOINT = ENCORD_DOMAIN + ENCORD_PUBLIC_PATH
ENCORD_USER_ENDPOINT = ENCORD_DOMAIN + ENCORD_PUBLIC_USER_PATH
WEBSOCKET_PATH = "/websocket"
WEBSOCKET_DOMAIN = "wss://ws.encord.com"
WEBSOCKET_ENDPOINT = WEBSOCKET_DOMAIN + WEBSOCKET_PATH

_CORD_PROJECT_ID = "CORD_PROJECT_ID"
_ENCORD_PROJECT_ID = "ENCORD_PROJECT_ID"
_CORD_DATASET_ID = "CORD_DATASET_ID"
_ENCORD_DATASET_ID = "ENCORD_DATASET_ID"
_CORD_API_KEY = "CORD_API_KEY"
_ENCORD_API_KEY = "ENCORD_API_KEY"
_ENCORD_SSH_KEY = "ENCORD_SSH_KEY"
_ENCORD_SSH_KEY_FILE = "ENCORD_SSH_KEY_FILE"

logger = logging.getLogger(__name__)

import platform
from uuid import uuid4

from requests import PreparedRequest

from encord._version import __version__ as encord_version
from encord.http.common import (
    HEADER_CLOUD_TRACE_CONTEXT,
    HEADER_USER_AGENT,
)
from encord.http.v2.request_signer import sign_request


class BaseConfig(ABC):
    """
    Abstract base class for configuration.

    Args:
        endpoint (str): The API endpoint URL.
        requests_settings (RequestsSettings): Settings for HTTP requests.

    Attributes:
        read_timeout (int): Timeout for read operations.
        write_timeout (int): Timeout for write operations.
        connect_timeout (int): Timeout for connection operations.
        endpoint (str): The API endpoint URL.
        requests_settings (RequestsSettings): Settings for HTTP requests.
    """

    def __init__(self, endpoint: str, requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS):
        self.read_timeout: int = requests_settings.read_timeout
        self.write_timeout: int = requests_settings.write_timeout
        self.connect_timeout: int = requests_settings.connect_timeout

        self.endpoint: str = endpoint
        self.requests_settings = requests_settings

    @abstractmethod
    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        """
        Define headers for a request.

        Args:
            resource_id (Optional[str]): The resource ID.
            resource_type (Optional[str]): The resource type.
            data (str): The request data.

        Returns:
            Dict[str, Any]: A dictionary of headers.
        """
        pass

    @abstractmethod
    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        """
        Define headers for a request (v2).

        Args:
            request (PreparedRequest): The prepared request.

        Returns:
            PreparedRequest: The prepared request with headers defined.
        """
        pass


class UserConfig(BaseConfig):
    """
    Configuration for user-specific requests, redirecting to the "/public/user" endpoint.

    Args:
        config (Config): The base configuration.

    Attributes:
        config (Config): The base configuration.
    """

    def __init__(self, config: Config):
        self.config = config
        super().__init__(endpoint=config.domain + ENCORD_PUBLIC_USER_PATH, requests_settings=config.requests_settings)

    @property
    def domain(self) -> str:
        """
        Get the domain from the base configuration.

        Returns:
            str: The domain.
        """
        return self.config.domain

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        """
        Define headers for a user-specific request.

        Args:
            resource_id (Optional[str]): The resource ID.
            resource_type (Optional[str]): The resource type.
            data (str): The request data.

        Returns:
            Dict[str, Any]: A dictionary of headers.
        """
        return self.config.define_headers(resource_id, resource_type, data)

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        """
        Define headers for a user-specific request (v2).

        Args:
            request (PreparedRequest): The prepared request.

        Returns:
            PreparedRequest: The prepared request with headers defined.
        """
        return self.config.define_headers_v2(request)


class Config(BaseConfig):
    """
    Configuration defining endpoint, project ID, API key, and timeouts.

    Args:
        web_file_path (str): The web file path for the endpoint.
        domain (Optional[str]): The domain.
        websocket_endpoint (str): The WebSocket endpoint.
        requests_settings (RequestsSettings): Settings for HTTP requests.

    Attributes:
        websocket_endpoint (str): The WebSocket endpoint.
        domain (str): The domain.
    """

    def __init__(
        self,
        web_file_path: str = ENCORD_PUBLIC_PATH,
        domain: Optional[str] = None,
        websocket_endpoint: str = WEBSOCKET_ENDPOINT,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
    ):
        self.websocket_endpoint = websocket_endpoint
        if domain is None:
            raise RuntimeError("`domain` must be specified")

        self.domain = domain
        endpoint = domain + web_file_path
        super().__init__(endpoint, requests_settings=requests_settings)

    @staticmethod
    def _user_agent() -> str:
        return f"encord-sdk-python/{encord_version} python/{platform.python_version()}"

    def _tracing_id(self) -> str:
        if self.requests_settings.trace_id_provider:
            return self.requests_settings.trace_id_provider()
        return f"{uuid4().hex}/1;o=1"


def get_env_resource_id() -> str:
    """
    Get the resource ID from environment variables.

    Returns:
        str: The resource ID.

    Raises:
        encord.exceptions.InitialisationError: If both project and dataset IDs are found.
        encord.exceptions.AuthenticationError: If no project or dataset ID is found.
    """
    project_id = os.environ.get(_ENCORD_PROJECT_ID) or os.environ.get(_CORD_PROJECT_ID)
    dataset_id = os.environ.get(_ENCORD_DATASET_ID) or os.environ.get(_CORD_DATASET_ID)
    if (project_id is not None) and (dataset_id is not None):
        raise encord.exceptions.InitialisationError(
            message=(
                "Found both Project EntityId and Dataset EntityId in os.environ. "
                "Please initialise EncordClient by passing resource_id."
            )
        )

    elif project_id is not None:
        resource_id = project_id

    elif dataset_id is not None:
        resource_id = dataset_id

    else:
        raise encord.exceptions.AuthenticationError(message="Project EntityId or dataset EntityId not provided")

    return resource_id


def get_env_api_key() -> str:
    """
    Get the API key from environment variables.

    Returns:
        str: The API key.

    Raises:
        encord.exceptions.AuthenticationError: If no API key is found.
    """
    api_key = os.environ.get(_ENCORD_API_KEY) or os.environ.get(_CORD_API_KEY)
    if api_key is None:
        raise encord.exceptions.AuthenticationError(message="API key not provided")

    return api_key


def get_env_ssh_key() -> str:
    """
    Get the raw SSH key from environment variables.

    Returns:
        str: The raw SSH key.

    Raises:
        ResourceNotFoundError: If the SSH key file or key is not found or is empty.
    """
    ssh_file = os.environ.get(_ENCORD_SSH_KEY_FILE)
    if ssh_file:
        ssh_file = os.path.abspath(os.path.expanduser(ssh_file))
        if not os.path.exists(ssh_file):
            raise ResourceNotFoundError(
                f"SSH key file `{ssh_file}` which is defined in the `{_ENCORD_SSH_KEY_FILE}` environment variable does not seem to exist. "
                f"Failed to load private ssh key."
            )

        with open(ssh_file, encoding="ascii") as f:
            return f.read()

    raw_ssh_key = os.environ.get(_ENCORD_SSH_KEY)
    if raw_ssh_key is None:
        raise ResourceNotFoundError(
            f"Neither of the environment variables {_ENCORD_SSH_KEY_FILE} or {_ENCORD_SSH_KEY} were found. "
            f"Failed to load private ssh key."
        )

    if raw_ssh_key == "":
        raise ResourceNotFoundError(
            f"Environment variable {_ENCORD_SSH_KEY} found but is empty. " f"Failed to load private ssh key."
        )

    return raw_ssh_key


class ApiKeyConfig(Config):
    """
    Configuration for API key-based authorization.

    Args:
        resource_id (Optional[str]): The resource ID.
        api_key (Optional[str]): The API key.
        domain (Optional[str]): The domain.
        requests_settings (RequestsSettings): Settings for HTTP requests.

    Attributes:
        resource_id (Optional[str]): The resource ID.
        api_key (str): The API key.
        _headers (Dict[str, str]): Default headers for requests.
    """

    def __init__(
        self,
        resource_id: Optional[str] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
    ):
        web_file_path = ENCORD_PUBLIC_PATH
        if api_key is None:
            api_key = get_env_api_key()

        self.resource_id = resource_id
        self.api_key = api_key
        self._headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "ResourceID": resource_id,
            "Authorization": self.api_key,
        }
        super().__init__(web_file_path=web_file_path, domain=domain, requests_settings=requests_settings)

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        """
        Define headers for an API key-based request.

        Args:
            resource_id (Optional[str]): The resource ID.
            resource_type (Optional[str]): The resource type.
            data (str): The request data.

        Returns:
            Dict[str, Any]: A dictionary of headers.
        """
        return self._headers

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        """
        Define headers for an API key-based request (v2).

        Args:
            request (PreparedRequest): The prepared request.

        Raises:
            NotImplementedError: API key authorization is not supported for the Encord API v2.
        """
        raise NotImplementedError("API key authorization is not supported for the Encord API v2")


EncordConfig = ApiKeyConfig
CordConfig = EncordConfig


class SshConfig(Config):
    """
    Configuration for SSH key-based authorization.

    Args:
        private_key (Ed25519PrivateKey): The private SSH key.
        domain (str): The domain.
        requests_settings (RequestsSettings): Settings for HTTP requests.

    Attributes:
        private_key (Ed25519PrivateKey): The private SSH key.
        public_key (Ed25519PublicKey): The public SSH key.
        public_key_hex (str): The public key in hexadecimal format.
    """

    def __init__(
        self,
        private_key: Ed25519PrivateKey,
        domain: str = ENCORD_DOMAIN,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
    ):
        self.private_key: Ed25519PrivateKey = private_key
        self.public_key: Ed25519PublicKey = private_key.public_key()
        self.public_key_hex: str = self.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()

        super().__init__(domain=domain, requests_settings=requests_settings)

    @staticmethod
    def _get_v1_signature(data: str, private_key: Ed25519PrivateKey) -> bytes:
        hash_builder = hashlib.sha256()
        hash_builder.update(data.encode())
        contents_hash = hash_builder.digest()

        return private_key.sign(contents_hash)

    @staticmethod
    def _get_v1_ssh_authorization_header(public_key_hex: str, signature: bytes) -> str:
        return f"{public_key_hex}:{signature.hex()}"

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        """
        Define headers for an SSH key-based request.

        Args:
            resource_id (Optional[str]): The resource ID.
            resource_type (Optional[str]): The resource type.
            data (str): The request data.

        Returns:
            Dict[str, Any]: A dictionary of headers.
        """
        signature = self._get_v1_signature(data, self.private_key)
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
            "ResourceType": resource_type or "",
            "ResourceID": resource_id or "",
            "Authorization": self._get_v1_ssh_authorization_header(self.public_key_hex, signature),
            HEADER_USER_AGENT: self._user_agent(),
            HEADER_CLOUD_TRACE_CONTEXT: self._tracing_id(),
        }

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        """
        Define headers for an SSH key-based request (v2).

        Args:
            request (PreparedRequest): The prepared request.

        Returns:
            PreparedRequest: The prepared request with headers defined.
        """
        request.headers[HEADER_USER_AGENT] = self._user_agent()
        request.headers[HEADER_CLOUD_TRACE_CONTEXT] = self._tracing_id()

        return sign_request(request, self.public_key_hex, self.private_key)

    @staticmethod
    def from_ssh_private_key(
        ssh_private_key: str,
        password: Optional[str] = "",
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        **kwargs,
    ) -> SshConfig:
        """
        Instantiate a SshConfig object by the content of a private SSH key.

        Args:
            ssh_private_key: The content of a private key file.
            password: The password for the private key file.
            requests_settings: The requests settings for all outgoing network requests.

        Returns:
            SshConfig: The SSH configuration.

        Raises:
            ValueError: If the provided key content is not of the correct format.
        """
        key_bytes = ssh_private_key.encode()
        password_bytes = password.encode() if password else None
        private_key = ssh.load_ssh_private_key(key_bytes, password_bytes)

        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError(f"Provided key [{ssh_private_key}] is not an Ed25519 private key")

        return SshConfig(private_key, requests_settings=requests_settings, **kwargs)


class BearerConfig(Config):
    """
    Configuration for bearer token-based authorization.

    Args:
        token (str): The bearer token.
        domain (str): The domain.
        requests_settings (RequestsSettings): Settings for HTTP requests.

    Attributes:
        token (str): The bearer token.
    """

    def __init__(
        self,
        token: str,
        domain: str = ENCORD_DOMAIN,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
    ):
        self.token = token
        super().__init__(domain=domain, requests_settings=requests_settings)

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        """
        Define headers for a bearer token-based request.

        Args:
            resource_id (Optional[str]): The resource ID.
            resource_type (Optional[str]): The resource type.
            data (str): The request data.

        Returns:
            Dict[str, Any]: A dictionary of headers.
        """
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "ResourceID": resource_id or "",
            "ResourceType": resource_type or "",
            "Authorization": f"Bearer {self.token}",
            HEADER_USER_AGENT: self._user_agent(),
            HEADER_CLOUD_TRACE_CONTEXT: self._tracing_id(),
        }

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        """
        Define headers for a bearer token-based request (v2).

        Args:
            request (PreparedRequest): The prepared request.

        Returns:
            PreparedRequest: The prepared request with headers defined.
        """
        request.headers["Authorization"] = f"Bearer {self.token}"
        request.headers[HEADER_USER_AGENT] = self._user_agent()
        request.headers[HEADER_CLOUD_TRACE_CONTEXT] = self._tracing_id()

        return request

    @staticmethod
    def from_bearer_token(
        token: str,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        **kwargs,
    ) -> BearerConfig:
        """
        Instantiate a BearerConfig object using a bearer token.

        Args:
            token: The bearer token.
            requests_settings: The requests settings for all outgoing network requests.

        Returns:
            BearerConfig: The bearer token configuration.
        """
        return BearerConfig(token=token, requests_settings=requests_settings, **kwargs)
