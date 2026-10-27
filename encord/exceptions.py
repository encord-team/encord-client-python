"""---
title: "Exceptions"
slug: "sdk-ref-exceptions"
hidden: false
metadata:
  title: "Exceptions"
  description: "Encord SDK Exceptions."
category: "64e481b57b6027003f20aaa0"
---
"""

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

if TYPE_CHECKING:
    from encord.orm.storage import ClientMetadataPatchResult
    from encord.storage import ClientMetadataPatchJobs


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
    """Exception thrown when API key fails to initialize."""

    pass


class AuthenticationError(EncordException):
    """Exception thrown when API key fails authentication."""

    pass


class AuthorisationError(EncordException):
    """Exception thrown when access is unauthorized.
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


class RateLimitExceededError(EncordException):
    """Exception raised when requests exceed the Encord API rate limit."""

    def __init__(
        self,
        *,
        message: str = "Rate limit exceeded.",
        context: Optional[ExceptionContext] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        if retry_after:
            message += f" Retry after {retry_after} second{'s' if retry_after > 1 else ''}."

        super().__init__(message, context)
        self.retry_after = retry_after


class PayloadTooLargeError(EncordException):
    """Exception raised when request payload exceeds the maximum allowed size."""

    def __init__(
        self,
        message: str,
        *,
        context: Optional[ExceptionContext] = None,
    ) -> None:
        super().__init__(message, context)


class UnknownException(EncordException):
    """Unknown error."""

    pass


class ServiceUnavailableError(EncordException):
    """Exception raised when the Encord platform cannot be reached or is temporarily unavailable.

    Raised for the gateway / availability statuses (HTTP 502, 503 and 504) that the infrastructure in
    front of the API answers with while the service is down, restarting or overloaded. These are
    transient: retrying later is the expected remedy.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        status_code: Optional[int] = None,
        context: Optional[ExceptionContext] = None,
    ) -> None:
        if not message:
            status = f" (HTTP {status_code})" if status_code else ""
            message = (
                f"The Encord platform is temporarily unavailable{status}. "
                "This is usually transient - please retry in a few minutes. "
                "If the problem persists, contact Encord support."
            )
        super().__init__(message, context)
        self.status_code = status_code


class InvalidDateFormatError(EncordException):
    """Invalid date format error"""

    pass


class MethodNotAllowedError(EncordException):
    """Exception thrown when HTTP method is not allowed."""

    pass


class OperationNotAllowed(EncordException):
    """Exception thrown when a read/write operation is not allowed.
    The API key blocks the operation.
    """

    pass


class AnswerDictionaryError(EncordException):
    """Exception thrown when answer dictionaries are incomplete.
    Occurs when an object or classification is missing.
    """

    pass


class CorruptedLabelError(EncordException):
    """Exception thrown when a label is corrupted.
    (E.g. the frame labels have more frames than the video).
    """

    pass


class FileTypeNotSupportedError(EncordException):
    """Exception thrown when a file type is not supported.
    Supported file types are: image/jpeg, image/png, video/webm, video/mp4.
    """

    pass


class FileSizeNotSupportedError(EncordException):
    """Exception thrown when the combined size of the input files is larger than the supported limit."""

    pass


class FeatureDoesNotExistError(EncordException):
    """If a feature uid does not exist in a given project ontology."""

    pass


class ModelWeightsInconsistentError(EncordException):
    """Exception thrown when an attempted model training iteration has a different
    type of weights than what is recorded (i.e. if type of model_hash (uid) is faster_rcnn,
    but is attempted trained with different model weights).
    """

    pass


class ModelFeaturesInconsistentError(EncordException):
    """If a feature type is different than what is supported by the model (e.g. if
    creating a classification model using a bounding box).
    """

    pass


class UploadOperationNotSupportedError(EncordException):
    """Exception thrown when trying to upload a video/image group to non-Encord storage dataset"""

    pass


class DetectionRangeInvalidError(EncordException):
    """Exception thrown when a detection range is invalid.
    (E.g. negative or higher than num frames in video).
    """

    pass


class InvalidAlgorithmError(EncordException):
    """Exception thrown when invalid labeling algorithm name is sent."""

    pass


