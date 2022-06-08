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


class EncordException(Exception):
    """Base class for all exceptions."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


CordException = EncordException


class BadRequestErrors(EncordException):
    """Exception thrown when a request to the Encord server has lead to an error."""


class InitialisationError(EncordException):
    """Exception thrown when API key fails to initialise."""

    pass


class AuthenticationError(EncordException):
    """Exception thrown when API key fails authentication."""

    pass


class AuthorisationError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when access is unauthorised.
    (E.g. access to a data asset or method).
    """

    pass


class ResourceNotFoundError(EncordException):
    """Exception thrown when a requested resource is not found.
    (E.g. label, data asset).
    """

    pass


class TimeOutError(EncordException):
    """Exception thrown when a request times out."""

    pass


class RequestException(EncordException):
    """Ambiguous exception while handling request."""

    pass


class UnknownException(EncordException):
    """Unknown error."""

    pass


class InvalidDateFormatError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Invalid date format error
    """

    pass


class MethodNotAllowedError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead
    Exception thrown when HTTP method is not allowed.
    """

    pass


class OperationNotAllowed(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when a read/write operation is not allowed.
    The API key blocks the operation.
    """

    pass


class AnswerDictionaryError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when answer dictionaries are incomplete.
    Occurs when an object or classification is missing.
    """

    pass


class CorruptedLabelError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when a label is corrupted.
    (E.g. the frame labels have more frames than the video).
    """

    pass


class FileTypeNotSupportedError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when a file type is not supported.
    Supported file types are: image/jpeg, image/png, video/webm, video/mp4.
    """

    pass


class FileSizeNotSupportedError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when the combined size of the input files is larger than the supported limit.
    """

    pass


class FeatureDoesNotExistError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    If a feature uid does not exist in a given project ontology.
    """

    pass


class ModelWeightsInconsistentError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when an attempted model training iteration has a different
    type of weights than what is recorded (i.e. if type of model_hash (uid) is faster_rcnn,
    but is attempted trained with yolov5 weights).
    """

    pass


class ModelFeaturesInconsistentError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    If a feature type is different than what is supported by the model (e.g. if
    creating a classification model using a bounding box).
    """

    pass


class UploadOperationNotSupportedError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when trying to upload a video/image group to non-Encord storage dataset"""

    pass


class DetectionRangeInvalidError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when a detection range is invalid.
    (E.g. negative or higher than num frames in video).
    """

    pass


class InvalidAlgorithmError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead
    Exception thrown when invalid labeling algorithm name is sent.
    """

    pass


class ResourceExistsError(EncordException):
    """
    DEPRECATED - a ServerError will be thrown instead

    Exception thrown when trying to re-create a resource.
    Avoids overriding existing work.
    """

    pass
