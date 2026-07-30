from __future__ import annotations

from typing import Mapping

from encord.exceptions import (
    AuthenticationError,
    AuthorisationError,
    InvalidArgumentsError,
    MethodNotAllowedError,
    PayloadTooLargeError,
    RateLimitExceededError,
    ResourceExistsError,
    ResourceNotFoundError,
    UnknownException,
)
from encord.http.common import RequestContext

HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_CONFLICT = 409
HTTP_PAYLOAD_TOO_LARGE = 413
HTTP_TOO_MANY_REQUESTS = 429
HTTP_GENERAL_ERROR = 500


def handle_error_response(
    status_code: int,
    response_headers: Mapping[str, str],
    message: str | None = None,
    context: RequestContext | None = None,
):
    """Checks server response.
    Called if HTTP response status code is an error response.
    """
    if status_code == HTTP_UNAUTHORIZED:
        hint = (
            "You might also be seeing this because you're connecting to the wrong region. "
            "Try changing the `domain` parameter (e.g. 'https://api.us.encord.com' vs 'https://api.encord.com')."
        )
        if context and context.domain:
            hint = f"{hint} Currently connected to: {context.domain}"
        msg = f"{message or 'You are not authenticated to access the Encord platform.'} {hint}"
        raise AuthenticationError(msg, context=context)

    if status_code == HTTP_FORBIDDEN:
        raise AuthorisationError(message or "You are not authorised to access this asset.", context=context)

    if status_code == HTTP_NOT_FOUND:
        raise ResourceNotFoundError("The requested resource was not found.", context=context)

    if status_code == HTTP_METHOD_NOT_ALLOWED:
        raise MethodNotAllowedError("HTTP method is not allowed.", context=context)

    if status_code == HTTP_CONFLICT:
        raise ResourceExistsError(message or "The resource you are trying to create already exists.", context=context)

    if status_code == HTTP_BAD_REQUEST:
        raise InvalidArgumentsError(message or "Provided payload is invalid and can't be processed.", context=context)

    if status_code == HTTP_PAYLOAD_TOO_LARGE:
        raise PayloadTooLargeError(
            message or "Request payload is too large and exceeds the maximum allowed size.", context=context
        )

    if status_code == HTTP_TOO_MANY_REQUESTS:
        retry_after_header = response_headers.get("Retry-After", "")
        retry_after = int(retry_after_header) if retry_after_header.isdigit() else None
        raise RateLimitExceededError(retry_after=retry_after, context=context)

    raise UnknownException(message or "An unknown error occurred.", context=context)
