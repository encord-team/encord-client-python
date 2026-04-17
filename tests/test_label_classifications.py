import uuid
from unittest.mock import MagicMock, patch

from encord.http.v2.api_client import ApiClient
from encord.orm.project import (
    BulkClassificationsPayload,
    BulkClassificationsResponse,
    LabelClassificationsEntry,
)
from encord.project import Project


def _make_entry(**overrides) -> LabelClassificationsEntry:
    defaults = dict(label_uuid=uuid.uuid4(), data_uuid=uuid.uuid4())
    defaults.update(overrides)
    return LabelClassificationsEntry(**defaults)


def _make_response(*entries: LabelClassificationsEntry) -> BulkClassificationsResponse:
    return BulkClassificationsResponse(labels=list(entries))


@patch.object(ApiClient, "post")
def test_single_batch(api_post: MagicMock, project: Project) -> None:
    entry = _make_entry()
    api_post.return_value = _make_response(entry)

    label_uuids = [uuid.uuid4() for _ in range(3)]
    result = list(project.get_label_classifications(label_uuids))

    api_post.assert_called_once()
    _, kwargs = api_post.call_args
    assert kwargs["payload"] == BulkClassificationsPayload(
        label_uuids=[str(u) for u in label_uuids],
        branch_name="main",
    )
    assert kwargs["result_type"] is BulkClassificationsResponse
    assert f"projects/{project.project_hash}/label-rows/classifications" in api_post.call_args.args[0]
    assert result == [entry]


@patch.object(ApiClient, "post")
def test_multiple_batches(api_post: MagicMock, project: Project) -> None:
    entry_a = _make_entry()
    entry_b = _make_entry()
    api_post.side_effect = [_make_response(entry_a), _make_response(entry_b)]

    label_uuids = [uuid.uuid4() for _ in range(5)]
    result = list(project.get_label_classifications(label_uuids, batch_size=3))

    assert api_post.call_count == 2

    first_payload = api_post.call_args_list[0][1]["payload"]
    second_payload = api_post.call_args_list[1][1]["payload"]
    assert first_payload.label_uuids == [str(u) for u in label_uuids[:3]]
    assert second_payload.label_uuids == [str(u) for u in label_uuids[3:]]

    assert result == [entry_a, entry_b]


@patch.object(ApiClient, "post")
def test_custom_branch_name(api_post: MagicMock, project: Project) -> None:
    api_post.return_value = _make_response(_make_entry())

    list(project.get_label_classifications([uuid.uuid4()], branch_name="my-branch"))

    payload = api_post.call_args[1]["payload"]
    assert payload.branch_name == "my-branch"


@patch.object(ApiClient, "post")
def test_empty_input(api_post: MagicMock, project: Project) -> None:
    result = list(project.get_label_classifications([]))

    api_post.assert_not_called()
    assert result == []
