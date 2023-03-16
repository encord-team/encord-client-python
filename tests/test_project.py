import os
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from requests import Session

from encord.configs import _ENCORD_SSH_KEY_FILE
from encord.constants.model import Device
from encord.constants.model_weights import faster_rcnn_R_101_C4_3x
from encord.exceptions import EncordException
from encord.project import Project
from encord.user_client import EncordUserClient
from encord.client import EncordClientProject

PRIVATE_KEY = (
    Ed25519PrivateKey.generate()
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
)
UID = "d958ddbb-fcd0-477a-adf9-de14431dbbd2"


@pytest.fixture
def ssh_key_file_path():
    return os.path.join(os.path.dirname(__file__), "resources/test_key")


def teardown_function():
    if _ENCORD_SSH_KEY_FILE in os.environ:
        del os.environ[_ENCORD_SSH_KEY_FILE]


@pytest.fixture
@patch.object(EncordClientProject, "get_project")
def project(project_client_mock, ssh_key_file_path):
    project_client_mock.get_project.return_value = MagicMock()

    os.environ[_ENCORD_SSH_KEY_FILE] = ssh_key_file_path
    user_client = EncordUserClient.create_with_ssh_private_key()
    assert isinstance(user_client, EncordUserClient)
    return user_client.get_project("test_project")



@pytest.mark.parametrize("weights", [None, "invalid-weight"])
def test_invalid_weights_raises(project: Project, weights):

    with pytest.raises(EncordException) as excinfo:
        project.model_train(
            uid=UID,
            label_rows=[],
            epochs=500,
            batch_size=24,
            weights=weights,
            device=Device.CUDA,
        )

    assert "encord.constants.model_weights" in excinfo.value.message


@pytest.mark.parametrize("device", [None, "gpu"])
def test_invalid_device_raises(project: Project, device):

    with pytest.raises(EncordException) as trainExcInfo:
        project.model_train(
            uid=UID,
            label_rows=[],
            epochs=500,
            batch_size=24,
            weights=faster_rcnn_R_101_C4_3x,
            device=device,
        )

    assert "encord.constants.model.Device" in trainExcInfo.value.message

    with pytest.raises(EncordException) as inferenceExcInfo:
        project.model_inference(
            uid=UID,
            base64_strings=[bytes("base64string", "utf-8")],
            device=device,
        )

    assert "encord.constants.model.Device" in inferenceExcInfo.value.message


@pytest.mark.parametrize("device", [Device.CPU, Device.CUDA, "cuda", "cpu"])
@patch.object(Session, "send")
def test_valid_device(mock_send, project: Project, device):

    response = "ok"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": 200, "response": response}

    mock_send.return_value = mock_response

    result_train = project.model_train(
        uid=UID,
        label_rows=[],
        epochs=500,
        batch_size=24,
        weights=faster_rcnn_R_101_C4_3x,
        device=device,
    )

    assert result_train == response

    result_inference = project.model_inference(
        uid=UID,
        base64_strings=[bytes("base64string", "utf-8")],
        device=device,
    )

    assert result_inference == response
