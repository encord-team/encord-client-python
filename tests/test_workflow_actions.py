import json
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from encord import Project
from encord.client import EncordClientProject
from encord.http.querier import Querier, RequestContext
from encord.orm.label_row import LabelRowMetadata
from tests.fixtures import ontology, project, user_client
from tests.test_data.label_rows_metadata_blurb import LABEL_ROW_METADATA_BLURB

assert user_client and project and ontology

DUMMY_PRIVATE_KEY = (
    Ed25519PrivateKey.generate()
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
)


@patch.object(Querier, "_execute")
@patch.object(EncordClientProject, "list_label_rows")
def test_workflow_reopen(list_label_rows_mock: MagicMock, querier_request_mock: MagicMock, project: Project):
    label_rows_metadata = [LabelRowMetadata.from_dict(row) for row in LABEL_ROW_METADATA_BLURB]
    list_label_rows_mock.return_value = label_rows_metadata
    querier_request_mock.return_value = (True, RequestContext())

    test_label_row = project.list_label_rows_v2()[0]

    test_label_row.workflow_reopen()

    querier_request_mock.assert_called_once()

    request = querier_request_mock.call_args[0][0]
    request_data = json.loads(request.data)

    assert request_data["query_type"] == "labelworkflowgraphnode"
    assert request_data["values"]["payload"]["action"] == "reopen"
    assert request_data["values"]["uid"] == [test_label_row.label_hash]


@patch.object(Querier, "_execute")
@patch.object(EncordClientProject, "list_label_rows")
def test_workflow_reopen_bundle(list_label_rows_mock: MagicMock, querier_request_mock: MagicMock, project: Project):
    label_rows_metadata = [LabelRowMetadata.from_dict(row) for row in LABEL_ROW_METADATA_BLURB]
    list_label_rows_mock.return_value = label_rows_metadata
    querier_request_mock.return_value = (True, RequestContext())

    with project.create_bundle() as bundle:
        for lr in project.list_label_rows_v2():
            lr.workflow_reopen(bundle=bundle)

    querier_request_mock.assert_called_once()

    request = querier_request_mock.call_args[0][0]
    request_data = json.loads(request.data)

    assert request_data["query_type"] == "labelworkflowgraphnode"
    assert request_data["values"]["payload"]["action"] == "reopen"
    assert request_data["values"]["uid"] == [lr.label_hash for lr in label_rows_metadata]


@patch.object(Querier, "_execute")
@patch.object(EncordClientProject, "list_label_rows")
def test_workflow_complete(list_label_rows_mock: MagicMock, querier_request_mock: MagicMock, project: Project):
    label_rows_metadata = [LabelRowMetadata.from_dict(row) for row in LABEL_ROW_METADATA_BLURB]
    list_label_rows_mock.return_value = label_rows_metadata
    querier_request_mock.return_value = (True, RequestContext())

    test_label_row = project.list_label_rows_v2()[0]

    test_label_row.workflow_complete()

    querier_request_mock.assert_called_once()

    request = querier_request_mock.call_args[0][0]
    request_data = json.loads(request.data)

    assert request_data["query_type"] == "labelworkflowgraphnode"
    assert request_data["values"]["payload"]["action"] == "complete"
    assert request_data["values"]["uid"] == [test_label_row.label_hash]


@patch.object(Querier, "_execute")
@patch.object(EncordClientProject, "list_label_rows")
def test_workflow_complete_bundle(list_label_rows_mock: MagicMock, querier_request_mock: MagicMock, project: Project):
    label_rows_metadata = [LabelRowMetadata.from_dict(row) for row in LABEL_ROW_METADATA_BLURB]
    list_label_rows_mock.return_value = label_rows_metadata
    querier_request_mock.return_value = (True, RequestContext())

    with project.create_bundle() as bundle:
        for lr in project.list_label_rows_v2():
            lr.workflow_complete(bundle=bundle)

    querier_request_mock.assert_called_once()

    request = querier_request_mock.call_args[0][0]
    request_data = json.loads(request.data)

    assert request_data["query_type"] == "labelworkflowgraphnode"
    assert request_data["values"]["payload"]["action"] == "complete"
    assert request_data["values"]["uid"] == [lr.label_hash for lr in label_rows_metadata]
