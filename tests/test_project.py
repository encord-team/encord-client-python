import uuid
from typing import Tuple
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from encord.client import EncordClientProject
from encord.exceptions import ResourceNotFoundError
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.label_row import LabelRow
from encord.orm.project import OrganisationTag, ProjectDataset
from encord.orm.project import Project as OrmProject
from encord.project import Project

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


@pytest.mark.parametrize(
    "tag_names",
    [
        pytest.param([], id="none"),
        pytest.param(["my-tag"], id="one"),
        pytest.param(["alpha", "beta", "gamma"], id="many"),
    ],
)
@patch.object(ApiClient, "get")
def test_get_organisation_tags(api_get: MagicMock, project: Project, tag_names: list[str]) -> None:
    tags = [OrganisationTag(uuid=uuid.uuid4(), name=name) for name in tag_names]
    api_get.return_value = Page(results=tags)

    result = project.get_organisation_tags()

    assert result == tags
    api_get.assert_called_once()


@patch.object(ApiClient, "get")
def test_get_organisation_tags_cached(api_get: MagicMock, project: Project) -> None:
    api_get.return_value = Page(results=[OrganisationTag(uuid=uuid.uuid4(), name="my-tag")])

    project.get_organisation_tags()
    project.get_organisation_tags()

    api_get.assert_called_once()


@patch.object(ApiClient, "get")
def test_get_organisation_tags_use_cache_false(api_get: MagicMock, project: Project) -> None:
    api_get.return_value = Page(results=[OrganisationTag(uuid=uuid.uuid4(), name="my-tag")])

    project.get_organisation_tags()
    project.get_organisation_tags(use_cache=False)

    assert api_get.call_count == 2


@patch.object(ApiClient, "get")
def test_get_tags_is_deprecated_and_delegates(api_get: MagicMock, project: Project) -> None:
    tags = [OrganisationTag(uuid=uuid.uuid4(), name="my-tag")]
    api_get.return_value = Page(results=tags)

    with pytest.warns(DeprecationWarning, match="get_organisation_tags"):
        result = project.get_tags()

    assert result == tags
    api_get.assert_called_once()


TAG_IDENTIFIER_KINDS = ["instance", "uuid", "uuid-str", "name"]


def _tag_ref(tag: OrganisationTag, kind: str) -> Tuple[tuple, dict]:
    """Return the (args, kwargs) that reference `tag` in the given way."""
    return {
        "instance": ((tag,), {}),
        "uuid": ((), {"tag_uuid": tag.uuid}),
        "uuid-str": ((), {"tag_uuid": str(tag.uuid)}),
        "name": ((), {"tag_name": tag.name}),
    }[kind]


@pytest.mark.parametrize("kind", TAG_IDENTIFIER_KINDS)
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "put")
def test_add_organisation_tag_puts_to_project_tag_path(
    api_put: MagicMock, api_get: MagicMock, project: Project, kind: str
) -> None:
    tag = OrganisationTag(uuid=uuid.uuid4(), name="batch-3")
    api_get.return_value = Page(results=[OrganisationTag(uuid=uuid.uuid4(), name="batch-2"), tag])

    args, kwargs = _tag_ref(tag, kind)
    project.add_organisation_tag(*args, **kwargs)

    api_put.assert_called_once_with(f"projects/{project.project_hash}/tags/{tag.uuid}", params=None, payload=None)
    assert api_get.call_count == (1 if kind == "name" else 0)


@pytest.mark.parametrize("kind", TAG_IDENTIFIER_KINDS)
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_remove_organisation_tag_deletes_project_tag_path(
    api_delete: MagicMock, api_get: MagicMock, project: Project, kind: str
) -> None:
    tag = OrganisationTag(uuid=uuid.uuid4(), name="batch-3")
    api_get.return_value = Page(results=[tag])

    args, kwargs = _tag_ref(tag, kind)
    project.remove_organisation_tag(*args, **kwargs)

    api_delete.assert_called_once_with(
        f"projects/{project.project_hash}/tags/{tag.uuid}", params=None, result_type=None
    )
    assert api_get.call_count == (1 if kind == "name" else 0)


