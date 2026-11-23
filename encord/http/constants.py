"""---
title: "Constants"
slug: "sdk-ref-constants"
hidden: false
metadata:
  title: "Constants"
  description: "Encord SDK Constants."
category: "64e481b57b6027003f20aaa0"
---
"""

from dataclasses import dataclass
from typing import Callable, Optional

DEFAULT_CONNECTION_RETRIES = 3
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.5

DEFAULT_READ_TIMEOUT = 180  # In seconds
DEFAULT_WRITE_TIMEOUT = 180  # In seconds
DEFAULT_CONNECT_TIMEOUT = 180  # In seconds


@dataclass
class RequestsSettings:
    """The settings for all outgoing network requests. These apply for each individual request."""

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

    trace_id_provider: Optional[Callable[[], str]] = None
    """Function that supplies trace id for every request issued by the library. Random if not provided."""

    agent_run_token_provider: Optional[Callable[[], Optional[str]]] = None
    """Function that supplies the agent run token for every request issued by the library, sent as the
    ``X-Encord-Agent-Run-Token`` header. An agent sets it to the token Encord sent with the run it is handling, so the
    changes it makes can be attributed to that run. Called for each request, so a client shared across runs sends the
    current run's token; no header is sent when it is not set or returns None or an empty string."""


DEFAULT_REQUESTS_SETTINGS = RequestsSettings()
