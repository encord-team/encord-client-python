import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from requests import Session

from encord.configs import SshConfig
from encord.http.constants import RequestsSettings
from encord.http.v2.api_client import ApiClient
from encord.user_client import EncordUserClient
from tests.fixtures import PRIVATE_KEY, PRIVATE_KEY_PEM

PROJECT_HASH = uuid4().hex
ONTOLOGY_HASH = uuid4().hex
DATASET_HASH = uuid4().hex


@pytest.fixture
def api_client():
    return ApiClient(config=SshConfig(PRIVATE_KEY))


def stub_responses(*args, **kwargs) -> MagicMock:
    mock_response = MagicMock()

    if args[0].path_url.startswith("/v2/public/projects"):
        response = {
            "project_hash": PROJECT_HASH,
            "project_type": "manual_qa",
            "title": "Test project",
            "description": "",
            "created_at": "2024-01-01 11:11:11",
            "last_edited_at": "2024-01-01 11:11:11",
            "editor_ontology": {},
            "datasets": [uuid4().hex],
            "label_rows": [],
            "ontology_hash": ONTOLOGY_HASH,
        }
        mock_response.status_code = 200
        mock_response.json.return_value = response
    elif args[0].path_url.startswith("/v2/public/ontologies"):
        response = {
            "ontologyUuid": ONTOLOGY_HASH,
            "title": "Test ontology",
            "description": "",
            "created_at": "2024-01-01 11:11:11",
            "last_edited_at": "2024-01-01 11:11:11",
            "editor": {"objects": [], "classifications": []},
            "user_role": 1,
        }
        mock_response.status_code = 200
        mock_response.json.return_value = response
    else:
        # Legacy api
        body_json = json.loads(args[0].body)
        request_type = body_json["query_type"]
        if request_type == "ontology":
            response = {
                "title": "Test ontology",
                "description": "",
                "ontology_hash": ONTOLOGY_HASH,
                "created_at": "2024-01-01 11:11:11",
                "last_edited_at": "2024-01-01 11:11:11",
                "editor": {
                    "objects": [],
                    "classifications": [],
                },
            }
        elif request_type == "dataset":
            response = {
                "dataset_hash": DATASET_HASH,
                "title": "Test dataset",
                "description": "",
                "dataset_type": "cord",
                "data_rows": [],
            }
        elif request_type in ["datarows", "labelrowmetadata"]:
            response = {}  # These objects are not used in tests, so it's ok to return empty descriptor for now
        else:
            assert False, f"Unsupported request: {request_type}"

        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 200, "response": response}
        mock_response.content = json.dumps({"status": 200, "response": response})

    return mock_response


def verify_timeout_and_reset(mock: MagicMock, requests_settings: RequestsSettings, expected_call_count=1) -> None:
    assert mock.call_count == expected_call_count
    assert all(
        call[1]["timeout"] == (requests_settings.connect_timeout, requests_settings.read_timeout)
        for call in mock.call_args_list
    )

    mock.reset_mock()


@patch.object(Session, "send")
def test_request_timeout_settings_correctly_propagated(send: MagicMock, api_client: ApiClient):
    requests_settings = RequestsSettings(
        connect_timeout=1001,
        read_timeout=1002,
        write_timeout=1003,
    )

    send.side_effect = stub_responses

    user_client = EncordUserClient.create_with_ssh_private_key(
        ssh_private_key=PRIVATE_KEY_PEM, requests_settings=requests_settings
    )
    project = user_client.get_project(PROJECT_HASH)
    verify_timeout_and_reset(send, requests_settings, 2)

    project.list_label_rows_v2()
    verify_timeout_and_reset(send, requests_settings)

    dataset = user_client.get_dataset(DATASET_HASH)
    verify_timeout_and_reset(send, requests_settings)

    dataset.list_data_rows()
    verify_timeout_and_reset(send, requests_settings)

    ontology = user_client.get_ontology(ONTOLOGY_HASH)
    verify_timeout_and_reset(send, requests_settings)

    ontology.refetch_data()
    verify_timeout_and_reset(send, requests_settings)

    # Re-mocking for V2 API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_response.content = json.dumps({"results": []})
    send.side_effect = None
    send.return_value = mock_response

    _ = list(project.list_collaborator_timers(datetime.now()))
    verify_timeout_and_reset(send, requests_settings)
