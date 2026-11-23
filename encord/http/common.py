from dataclasses import dataclass
from typing import Mapping, Optional

from encord.exceptions import ExceptionContext

HEADER_USER_AGENT = "User-Agent"
HEADER_CLOUD_TRACE_CONTEXT = "X-Cloud-Trace-Context"
# Carries the agent run token Encord sent an agent, back to Encord on the agent's own calls. Not Authorization:
# requests already use that for the SSH signature or the bearer token that identifies the caller.
HEADER_AGENT_RUN_TOKEN = "X-Encord-Agent-Run-Token"


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
