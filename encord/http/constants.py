from dataclasses import dataclass

from requests.adapters import DEFAULT_POOLSIZE

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
    """With each retry, there will be a sleep of backoff_factor * (2 ** retry_number)"""

    pool_maxsize: int = DEFAULT_POOLSIZE
    """The maximum number of connections to save in the pool."""


DEFAULT_REQUESTS_SETTINGS = RequestsSettings()