@pytest.mark.parametrize("bad_tag", [pytest.param("batch-3", id="str"), pytest.param(uuid.uuid4(), id="UUID")])
@pytest.mark.parametrize("method_name", ["add_organisation_tag", "remove_organisation_tag"])
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "put")
@patch.object(ApiClient, "delete")
def test_add_and_remove_organisation_tag_reject_positional_identifiers(
    api_delete: MagicMock, api_put: MagicMock, api_get: MagicMock, project: Project, method_name: str, bad_tag: object
) -> None:
    with pytest.raises(TypeError, match="OrganisationTag"):
        getattr(project, method_name)(bad_tag)

    api_get.assert_not_called()
    api_put.assert_not_called()
    api_delete.assert_not_called()


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "put")
def test_add_organisation_tag_by_unknown_name_raises(api_put: MagicMock, api_get: MagicMock, project: Project) -> None:
    api_get.return_value = Page(results=[OrganisationTag(uuid=uuid.uuid4(), name="batch-2")])

    with pytest.raises(ResourceNotFoundError):
        project.add_organisation_tag(tag_name="batch-3")

    api_put.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({}, id="neither"),
        pytest.param({"tag_name": "batch-3", "tag_uuid": uuid.uuid4()}, id="name-and-uuid"),
        pytest.param(
            {"tag": OrganisationTag(uuid=uuid.uuid4(), name="batch-3"), "tag_name": "batch-3"}, id="instance-and-name"
        ),
    ],
)
@pytest.mark.parametrize("method_name", ["add_organisation_tag", "remove_organisation_tag"])
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "put")
@patch.object(ApiClient, "delete")
def test_add_and_remove_organisation_tag_require_exactly_one_identifier(
    api_delete: MagicMock, api_put: MagicMock, api_get: MagicMock, project: Project, method_name: str, kwargs: dict
) -> None:
    with pytest.raises(ValueError, match="Exactly one of"):
        getattr(project, method_name)(**kwargs)

    api_get.assert_not_called()
    api_put.assert_not_called()
    api_delete.assert_not_called()


@patch.object(ApiClient, "delete")
@patch.object(ApiClient, "put")
@patch.object(ApiClient, "get")
def test_add_and_remove_organisation_tag_invalidate_tags_cache(
    api_get: MagicMock, api_put: MagicMock, api_delete: MagicMock, project: Project
) -> None:
    tag = OrganisationTag(uuid=uuid.uuid4(), name="batch-3")
    api_get.return_value = Page(results=[tag])

    project.get_organisation_tags()
    project.add_organisation_tag(tag_uuid=tag.uuid)
    project.get_organisation_tags()
    project.remove_organisation_tag(tag_uuid=tag.uuid)
    project.get_organisation_tags()

    assert api_get.call_count == 3


@patch.object(EncordClientProject, "get_label_rows")
def test_get_label_rows_reconstructs_frame_classifications(get_label_rows_mock: MagicMock, project: Project):
    """The deprecated label row functions hand the raw response to the caller.

    The backend serves classifications through `classification_answers` only, so the SDK reconstructs the
    per-frame classifications to keep the shape of the returned dict intact.
    """
    get_label_rows_mock.return_value = [
        LabelRow(
            {
                "data_type": "video",
                "classification_answers": {
                    "clf": {
                        "classificationHash": "clf",
                        "featureHash": "feature",
                        "classifications": [{"name": "A classification", "value": "a_classification"}],
                        "createdBy": "user@encord.com",
                        "createdAt": "Tue, 05 Nov 2024 09:41:37 UTC",
                        "range": [[0, 1]],
                        "spaces": {},
                    }
                },
                "object_answers": {},
                "data_units": {
                    "data-hash": {
                        "labels": {
                            "0": {"objects": [], "classifications": []},
                            "1": {"objects": [], "classifications": []},
                        }
                    }
                },
            }
        )
    ]

    label_rows = project.get_label_rows(["label-hash"])

    frames = label_rows[0]["data_units"]["data-hash"]["labels"]
    for frame in ("0", "1"):
        assert [c["classificationHash"] for c in frames[frame]["classifications"]] == ["clf"]
        assert frames[frame]["classifications"][0]["name"] == "A classification"
        assert frames[frame]["classifications"][0]["createdBy"] == "user@encord.com"
