from dataclasses import dataclass
from typing import Optional

from encord.exceptions import ExceptionContext

HEADER_USER_AGENT = "User-Agent"
HEADER_CLOUD_TRACE_CONTEXT = "X-Cloud-Trace-Context"


@dataclass
class RequestContext(ExceptionContext):
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
