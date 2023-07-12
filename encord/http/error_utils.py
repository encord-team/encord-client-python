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

from encord.exceptions import *

# Error messages
AUTHENTICATION_ERROR = ["AUTHENTICATION_ERROR"]
AUTHORISATION_ERROR = ["AUTHORISATION_ERROR"]
RESOURCE_NOT_FOUND_ERROR = ["RESOURCE_NOT_FOUND_ERROR"]
METHOD_NOT_ALLOWED_ERROR = ["METHOD_NOT_ALLOWED_ERROR"]
UNKNOWN_ERROR = ["UNKNOWN_ERROR"]
OPERATION_NOT_ALLOWED_ERROR = ["OPERATION_NOT_ALLOWED"]
ANSWER_DICTIONARY_ERROR = ["ANSWER_DICTIONARY_ERROR"]
CORRUPTED_LABEL_ERROR = ["CORRUPTED_LABEL_ERROR"]
FILE_TYPE_NOT_SUPPORTED_ERROR = ["FILE_TYPE_NOT_SUPPORTED_ERROR"]
FILE_SIZE_NOT_SUPPORTED_ERROR = ["FILE_SIZE_NOT_SUPPORTED_ERROR"]
FEATURE_DOES_NOT_EXIST_ERROR = ["FEATURE_DOES_NOT_EXIST_ERROR"]
MODEL_WEIGHTS_INCONSISTENT_ERROR = ["MODEL_WEIGHTS_INCONSISTENT_ERROR"]
MODEL_FEATURES_INCONSISTENT_ERROR = ["MODEL_FEATURES_INCONSISTENT_ERROR"]
UPLOAD_OPERATION_NOT_SUPPORTED_ERROR = ["UPLOAD_OPERATION_NOT_SUPPORTED_ERROR"]
MUST_SET_DETECTION_RANGE_ERROR = ["MUST_SET_DETECTION_RANGE_ERROR"]
DETECTION_RANGE_INVALID_ERROR = ["DETECTION_RANGE_INVALID_ERROR"]
RESOURCE_EXISTS_ERROR = ["RESOURCE_EXISTS_ERROR"]
INVALID_DATE_FORMAT_ERROR = ["INVALID_DATE_FORMAT_ERROR"]
DUPLICATE_SSH_KEY_ERROR = ["DUPLICATE_SSH_KEY_ERROR"]
SSH_KEY_NOT_FOUND_ERROR = ["SSH_KEY_NOT_FOUND_ERROR"]
INVALID_ARGUMENTS_ERROR = ["INVALID_ARGUMENTS_ERROR"]
MULTI_LABEL_LIMIT_ERROR = ["MULTI_LABEL_LIMIT_ERROR"]
WRONG_PROJECT_TYPE_ERROR = ["WRONG_PROJECT_TYPE_ERROR"]


def check_error_response(response, context=None, payload=None):
    """
    Checks server response.
    Called if HTTP response status code is an error response.
    """
    if response == AUTHENTICATION_ERROR:
        raise AuthenticationError("You are not authenticated to access the Encord platform.", context=context)

    if response == AUTHORISATION_ERROR:
        raise AuthorisationError("You are not authorised to access this asset.", context=context)

    if response == RESOURCE_NOT_FOUND_ERROR:
        if payload:
            raise ResourceNotFoundError(payload, context=context)
        raise ResourceNotFoundError("The requested resource was not found in the database.", context=context)

    if response == METHOD_NOT_ALLOWED_ERROR:
        raise MethodNotAllowedError("HTTP method is not allowed.", context=context)

    if response == UNKNOWN_ERROR:
        raise UnknownException("An unknown error occurred.", context=context)

    if response == OPERATION_NOT_ALLOWED_ERROR:
        raise OperationNotAllowed("The read/write operation is not allowed by the API key.", context=context)

    if response == ANSWER_DICTIONARY_ERROR:
        raise AnswerDictionaryError(
            "An object or classification is missing in the answer dictionaries.", context=context
        )

    if response == CORRUPTED_LABEL_ERROR:
        raise CorruptedLabelError(
            "The label blurb is corrupted. This could be due to the number of "
            "frame labels exceeding the number of frames in the labelled video.",
            context=context,
        )

    if response == FILE_TYPE_NOT_SUPPORTED_ERROR:
        raise FileTypeNotSupportedError(
            "Supported file types are: image/jpeg, image/png, video/webm, video/mp4.", context=context
        )

    if response == FILE_SIZE_NOT_SUPPORTED_ERROR:
        raise FileSizeNotSupportedError(
            "The combined size of the input files is larger than the supported limit", context=context
        )

    if response == FEATURE_DOES_NOT_EXIST_ERROR:
        raise FeatureDoesNotExistError("The passed feature does not exist in the project ontology.", context=context)

    if response == MODEL_WEIGHTS_INCONSISTENT_ERROR:
        raise ModelWeightsInconsistentError(
            "The passed model weights are incompatible with the selected model.", context=context
        )

    if response == MODEL_FEATURES_INCONSISTENT_ERROR:
        raise ModelFeaturesInconsistentError(
            "The passed features are incompatible with the selected model.", context=context
        )

    if response == UPLOAD_OPERATION_NOT_SUPPORTED_ERROR:
        raise UploadOperationNotSupportedError(
            "Uploading a file to an external (e.g. S3/GCP/Azure) dataset is not " "permitted.", context=context
        )

    if response == DETECTION_RANGE_INVALID_ERROR:
        raise DetectionRangeInvalidError(
            "The detection range is invalid (e.g. less than 0, or" " higher than num frames in the video)",
            context=context,
        )

    if response == INVALID_DATE_FORMAT_ERROR:
        raise InvalidDateFormatError("Invalid date format supplied as input", context=context)

    if response == RESOURCE_EXISTS_ERROR:
        raise ResourceExistsError(
            "Trying to create a resource that already exists. " "Payload for this failure is: " + str(payload),
            context=context,
        )

    if response == DUPLICATE_SSH_KEY_ERROR:
        raise DuplicateSshKeyError(
            "The used SSH key exists more than once. Please create a unique user SSH key.", context=context
        )

    if response == SSH_KEY_NOT_FOUND_ERROR:
        raise SshKeyNotFound(
            "The used SSH key does not exist on the Encord platform. Please add this SSH key to your user profile.",
            context=context,
        )

    if response == INVALID_ARGUMENTS_ERROR:
        default_message = "Some of the arguments to the SDK function were invalid."
        if payload is None:
            message = default_message
        else:
            message = payload
        raise InvalidArgumentsError(message, context=context)

    if response == MULTI_LABEL_LIMIT_ERROR:
        maximum_labels_allowed = payload["maximum_labels_allowed"]
        raise MultiLabelLimitError(
            f"Too many labels were requested. The limit is {maximum_labels_allowed}. Please reduce the amount "
            "of requested labels to stay under the reported limit.",
            maximum_labels_allowed=maximum_labels_allowed,
            context=context,
        )

    if response == WRONG_PROJECT_TYPE_ERROR:
        default_message = "Operation is not supported by the project type"
        if payload is None:
            message = default_message
        else:
            message = payload
        raise WrongProjectTypeError(message, context=context)

    payload_string = ""
    if payload:
        payload_string = f" with the following payload `{payload}`"
    raise GenericServerError(
        f"The Encord server has reported an error of type `{response}`{payload_string}. Please do not parse this error "
        "programmatically, instead please upgrade the SDK to the latest version to get the exact error.",
        context=context,
    )
