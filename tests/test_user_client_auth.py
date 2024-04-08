import json
import uuid
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_ssh_private_key,
)
from requests import PreparedRequest, Session

from encord.client import EncordClient
from encord.configs import _get_signature, _get_ssh_authorization_header
from encord.http.v2.payloads import Page
from encord.orm.analytics import CollaboratorTimer
from encord.orm.ontology import Ontology as OrmOntology
from encord.orm.ontology import OntologyStructure
from encord.orm.project import Project as OrmProject
from encord.user_client import EncordUserClient
from tests.fixtures import DUMMY_PRIVATE_KEY

PROJECT_HASH = str(uuid.uuid4())
ONTOLOGY_HASH = str(uuid.uuid4())


ontology_orm = OrmOntology(
    ontology_hash=ONTOLOGY_HASH,
    title="Test ontology",
    structure=OntologyStructure(),
    created_at=datetime.now(),
    last_edited_at=datetime.now(),
)

ontology_dic = {
    "ontology_hash": ONTOLOGY_HASH,
    "title": "Test ontology",
    "created_at": datetime.now(),
    "last_edited_at": datetime.now(),
    "editor": OntologyStructure().to_dict(),
    "description": "",
}

api_key_meta_dic = {"title": "dummy key", "resource_type": "project"}

project_orm = OrmProject({"project_hash": PROJECT_HASH, "ontology_hash": ONTOLOGY_HASH})


@pytest.fixture
def bearer_token() -> str:
    return "a-fake-token"


def make_side_effects(project_response: Optional[MagicMock] = None, ontology_response: Optional[MagicMock] = None):
    # Mocking a few service endpoints to make it possible to test authentication

    def side_effects(*args, **kwargs):
        if args[0].path_url.startswith("/public/user"):
            request_type = json.loads(args[0].body)["query_type"]
            if request_type == "datasetwithuserrole":
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 200, "response": {}}
                mock_response.content = json.dumps({"status": 200, "response": {}})
                return mock_response
            else:
                assert False
        elif args[0].path_url.startswith("/public"):
            request_type = json.loads(args[0].body)["query_type"]

            if request_type == "project":
                if project_response:
                    return project_response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 200, "response": project_orm}
                mock_response.content = json.dumps({"status": 200, "response": project_orm}, default=str)
                return mock_response
            elif request_type == "ontology":
                if ontology_response:
                    return ontology_response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 200, "response": ontology_dic}
                mock_response.content = json.dumps({"status": 200, "response": ontology_dic}, default=str)
                return mock_response
            elif request_type == "apikeymeta":
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 200, "response": api_key_meta_dic}
                mock_response.content = json.dumps({"status": 200, "response": api_key_meta_dic})
                return mock_response
            else:
                print(f"Unknown type {request_type}")
                assert False

        elif args[0].path_url.startswith("/v2/public/analytics/collaborators/timers"):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = Page[CollaboratorTimer](results=[]).to_dict()
            mock_response.json.content = json.dumps(Page[CollaboratorTimer](results=[]).to_dict())
            return mock_response
        else:
            raise RuntimeError(f"Not mocked URL: {args[0].path_url}")

    return side_effects


def get_encord_auth_header(request: PreparedRequest) -> str:
    private_key = load_ssh_private_key(DUMMY_PRIVATE_KEY.encode(), None)
    public_key = private_key.public_key()
    signature = _get_signature(request.body, private_key)
    return _get_ssh_authorization_header(public_key.public_bytes(Encoding.Raw, PublicFormat.Raw).hex(), signature)


@patch.object(Session, "send")
def test_v1_public_resource_when_initialised_with_ssh_key(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key=DUMMY_PRIVATE_KEY)
    user_client.get_project(project_hash=PROJECT_HASH)

    assert mock_send.call_count == 2
    for mock_call in mock_send.call_args_list:
        # Expect call to have correct resource type and id, and correct bearer auth
        request = mock_call.args[0]

        assert request.path_url == "/public"
        assert request.headers["ResourceType"] == "project"
        assert request.headers["ResourceID"] == PROJECT_HASH
        assert request.headers["Authorization"] == get_encord_auth_header(request)


