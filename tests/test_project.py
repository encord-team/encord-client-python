import os
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from requests import Session

from encord.client import EncordClientProject
from encord.configs import _ENCORD_SSH_KEY_FILE
from encord.constants.model import Device
from encord.constants.model_weights import faster_rcnn_R_101_C4_3x
from encord.exceptions import EncordException
from encord.orm.label_row import LabelRow
from encord.orm.project import Project as OrmProject
from encord.project import Project
from encord.user_client import EncordUserClient

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
def project(project_client_mock: MagicMock, ssh_key_file_path):
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


@patch.object(EncordClientProject, "get_project")
def test_label_rows_property_queries_metadata(project_client_mock: MagicMock, project: Project):
    project_current_orm_mock = MagicMock(spec=OrmProject)
    type(project_current_orm_mock).label_rows = PropertyMock(return_value=None)
    project._project_instance = project_current_orm_mock

    project_orm_mock = MagicMock(spec=OrmProject)
    project_client_mock.return_value = project_orm_mock
    type(project_orm_mock).label_rows = PropertyMock(return_value=[LabelRow({"data_title": "abc"})])

    project_client_mock.assert_not_called()

    rows = project.label_rows

    # Expect project data query to happen during the property call
    project_client_mock.assert_called_once()

    assert project_client_mock.call_args[1] == {"include_labels_metadata": True}

    assert len(rows) == 1
    assert rows[0].data_title == "abc"

    # Expect label rows metadata to be cached, so data query doesn't happen again
    _ = project.label_rows
    project_client_mock.assert_called_once()
