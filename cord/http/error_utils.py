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

from cord.exceptions import *

# Error messages
AUTHENTICATION_ERROR = ['AUTHENTICATION_ERROR']
AUTHORISATION_ERROR = ['AUTHORISATION_ERROR']
METHOD_NOT_ALLOWED_ERROR = ['METHOD_NOT_ALLOWED_ERROR']
UNKNOWN_ERROR = ['UNKNOWN_ERROR']
OPERATION_NOT_ALLOWED_ERROR = ['OPERATION_NOT_ALLOWED']
ANSWER_DICTIONARY_ERROR = ['ANSWER_DICTIONARY_ERROR']
CORRUPTED_LABEL_ERROR = ['CORRUPTED_LABEL_ERROR']
FILE_TYPE_NOT_SUPPORTED_ERROR = ['FILE_TYPE_NOT_SUPPORTED_ERROR']
UPLOAD_OPERATION_NOT_SUPPORTED_ERROR = ['UPLOAD_OPERATION_NOT_SUPPORTED_ERROR']
MUST_SET_DETECTION_RANGE_ERROR = ['MUST_SET_DETECTION_RANGE_ERROR']
DETECTION_RANGE_INVALID_ERROR = ['DETECTION_RANGE_INVALID_ERROR']
RESOURCE_EXISTS_ERROR = ['RESOURCE_EXISTS_ERROR']


def check_error_response(response, payload=None):
    """
    Checks server response.
    Called if HTTP response status code is an error response.
    """
    if response == AUTHENTICATION_ERROR:
        raise AuthenticationError("Invalid API key.")

    if response == AUTHORISATION_ERROR:
        raise AuthorisationError("You are not authorised to access this asset.")

    if response == METHOD_NOT_ALLOWED_ERROR:
        raise MethodNotAllowedError("HTTP method is not allowed.")

    if response == UNKNOWN_ERROR:
        raise UnknownException("An unknown error occurred.")

    if response == OPERATION_NOT_ALLOWED_ERROR:
        raise OperationNotAllowed("The read/write operation is not allowed by the API key.")

    if response == ANSWER_DICTIONARY_ERROR:
        raise AnswerDictionaryError("An object or classification is missing in the answer dictionaries.")

    if response == CORRUPTED_LABEL_ERROR:
        raise CorruptedLabelError("The label blurb is corrupted. This could be due to the number of "
                                  "frame labels exceeding the number of frames in the labelled video.")

    if response == FILE_TYPE_NOT_SUPPORTED_ERROR:
        raise FileTypeNotSupportedError("Supported file types are: image/jpeg, image/png, video/webm, video/mp4.")

    if response == UPLOAD_OPERATION_NOT_SUPPORTED_ERROR:
        raise UploadOperationNotSupportedError("Uploading a file to an external (e.g. S3/GCP/Azure) dataset is not "
                                               "permitted.")

    if response == DETECTION_RANGE_INVALID_ERROR:
        raise DetectionRangeInvalidError("The detection range is invalid (e.g. less than 0, or"
                                         " higher than num frames in the video)")

    if response == RESOURCE_EXISTS_ERROR:
        raise ResourceExistsError(
            "Trying to create a resource that already exists."
            "Label hash for this data is: " + str(payload)
        )

    pass