class ResourceExistsError(EncordException):
    """Exception thrown when trying to re-create a resource.
    Avoids overriding existing work.
    """

    pass


class DuplicateSshKeyError(EncordException):
    """Exception thrown when using an SSH key that was added twice to the platform."""

    pass


class SshKeyNotFound(EncordException):
    """Exception thrown when using an SSH key that was not added to the platform."""


class InvalidArgumentsError(EncordException):
    """Exception thrown when the arguments are invalid."""

    pass


class GenericServerError(EncordException):
    """The server has reported an error which is not recognized by this SDK version. Try upgrading the SDK version to
    see the precise error that is reported.
    """

    pass


class CloudUploadError(EncordException):
    """The upload to the cloud was not successful"""

    pass


class MultiLabelLimitError(EncordException):
    """Too many labels were requested"""

    def __init__(self, message, maximum_labels_allowed: int, context: Optional[ExceptionContext] = None):
        super().__init__(message=message, context=context)
        self.maximum_labels_allowed = maximum_labels_allowed


class LabelRowError(EncordException):
    """An error thrown when the construction of a LabelRow class is invalid."""

    pass


class DatasetError(EncordException):
    """An error thrown when a Dataset is used in an invalid state."""

    pass


class OntologyError(EncordException):
    """An error thrown when using the ontology class with an error."""

    pass


class WrongProjectTypeError(CordException):
    """An error thrown when project type does not match the operation
    E.g. when Workflow-specific operations are attempted on a non-Workflow project
    """


class BundledMoveWorkflowTasksPayloadError(EncordException):
    """An error thrown when an invalid item is added to the bundle to move workflow tasks"""

    pass


class ClientMetadataPatchTimeoutError(TimeOutError):
    """The wait for client metadata patch jobs ended before all of them finished.

    The SDK stopped waiting; it did not cancel the jobs, which may still finish. ``pending_job_uuids`` are the jobs
    that had not finished; check them with :meth:`encord.user_client.EncordUserClient.get_client_metadata_patch_job`.
    ``failures`` are the patches that could not be confirmed as applied by the jobs that had finished. ``started`` are
    all the jobs waited for, with the items each one patches.
    """

    def __init__(
        self,
        message: str,
        pending_job_uuids: List[UUID],
        failures: List["ClientMetadataPatchResult"],
        started: "ClientMetadataPatchJobs",
    ) -> None:
        super().__init__(message)
        self.pending_job_uuids = pending_job_uuids
        self.failures = failures
        self.started = started


class ClientMetadataPatchWaitError(EncordException):
    """The wait for client metadata patch jobs stopped on an error before all of them were checked.

    The SDK stopped waiting; it did not cancel the jobs, which may still finish. ``pending_job_uuids`` are the jobs
    whose result was not received; check them with
    :meth:`encord.user_client.EncordUserClient.get_client_metadata_patch_job`. ``failures`` are the patches that could
    not be confirmed as applied by the jobs that had finished. ``started`` are all the jobs waited for, with the items
    each one patches. The error that stopped the wait is the cause (``__cause__``).
    """

    def __init__(
        self,
        message: str,
        pending_job_uuids: List[UUID],
        failures: List["ClientMetadataPatchResult"],
        started: "ClientMetadataPatchJobs",
    ) -> None:
        super().__init__(message)
        self.pending_job_uuids = pending_job_uuids
        self.failures = failures
        self.started = started


class ClientMetadataPatchPartiallyStartedError(EncordException):
    """Starting the client metadata patch jobs stopped part-way, so only some of the patches were sent.

    The jobs in ``started`` are running and were not cancelled; check them with
    :meth:`encord.user_client.EncordUserClient.get_client_metadata_patch_job`. The patches of the items in
    ``not_started_item_uuids`` were not sent, and can be sent again. The error that stopped the start is the cause
    (``__cause__``).
    """

    def __init__(self, message: str, started: "ClientMetadataPatchJobs", not_started_item_uuids: List[UUID]) -> None:
        super().__init__(message)
        self.started = started
        self.not_started_item_uuids = not_started_item_uuids
