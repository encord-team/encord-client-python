from dataclasses import dataclass

DEFAULT_CONNECTION_RETRIES = 3
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.5

DEFAULT_READ_TIMEOUT = 180  # In seconds
DEFAULT_WRITE_TIMEOUT = 180  # In seconds
DEFAULT_CONNECT_TIMEOUT = 180  # In seconds


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

    connect_timeout: int = DEFAULT_CONNECT_TIMEOUT
    """Maximum number of seconds from connection establishment to the first byte of response received"""

    read_timeout: int = DEFAULT_READ_TIMEOUT
    """Maximum number of seconds to obtain full response"""

    write_timeout: int = DEFAULT_WRITE_TIMEOUT
    """Maximum number of seconds to send request payload"""


DEFAULT_REQUESTS_SETTINGS = RequestsSettings()
