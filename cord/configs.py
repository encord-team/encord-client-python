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
_CORD_API_KEY = 'CORD_API_KEY'

READ_TIMEOUT = 15  # In seconds
WRITE_TIMEOUT = 30  # In seconds
CONNECT_TIMEOUT = 15  # In seconds

log = logging.getLogger(__name__)


class Config(metaclass=ABCMeta):
    """
    Config defining endpoint, project id, API key, and timeouts.
    """
    def __init__(self,
                 project_id=None,
                 api_key=None,
                 endpoint=CORD_ENDPOINT
                 ):

        if project_id is None:
            if _CORD_PROJECT_ID not in os.environ:
                raise cord.exceptions.AuthenticationError(
                    message="Project ID not provided"
                )

            project_id = os.environ[_CORD_PROJECT_ID]

        if api_key is None:
            if _CORD_API_KEY not in os.environ:
                raise cord.exceptions.AuthenticationError(
                    message="API key not provided"
                )

            api_key = os.environ[_CORD_API_KEY]

        self.project_id = project_id
        self.api_key = api_key

        self.read_timeout = READ_TIMEOUT
        self.write_timeout = WRITE_TIMEOUT
        self.connect_timeout = CONNECT_TIMEOUT

        self.endpoint = endpoint
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'ProjectID': '%s' % project_id,
            'Authorization': '%s' % api_key,
        }

        log.info("Initialised Cord client with endpoint: %s and project_id: %s", endpoint, project_id)


class CordConfig(Config):
    def __init__(self, project_id=None, api_key=None):
        super(CordConfig, self).__init__(project_id, api_key)
