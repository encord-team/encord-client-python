from dataclasses import dataclass

DEFAULT_CONNECTION_RETRIES = 3
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.5


@dataclass
class RequestsSettings:
    """
    The settings for all outgoing network requests. These apply for each individual request.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    """Number of allowed retries when a request is sent. It only affects idempotent retryable requests."""

    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    """With each retry, there will be a sleep of backoff_factor * (2 ** (retry_number - 1) )"""

    connection_retries: int = DEFAULT_CONNECTION_RETRIES
    """Number of allowed retries to establish TCP connection when a request is sent."""


DEFAULT_REQUESTS_SETTINGS = RequestsSettings()
