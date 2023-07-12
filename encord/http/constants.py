from dataclasses import dataclass

DEFAULT_MAX_RETRIES = 0
DEFAULT_BACKOFF_FACTOR = 0.1


@dataclass
class RequestsSettings:
    """
    The settings for all outgoing network requests. These apply for each individual request.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    """Number of allowed retries when a request is sent."""

    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    """With each retry, there will be a sleep of backoff_factor * (2 ** (retry_number - 1) )"""


DEFAULT_REQUESTS_SETTINGS = RequestsSettings()
