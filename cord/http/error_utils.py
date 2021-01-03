from cord.exceptions import *

# Error messages
AUTHENTICATION_ERROR = ['AUTHENTICATION_ERROR']
AUTHORISATION_ERROR = ['AUTHORISATION_ERROR']
METHOD_NOT_ALLOWED_ERROR = ['METHOD_NOW_ALLOWED_ERROR']
UNKNOWN_ERROR = ['UNKNOWN_ERROR']
OPERATION_NOT_ALLOWED_ERROR = ['OPERATION_NOT_ALLOWED']
ANSWER_DICTIONARY_ERROR = ['ANSWER_DICTIONARY_ERROR']
CORRUPTED_LABEL_ERROR = ['CORRUPTED_LABEL_ERROR']


def check_error_response(response):
    """
    Checks server response, called if HTTP response status code is an error response
    """
    if response == AUTHENTICATION_ERROR:
        raise AuthenticationError("Invalid API key.")

    if response == AUTHORISATION_ERROR:
        raise AuthorisationError("You are not authorised to access this asset.")

    if response == METHOD_NOT_ALLOWED_ERROR:
        raise MethodNotAllowedError("HTTP method is not allowed.")

    if response == UNKNOWN_ERROR:
        raise UnknownException("An unknown error occurred.")

    if response == OPERATION_NOT_ALLOWED_ERROR:
        raise OperationNotAllowed("The read/write operation is not allowed by the API key.")

    if response == ANSWER_DICTIONARY_ERROR:
        raise AnswerDictionaryError("An object or classification is missing in the answer dictionaries.")

    if response == CORRUPTED_LABEL_ERROR:
        raise CorruptedLabelError("The label blurb is corrupted. This could be due to the number of "
                                  "frame labels exceeding the number of frames in the labelled video.")

    pass
