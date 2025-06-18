from __future__ import annotations

import json
from uuid import UUID

from jwcrypto.common import base64url_decode
from pydantic import BaseModel

from encord.exceptions import TokenVerificationError
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO
import jwt

class Token(BaseModel):
    aud: str
    iat: float
    iss: str
    sub: str


class ServiceIntegration:
    """
    A web service that Encord integrates with.
    """

    def __init__(self, api_client: ApiClient, uuid: UUID) -> None:
        self._api_client = api_client
        self._uuid = uuid
        self._jwks = None

    @property
    def uuid(self) -> UUID:
        return self._uuid




class _JSONWebKeySet(BaseDTO):
    keys: list[_JSONWebKey]


class _JSONWebKey(BaseDTO):
    kid: str
    kty: str
    crv: str
    alg: str
    use: str
    x: str
