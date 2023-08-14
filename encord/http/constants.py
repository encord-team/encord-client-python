from dataclasses import dataclass

DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_CONNECTION_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1


@dataclass
class RequestsSettings:
    """
    The settings for all outgoing network requests. These apply for each individual request.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    """Maximum number of retries when a request is sent. Only GET requests are automatically retried."""

    max_connection_retries: int = DEFAULT_MAX_CONNECTION_RETRIES
    """Maximum number of retries when establishing a connection."""

    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    """With each retry, there will be a sleep of backoff_factor * (2 ** (retry_number - 1) )"""


DEFAULT_REQUESTS_SETTINGS = RequestsSettings()
