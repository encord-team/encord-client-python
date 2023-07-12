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
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ExceptionContext:
    timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def __str__(self):
        return " ".join(
            f"{object_field.name}={getattr(self, object_field.name)!r}"
            for object_field in fields(self)
            if getattr(self, object_field.name) is not None
        )


class EncordException(Exception):
    """Base class for all exceptions."""

    def __init__(self, message: str, context: Optional[ExceptionContext] = None):
        super().__init__(message)
        self.message = message
        self.context = context if context is not None else ExceptionContext()

    def __str__(self):
        return f"{self.message} {self.context}"


CordException = EncordException


class InitialisationError(EncordException):
    """Exception thrown when API key fails to initialise."""

    pass


class AuthenticationError(EncordException):
    """Exception thrown when API key fails authentication."""

    pass


class AuthorisationError(EncordException):
    """
    Exception thrown when access is unauthorised.
    (E.g. access to a data asset or method).
    """

    pass


class ResourceNotFoundError(EncordException):
    """
    Exception thrown when a requested resource is not found.
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
    """Invalid date format error"""

    pass


class MethodNotAllowedError(EncordException):
    """Exception thrown when HTTP method is not allowed."""

    pass


class OperationNotAllowed(EncordException):
    """
    Exception thrown when a read/write operation is not allowed.
    The API key blocks the operation.
    """

    pass


class AnswerDictionaryError(EncordException):
    """
    Exception thrown when answer dictionaries are incomplete.
    Occurs when an object or classification is missing.
    """

    pass


class CorruptedLabelError(EncordException):
    """
    Exception thrown when a label is corrupted.
    (E.g. the frame labels have more frames than the video).
    """

    pass


class FileTypeNotSupportedError(EncordException):
    """
    Exception thrown when a file type is not supported.
    Supported file types are: image/jpeg, image/png, video/webm, video/mp4.
    """

    pass


class FileSizeNotSupportedError(EncordException):
    """
    Exception thrown when the combined size of the input files is larger than the supported limit.
    """

    pass


class FeatureDoesNotExistError(EncordException):
    """
    If a feature uid does not exist in a given project ontology.
    """

    pass


class ModelWeightsInconsistentError(EncordException):
    """
    Exception thrown when an attempted model training iteration has a different
    type of weights than what is recorded (i.e. if type of model_hash (uid) is faster_rcnn,
    but is attempted trained with different model weights).
    """

    pass


class ModelFeaturesInconsistentError(EncordException):
    """
    If a feature type is different than what is supported by the model (e.g. if
    creating a classification model using a bounding box).
    """

    pass


class UploadOperationNotSupportedError(EncordException):
    """Exception thrown when trying to upload a video/image group to non-Encord storage dataset"""

    pass


class DetectionRangeInvalidError(EncordException):
    """
    Exception thrown when a detection range is invalid.
    (E.g. negative or higher than num frames in video).
    """

    pass


class InvalidAlgorithmError(EncordException):
    """Exception thrown when invalid labeling algorithm name is sent."""

    pass


class ResourceExistsError(EncordException):
    """
    Exception thrown when trying to re-create a resource.
    Avoids overriding existing work.
    """

    pass


class DuplicateSshKeyError(EncordException):
    """
    Exception thrown when using an SSH key that was added twice to the platform.
    """

    pass


class SshKeyNotFound(EncordException):
    """
    Exception thrown when using an SSH key that was not added to the platform.
    """


class InvalidArgumentsError(EncordException):
    """Exception thrown when the arguments are invalid."""

    pass


class GenericServerError(EncordException):
    """
    The server has reported an error which is not recognised by this SDK version. Try upgrading the SDK version to
    see the precise error that is reported.
    """

    pass


class CloudUploadError(EncordException):
    """
    The upload to the cloud was not successful
    """

    pass


class MultiLabelLimitError(EncordException):
    """
    Too many labels were requested
    """

    def __init__(self, message, maximum_labels_allowed: int, context: Optional[ExceptionContext] = None):
        super().__init__(message=message, context=context)
        self.maximum_labels_allowed = maximum_labels_allowed


class LabelRowError(EncordException):
    """An error thrown when the construction of a LabelRow class is invalid."""

    pass


class OntologyError(EncordException):
    """An error thrown when using the ontology class with an error."""

    pass


class WrongProjectTypeError(CordException):
    """
    An error thrown when project type does not match the operation
    E.g. when TMS2 specific operations are attempted on non-TMS2 project
    """
