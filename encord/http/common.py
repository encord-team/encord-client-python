from dataclasses import dataclass
from typing import Mapping, Optional

from encord.exceptions import ExceptionContext

HEADER_USER_AGENT = "User-Agent"
HEADER_CLOUD_TRACE_CONTEXT = "X-Cloud-Trace-Context"


@dataclass
class RequestContext(ExceptionContext):
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    domain: Optional[str] = None


def parse_retry_after(response_headers: Mapping[str, str]) -> Optional[int]:
    """Read the `Retry-After` hint, in whole seconds, from response headers.

    Both API clients surface this on `RateLimitExceededError` so callers can back off for as long
    as the server asked. Only the delay-in-seconds form is understood; the HTTP-date form (and
    anything else unparseable) is reported as no hint at all.
    """
    retry_after = response_headers.get("Retry-After", "")
    return int(retry_after) if retry_after.isdigit() else None
