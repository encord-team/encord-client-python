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

from encord.exceptions import *


def check_error_response(response, payload=None):
    """
    Checks server response.
    Called if HTTP response status code is an error response.
    """
    message = f"The server has reported a response of type `{response}` with the following message: `{payload}`"
    raise ServerError(message)
