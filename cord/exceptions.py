#
# Copyright (c) 2020 Cord Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

class CordException(Exception):
    """ Base class for all exceptions. """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class AuthenticationError(CordException):
    """ Exception thrown when API key fails authentication. """
    pass


class AuthorisationError(CordException):
    """ Exception thrown when access to a data asset or method is unauthorised. """
    pass


class ResourceNotFoundError(CordException):
    """ Exception thrown when a requested resource (e.g. label, data asset) is not found. """
    pass


class TimeOutError(CordException):
    """ Exception thrown when a request times out. """
    pass


class RequestException(CordException):
    """ Ambiguous exception while handling request. """
    pass


class UnknownException(CordException):
    """ Unknown error. """
    pass


class MethodNotAllowedError(CordException):
    """ Exception thrown when HTTP method is not allowed. """
    pass


class OperationNotAllowed(CordException):
    """ Exception thrown when a read/write operation is not allowed by the API key. """
    pass


class AnswerDictionaryError(CordException):
    """ Exception thrown when object or classification is missing in answer dictionaries. """
    pass


class CorruptedLabelError(CordException):
    """ Exception thrown when a label is corrupted (e.g. the frame labels have more frames than the video.) """
    pass


class FileTypeNotSupportedError(CordException):
    """ Exception thrown when a file type is not supported
    Supported file types are: image/jpeg, image/png, video/webm, video/mp4. """
    pass


class DetectionRangeInvalidError(CordException):
    """ Exception thrown when a detection range is invalid (e.g. negative or higher than num frames in video) """
    pass


class InvalidAlgorithmError(CordException):
    """ Exception thrown when invalid labeling algorithm name is sent. """
    pass