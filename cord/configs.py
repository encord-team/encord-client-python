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

import os
import logging

from abc import ABCMeta
import cord.exceptions
 
CORD_ENDPOINT = 'https://api.cord.tech/public'

_CORD_PROJECT_ID = 'CORD_PROJECT_ID'
_CORD_DATASET_ID = 'CORD_DATASET_ID'
_CORD_API_KEY = 'CORD_API_KEY'

READ_TIMEOUT = 180  # In seconds
WRITE_TIMEOUT = 180  # In seconds
CONNECT_TIMEOUT = 180  # In seconds

log = logging.getLogger(__name__)


class Config(metaclass=ABCMeta):
    """
    Config defining endpoint, project id, API key, and timeouts.
    """
    def __init__(self,
                 resource_id=None,
                 api_key=None,
                 endpoint=CORD_ENDPOINT
                 ):

        if resource_id is None:
            resource_id = get_env_resource_id()

        if api_key is None:
            api_key = get_env_api_key()

        self.resource_id = resource_id
        self.api_key = api_key
        self.read_timeout = READ_TIMEOUT
        self.write_timeout = WRITE_TIMEOUT
        self.connect_timeout = CONNECT_TIMEOUT
        self.endpoint = endpoint
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'ResourceID': '%s' % resource_id,
            'Authorization': '%s' % api_key,
        }

        log.info("Initialising Cord client with endpoint: %s and resource_id: %s",
                 endpoint, resource_id)


def get_env_resource_id():
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


def get_env_api_key():
    if _CORD_API_KEY not in os.environ:
        raise cord.exceptions.AuthenticationError(
            message="API key not provided"
        )

    return os.environ[_CORD_API_KEY]


class CordConfig(Config):
    def __init__(self, resource_id=None, api_key=None):
        super().__init__(resource_id, api_key)
