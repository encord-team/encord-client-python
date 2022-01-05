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
from typing import Dict, Optional

import cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_ssh_private_key, Encoding, PublicFormat

import cord.exceptions

CORD_DOMAIN = 'https://api.cord.tech'
CORD_PUBLIC_PATH = '/public'
CORD_PUBLIC_USER_PATH = '/public/user'
CORD_ENDPOINT = CORD_DOMAIN + CORD_PUBLIC_PATH
CORD_USER_ENDPOINT = CORD_DOMAIN + CORD_PUBLIC_USER_PATH
WEBSOCKET_PATH = '/websocket'
WEBSOCKET_DOMAIN = 'wss://message-api.cord.tech'
WEBSOCKET_ENDPOINT = WEBSOCKET_DOMAIN + WEBSOCKET_PATH

_CORD_PROJECT_ID = 'CORD_PROJECT_ID'
_CORD_DATASET_ID = 'CORD_DATASET_ID'
_CORD_API_KEY = 'CORD_API_KEY'

READ_TIMEOUT = 180  # In seconds
WRITE_TIMEOUT = 180  # In seconds
CONNECT_TIMEOUT = 180  # In seconds

log = logging.getLogger(__name__)


class BaseConfig(ABC):
    def __init__(self, endpoint: str):
        self.read_timeout: int = READ_TIMEOUT
        self.write_timeout: int = WRITE_TIMEOUT
        self.connect_timeout: int = CONNECT_TIMEOUT

        self.endpoint: str = endpoint

    @abstractmethod
    def define_headers(self, data: str) -> Dict:
        pass


class Config(BaseConfig):
    """
    Config defining endpoint, project id, API key, and timeouts.
    """

    def define_headers(self, data) -> Dict:
        return self._headers

    def __init__(self,
                 resource_id: Optional[str] = None,
                 api_key: Optional[str] = None,
                 web_file_path: Optional[str] = None,
                 domain: Optional[str] = None,
                 websocket_endpoint: str = WEBSOCKET_ENDPOINT
                 ):

        if resource_id is None:
            resource_id = get_env_resource_id()

        if api_key is None:
            api_key = get_env_api_key()

        self.resource_id = resource_id
        self.api_key = api_key
        self.websocket_endpoint = websocket_endpoint
        self._headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'ResourceID': resource_id,
            'Authorization': self.api_key
        }
        if web_file_path is None:
            raise RuntimeError("`web_file_path` must be specified")
        if domain is None:
            raise RuntimeError("`domain` must be specified")

        self.domain = domain
        endpoint = domain + web_file_path
        super().__init__(endpoint)
        log.info("Initialising Cord client with endpoint: %s and resource_id: %s",
                 endpoint, resource_id)


def get_env_resource_id() -> str:
    if (_CORD_PROJECT_ID in os.environ) and (_CORD_DATASET_ID in os.environ):
        raise cord.exceptions.InitialisationError(
            message=(
                "Found both Project ID and Dataset ID in os.environ. "
                "Please initialise CordClient by passing resource_id."
            )
        )

    elif _CORD_PROJECT_ID in os.environ:
        resource_id = os.environ[_CORD_PROJECT_ID]

    elif _CORD_DATASET_ID in os.environ:
        resource_id = os.environ[_CORD_DATASET_ID]

    else:
        raise cord.exceptions.AuthenticationError(
            message="Project ID or dataset ID not provided"
        )

    return resource_id


def get_env_api_key() -> str:
    if _CORD_API_KEY not in os.environ:
        raise cord.exceptions.AuthenticationError(
            message="API key not provided"
        )

    return os.environ[_CORD_API_KEY]


class CordConfig(Config):
    def __init__(self, resource_id: Optional[str] = None, api_key: Optional[str] = None, domain: str = CORD_DOMAIN):
        web_file_path = CORD_PUBLIC_PATH
        super().__init__(resource_id, api_key, web_file_path=web_file_path, domain=domain)


class UserConfig(BaseConfig):
    def __init__(self, private_key: Ed25519PrivateKey, domain: str = CORD_DOMAIN):
        self.private_key: Ed25519PrivateKey = private_key
        self.public_key: Ed25519PublicKey = private_key.public_key()
        self._public_key_hex: str = self.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()

        self.domain = domain

        endpoint = domain + CORD_PUBLIC_USER_PATH
        super().__init__(endpoint)

    def define_headers(self, data: str) -> Dict:
        hash_builder = hashlib.sha256()
        hash_builder.update(data.encode())
        contents_hash = hash_builder.digest()

        signature = self.private_key.sign(contents_hash)

        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'{self._public_key_hex}:{signature.hex()}'
        }

    @staticmethod
    def from_ssh_private_key(ssh_private_key: str, password: Optional[str], **kwargs):
        key_bytes = ssh_private_key.encode()
        password_bytes = password and password.encode()
        private_key = cryptography.hazmat.primitives.serialization.load_ssh_private_key(key_bytes, password_bytes)

        if isinstance(private_key, Ed25519PrivateKey):
            return UserConfig(private_key, **kwargs)
        else:
            raise ValueError(f'Provided key [{ssh_private_key}] is not an Ed25519 private key')
