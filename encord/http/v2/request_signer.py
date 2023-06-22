import base64
import hashlib
from datetime import datetime
from typing import Dict, Union

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from requests import PreparedRequest

_SIGNATURE_LABEL = "encord-sig"

"""
This file implements request signing according to the following RFC draft:
https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-message-signatures
"""


def _sfv_str(key: str, value: Union[str, bytes]) -> str:
    if isinstance(value, bytes):
        return f"{key}=:{base64.b64encode(value).decode('ascii')}:"
    return f"{key}={value}"


def _sfv_value(value: Union[int, str]) -> str:
    if isinstance(value, int):
        return str(value)
    return f'"{value}"'


def _request_body_bytes(request: PreparedRequest) -> bytes:
    if isinstance(request.body, str):
        return request.body.encode("utf-8")
    elif isinstance(request.body, bytes):
        return request.body
    else:
        return b""


def sign_request(request: PreparedRequest, key_id: str, private_key: Ed25519PrivateKey):
    assert request.method is not None

    content_digest = _sfv_str("sha-256", hashlib.sha256(_request_body_bytes(request)).digest())
    signature_params: Dict[str, Union[str, int]] = {
        "created": int(datetime.now().timestamp()),
        "keyid": key_id,
        "alg": "ed25519",
    }

    signature_elements = {
        "@method": request.method.upper(),
        "@request-target": request.path_url,
        "content-digest": content_digest,
    }

    covered_elements = [f'"{element_id}"' for element_id in signature_elements.keys()]
    signature_elements_pairs = [f"{k}={_sfv_value(v)}" for k, v in signature_params.items()]
    sig_params_serialised = ";".join([f"({' '.join(covered_elements)})"] + signature_elements_pairs)

    signature_elements["@signature-params"] = sig_params_serialised

    signature_base = "\n".join(f'"{k}": {v}' for k, v in signature_elements.items())
    signature = private_key.sign(signature_base.encode())

    request.headers["Content-Digest"] = content_digest
    request.headers["Signature-Input"] = _sfv_str(_SIGNATURE_LABEL, sig_params_serialised)
    request.headers["Signature"] = _sfv_str(_SIGNATURE_LABEL, signature)

    return request
