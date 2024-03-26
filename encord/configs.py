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
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_ssh_private_key,
)

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

from requests import PreparedRequest

from encord.http.v2.request_signer import sign_request


class BaseConfig(ABC):
    def __init__(self, endpoint: str, requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS):
        self.read_timeout: int = requests_settings.read_timeout
        self.write_timeout: int = requests_settings.write_timeout
        self.connect_timeout: int = requests_settings.connect_timeout

        self.endpoint: str = endpoint
        self.requests_settings = requests_settings

    @abstractmethod
    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        pass


def _get_signature(data: str, private_key: Ed25519PrivateKey) -> bytes:
    hash_builder = hashlib.sha256()
    hash_builder.update(data.encode())
    contents_hash = hash_builder.digest()

    return private_key.sign(contents_hash)


def _get_ssh_authorization_header(public_key_hex: str, signature: bytes) -> str:
    return f"{public_key_hex}:{signature.hex()}"


class UserConfig(BaseConfig):
    """
    Just a wrapper redirecting some of the requests towards the "/public/user" endpoint rather than just "/public"
    """

    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        super().__init__(endpoint=config.domain + ENCORD_PUBLIC_USER_PATH, requests_settings=config.requests_settings)

    @property
    def domain(self) -> str:
        return self.config.domain

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        return self.config.define_headers(resource_id, resource_type, data)

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        return self.config.define_headers_v2(request)


class Config(BaseConfig):
    """
    Config defining endpoint, project id, API key, and timeouts.
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


def get_env_resource_id() -> str:
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
    api_key = os.environ.get(_ENCORD_API_KEY) or os.environ.get(_CORD_API_KEY)
    if api_key is None:
        raise encord.exceptions.AuthenticationError(message="API key not provided")

    return api_key


def get_env_ssh_key() -> str:
    """
    Returns the raw ssh key by looking up the `ENCORD_SSH_KEY_FILE` and `ENCORD_SSH_KEY` environment variables
    in the mentioned order and returns the first successfully identified key.
    """
    # == 1. Look for key file
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

    # == 2. Look for raw key
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
        return self._headers

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        raise NotImplementedError("API key authorization is not supported for the Encord API v2")


EncordConfig = ApiKeyConfig
CordConfig = EncordConfig


class SshConfig(Config):
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

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        signature = _get_signature(data, self.private_key)
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
            "ResourceType": resource_type or "",
            "ResourceID": resource_id or "",
            "Authorization": _get_ssh_authorization_header(self.public_key_hex, signature),
        }

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        return sign_request(request, self.public_key_hex, self.private_key)

    @staticmethod
    def from_ssh_private_key(
        ssh_private_key: str,
        password: Optional[str] = "",
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        **kwargs,
    ) -> SshConfig:
        """
        Instantiate a UserConfig object by the content of a private ssh key.

        Args:
            ssh_private_key: The content of a private key file.
            password: The password for the private key file.
            requests_settings: The requests settings for all outgoing network requests.

        Returns:
            UserConfig.

        Raises:
            ValueError: If the provided key content is not of the correct format.

        """
        key_bytes = ssh_private_key.encode()
        password_bytes = password.encode() if password else None
        private_key = load_ssh_private_key(key_bytes, password_bytes)

        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError(f"Provided key [{ssh_private_key}] is not an Ed25519 private key")

        return SshConfig(private_key, requests_settings=requests_settings, **kwargs)


class BearerConfig(Config):
    def __init__(
        self,
        token: str,
        domain: str = ENCORD_DOMAIN,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
    ):
        self.token = token
        super().__init__(domain=domain, requests_settings=requests_settings)

    def define_headers(self, resource_id: Optional[str], resource_type: Optional[str], data: str) -> Dict[str, Any]:
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "ResourceID": resource_id or "",
            "ResourceType": resource_type or "",
            "Authorization": f"Bearer {self.token}",
        }

    def define_headers_v2(self, request: PreparedRequest) -> PreparedRequest:
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request

    @staticmethod
    def from_bearer_token(
        token: str,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        **kwargs,
    ) -> BearerConfig:
        return BearerConfig(token=token, requests_settings=requests_settings, **kwargs)
