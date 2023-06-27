from encord.exceptions import *

HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_GENERAL_ERROR = 500


def handle_error_response(status_code: int, message=None, context=None):
    """
    Checks server response.
    Called if HTTP response status code is an error response.
    """
    if status_code == HTTP_UNAUTHORIZED:
        raise AuthenticationError("You are not authenticated to access the Encord platform.", context=context)

    if status_code == HTTP_FORBIDDEN:
        raise AuthorisationError("You are not authorised to access this asset.", context=context)

    if status_code == HTTP_NOT_FOUND:
        raise ResourceNotFoundError("The requested resource was not found.", context=context)

    if status_code == HTTP_METHOD_NOT_ALLOWED:
        raise MethodNotAllowedError("HTTP method is not allowed.", context=context)

    raise UnknownException("An unknown error occurred.", context=context)