@patch.object(Session, "send")
def test_v1_public_resource_when_initialised_with_bearer_auth(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    user_client = EncordUserClient.create_with_bearer_token(bearer_token)
    user_client.get_project(project_hash=PROJECT_HASH)

    assert mock_send.call_count == 2
    for mock_call in mock_send.call_args_list:
        # Expect call to have correct resource type and id, and correct bearer auth
        assert mock_call.args[0].path_url == "/public"
        assert mock_call.args[0].headers["ResourceType"] == "project"
        assert mock_call.args[0].headers["ResourceID"] == PROJECT_HASH
        assert mock_call.args[0].headers["Authorization"] == f"Bearer {bearer_token}"


@patch.object(Session, "send")
def test_v1_public_user_resource_when_initialised_with_ssh_key(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key=DUMMY_PRIVATE_KEY)
    user_client.get_datasets()

    assert mock_send.call_count == 1
    for mock_call in mock_send.call_args_list:
        # Expect call to have correct resource type and id, and correct bearer auth
        request = mock_call.args[0]

        assert request.path_url == "/public/user"
        assert request.headers["Authorization"] == get_encord_auth_header(request)


@patch.object(Session, "send")
def test_v1_public_user_resource_when_initialised_with_bearer_auth(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    user_client = EncordUserClient.create_with_bearer_token(bearer_token)
    user_client.get_datasets()

    assert mock_send.call_count == 1
    for mock_call in mock_send.call_args_list:
        # Expect call to have correct resource type and id, and correct bearer auth
        request = mock_call.args[0]
        assert request.path_url == "/public/user"
        assert request.headers["Authorization"] == f"Bearer {bearer_token}"


@patch.object(Session, "send")
def test_v2_api_when_initialised_with_ssh_key(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key=DUMMY_PRIVATE_KEY)
    project = user_client.get_project(project_hash=PROJECT_HASH)

    mock_send.reset_mock()
    # Collaborator timers are implemented in API v2, so using it to test auth
    list(project.list_collaborator_timers(datetime.now()))

    assert mock_send.call_count == 1
    for mock_call in mock_send.call_args_list:
        # A bit tricky to validate signature, since sdk doesn't have implementation of the checker,
        # so just checking that correct headers are added.
        # Signature itself is checked as part of e2e tests.
        assert mock_call.args[0].path_url.startswith("/v2/public/analytics/collaborators/timers")
        assert (
            mock_call.args[0]
            .headers["Signature-Input"]
            .startswith('encord-sig=("@method" "@request-target" "content-digest")')
        )
        assert mock_call.args[0].headers["Signature"].startswith("encord-sig=")


@patch.object(Session, "send")
def test_v2_api_when_initialised_with_bearer_auth(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    user_client = EncordUserClient.create_with_bearer_token(bearer_token)
    project = user_client.get_project(project_hash=PROJECT_HASH)

    mock_send.reset_mock()
    # Collaborator timers are implemented in API v2, so using it to test auth
    list(project.list_collaborator_timers(datetime.now()))

    assert mock_send.call_count == 1
    for mock_call in mock_send.call_args_list:
        # Expect call to have correct resource type and id, and correct bearer auth
        assert mock_call.args[0].path_url.startswith("/v2/public/analytics/collaborators/timers")
        assert mock_call.args[0].headers["Authorization"] == f"Bearer {bearer_token}"


@patch.object(Session, "send")
def test_v1_public_when_initialised_with_api_key(mock_send, bearer_token):
    mock_send.side_effect = make_side_effects()

    client = EncordClient.initialise(resource_id="project-hash", api_key="dummy api key")
    client.get_project()

    assert mock_send.call_count == 2
    for mock_call in mock_send.call_args_list:
        # Expect call to have correct resource type and id, and correct bearer auth
        assert mock_call.args[0].path_url.startswith("/public")
        assert mock_call.args[0].headers["Authorization"] == "dummy api key"
