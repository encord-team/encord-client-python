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
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from pickle import NONE
from typing import Dict, Literal, Optional

import cryptography
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
from encord.constants.string_constants import TYPE_DATASET, TYPE_PROJECT

ENCORD_DOMAIN = "https://api.cord.tech"  #: str: The end-point for interacting with the Encord API.
ENCORD_PUBLIC_PATH = "/public"
ENCORD_PUBLIC_USER_PATH = "/public/user"
ENCORD_ENDPOINT = ENCORD_DOMAIN + ENCORD_PUBLIC_PATH
ENCORD_USER_ENDPOINT = ENCORD_DOMAIN + ENCORD_PUBLIC_USER_PATH
WEBSOCKET_PATH = "/websocket"
WEBSOCKET_DOMAIN = "wss://message-api.cord.tech"
WEBSOCKET_ENDPOINT = WEBSOCKET_DOMAIN + WEBSOCKET_PATH

_CORD_PROJECT_ID = "CORD_PROJECT_ID"
_ENCORD_PROJECT_ID = "ENCORD_PROJECT_ID"
_CORD_DATASET_ID = "CORD_DATASET_ID"
_ENCORD_DATASET_ID = "ENCORD_DATASET_ID"
_CORD_API_KEY = "CORD_API_KEY"
_ENCORD_API_KEY = "ENCORD_API_KEY"
_ENCORD_SSH_KEY = "ENCORD_SSH_KEY"
_ENCORD_SSH_KEY_FILE = "ENCORD_SSH_KEY_FILE"

READ_TIMEOUT = 180  # In seconds
WRITE_TIMEOUT = 180  # In seconds
CONNECT_TIMEOUT = 180  # In seconds

logger = logging.getLogger(__name__)

from encord.exceptions import ResourceNotFoundError


class BaseConfig(ABC):
    def __init__(self, endpoint: str):
        self.read_timeout: int = READ_TIMEOUT
        self.write_timeout: int = WRITE_TIMEOUT
        self.connect_timeout: int = CONNECT_TIMEOUT

        self.endpoint: str = endpoint

    @abstractmethod
    def define_headers(self, data: str) -> Dict:
        pass


def _get_signature(data: str, private_key: Ed25519PrivateKey) -> bytes:
    hash_builder = hashlib.sha256()
    hash_builder.update(data.encode())
    contents_hash = hash_builder.digest()

    return private_key.sign(contents_hash)


def _get_ssh_authorization_header(public_key_hex: str, signature: bytes) -> str:
    return f"{public_key_hex}:{signature.hex()}"


class UserConfig(BaseConfig):
    def __init__(self, private_key: Ed25519PrivateKey, domain: str = ENCORD_DOMAIN):
        self.private_key: Ed25519PrivateKey = private_key
        self.public_key: Ed25519PublicKey = private_key.public_key()  # DENIS: check if I can hide this.
        #  DENIS: make this public?
        self._public_key_hex: str = self.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()

        self.domain = domain

        endpoint = domain + ENCORD_PUBLIC_USER_PATH
        super().__init__(endpoint)

    def define_headers(self, data: str) -> Dict:
        signature = _get_signature(data, self.private_key)

        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": _get_ssh_authorization_header(self._public_key_hex, signature),
        }

    @staticmethod
    def from_ssh_private_key(ssh_private_key: str, password: Optional[str] = "", **kwargs):
        """
        Instantiate a UserConfig object by the content of a private ssh key.

        Args:
            ssh_private_key: The content of a private key file.
            password: The password for the private key file.

        Returns:
            UserConfig.

        Raises:
            ValueError: If the provided key content is not of the correct format.

        """
        key_bytes = ssh_private_key.encode()
        password_bytes = password and password.encode()
        private_key = cryptography.hazmat.primitives.serialization.load_ssh_private_key(key_bytes, password_bytes)

        if isinstance(private_key, Ed25519PrivateKey):
            return UserConfig(private_key, **kwargs)
        else:
            raise ValueError(f"Provided key [{ssh_private_key}] is not an Ed25519 private key")


class Config(BaseConfig):
    """
    Config defining endpoint, project id, API key, and timeouts.
    """

    # def define_headers(self, data) -> Dict:
    #     return self._headers

    def __init__(
        self,
        resource_id: Optional[str] = None,
        # DENIS: cannot remove the api_key for backwards compatibility.
        # api_key: Optional[str] = None,
        web_file_path: str = ENCORD_PUBLIC_PATH,
        domain: Optional[str] = None,
        websocket_endpoint: str = WEBSOCKET_ENDPOINT,
    ):

        if resource_id is None:
            resource_id = get_env_resource_id()

        self.resource_id = resource_id
        # self.api_key = api_key
        self.websocket_endpoint = websocket_endpoint
        # self._headers = {
        #     "Accept": "application/json",
        #     "Content-Type": "application/json",
        #     "ResourceID": resource_id,
        #     "Authorization": self.api_key,
        # }
        if domain is None:
            raise RuntimeError("`domain` must be specified")

        self.domain = domain
        endpoint = domain + web_file_path
        super().__init__(endpoint)
        logger.info("Initialising Encord client with endpoint: %s and resource_id: %s", endpoint, resource_id)


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

        with open(ssh_file) as f:
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
    ):
        web_file_path = ENCORD_PUBLIC_PATH
        if api_key is None:
            api_key = get_env_api_key()

        self.api_key = api_key
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "ResourceID": resource_id,
            "Authorization": self.api_key,
        }
        super().__init__(resource_id, web_file_path=web_file_path, domain=domain)

    def define_headers(self, data) -> Dict:
        return self._headers


EncordConfig = ApiKeyConfig


class SshConfig(Config):
    def __init__(
        self,
        user_config: UserConfig,
        resource_type: str,  # DENIS: typed?
        resource_id: Optional[str] = None,
        domain: Optional[str] = None,
    ):
        self._user_config = user_config
        self._resource_type = resource_type
        # self.resource_id = resource_id
        super().__init__(resource_id=resource_id, domain=domain)

    def define_headers(self, data: str) -> Dict:
        signature = _get_signature(data, self._user_config.private_key)
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "ResourceID": self.resource_id,
            "ResourceType": self._resource_type,
            "Authorization": _get_ssh_authorization_header(self._user_config._public_key_hex, signature),
        }


CordConfig = EncordConfig
