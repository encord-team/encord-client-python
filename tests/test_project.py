import uuid
from unittest.mock import MagicMock, PropertyMock, patch

from encord.client import EncordClientProject
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.label_row import LabelRow
from encord.orm.project import Project as OrmProject
from encord.orm.project import ProjectDataset
from encord.project import Project
from tests.fixtures import ontology, project, user_client

assert user_client and project and ontology


UID = "d958ddbb-fcd0-477a-adf9-de14431dbbd2"


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


@patch.object(ApiClient, "get")
def test_project_datasets(api_get: MagicMock, project: Project) -> None:
    dataset_hash = uuid.uuid4()
    expected_dataset = ProjectDataset(dataset_hash=dataset_hash, title="test dataset", description="my test dataset")
    api_get.return_value = Page(results=[expected_dataset])

    assert len(list(project.list_datasets())) == 1
    assert list(project.list_datasets()) == [expected_dataset]

    # Correctly serialised for legacy endpoint
    assert len(project.datasets) == 1
    assert project.datasets[0] == {
        "dataset_hash": str(dataset_hash),
        "title": "test dataset",
        "description": "my test dataset",
    }
