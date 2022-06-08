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

from encord.exceptions import ServerError


def check_error_response(error_string: str, error_code: int, payload=None):
    """
    Checks server response.
    Called if HTTP response status code is an error response.
    """
    if payload is not None:
        payload = " with the following message: " + payload
    message = f"The server has reported an error response with error code `{error_code}` and error string `{error_string}`{payload}"
    raise ServerError(message)
