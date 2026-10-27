"""Tests for label sets.

The backend is mocked at the ``ApiClient`` boundary. The serialisation tests pin the wire shapes the
backend expects (camelCase, ``id`` for the identifier, ``items`` for pages), and the update tests pin that
the trigger and selection the server returned are sent back on every PUT, since PUT is a full replacement.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional
from unittest.mock import MagicMock

import pytest

from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import ItemsPage
from encord.label_set import LabelSet
from encord.orm.base_dto import BaseDTO
from encord.orm.label_set import (
    CreateLabelSetPayload,
    CutLabelSetVersionPayload,
    FilteredLabelSelection,
    LabelSetLabellingStatus,
    LabelSetOrigin,
    LabelSetSummary,
    LabelSetVersion,
    LabelSetVersionMember,
    LabelSetVersionStatus,
    ListLabelSetsParams,
    ListLabelSetVersionsParams,
    SelectiveLabelSelection,
    UpdateLabelSetPayload,
)
from encord.orm.label_set import LabelSet as OrmLabelSet

LABEL_SET_UUID = uuid.UUID("8c1d0e2f-4a5b-6c7d-8e9f-0a1b2c3d4e5f")
PROJECT_HASH = uuid.UUID("1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d")
VERSION_UUID = uuid.UUID("2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e")
STAGE_UUID = uuid.UUID("3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f")
DATA_HASH = "4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a"
CREATED_AT = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)

INTERVAL_TRIGGER: Dict[str, Any] = {"type": "INTERVAL", "interval": "PT6H"}


def label_set_response(**overrides) -> Dict[str, Any]:
    """A label set as the get, create and update endpoints return it."""
    body: Dict[str, Any] = {
        "id": str(LABEL_SET_UUID),
        "projectHash": str(PROJECT_HASH),
        "branchName": "main",
        "name": "nightly",
        "description": "Labels for the nightly build",
        "origin": "WORKFLOW",
        "trigger": {"type": "MANUAL"},
        "createdBy": "user-hash",
        "createdAt": "2026-10-27T12:00:00Z",
        "labelSelectionMode": None,
    }
    body.update(overrides)
    return body


def summary_response(**overrides) -> Dict[str, Any]:
    """A label set as the list endpoint returns it: no selection."""
    body = label_set_response(**overrides)
    del body["labelSelectionMode"]
    return body


def version_response(**overrides) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "id": str(VERSION_UUID),
        "labelSetId": str(LABEL_SET_UUID),
        "versionNumber": 1,
        "name": "v1",
        "status": "READY",
        "triggerType": "MANUAL",
        "createdBy": "user-hash",
        "captureStartedAt": "2026-10-27T12:00:00Z",
        "captureFinishedAt": "2026-10-27T12:00:05Z",
        "labelCount": 42,
    }
    body.update(overrides)
    return body


def make_label_set(orm: Optional[BaseDTO] = None) -> "tuple[LabelSet, MagicMock]":
    client = MagicMock(spec=ApiClient)
    return LabelSet(client, orm or OrmLabelSet.from_dict(label_set_response())), client


# --- response deserialisation --------------------------------------------------------------------


def test_label_set_response_parses_camel_case_and_id():
    orm = OrmLabelSet.from_dict(label_set_response())

    assert orm.uuid == LABEL_SET_UUID
    assert orm.project_hash == PROJECT_HASH
    assert orm.branch_name == "main"
    assert orm.origin is LabelSetOrigin.WORKFLOW
    assert orm.trigger == {"type": "MANUAL"}
    assert orm.created_by == "user-hash"
    assert orm.created_at == CREATED_AT
    assert orm.label_selection_mode is None


def test_label_set_response_parses_selective_selection():
    orm = OrmLabelSet.from_dict(label_set_response(labelSelectionMode={"tag": "SELECTIVE", "dataHashes": [DATA_HASH]}))

    assert isinstance(orm.label_selection_mode, SelectiveLabelSelection)
    assert orm.label_selection_mode.data_hashes == [DATA_HASH]


def test_label_set_response_parses_filtered_selection():
    orm = OrmLabelSet.from_dict(
        label_set_response(
            labelSelectionMode={
                "tag": "FILTERED",
                "dataTitleSearch": "scene",
                "filterGraphNodeUuid": [str(STAGE_UUID)],
                "filterLabellingStatus": "LABELLED",
            }
        )
    )

    assert isinstance(orm.label_selection_mode, FilteredLabelSelection)
    assert orm.label_selection_mode.data_title_search == "scene"
    assert orm.label_selection_mode.filter_graph_node_uuid == [STAGE_UUID]
    assert orm.label_selection_mode.filter_labelling_status is LabelSetLabellingStatus.LABELLED


def test_label_set_response_keeps_unknown_trigger_shape():
    """The trigger is passed through untouched, so a shape the SDK has never seen must not fail."""
    orm = OrmLabelSet.from_dict(label_set_response(trigger={"type": "TASK_COUNT", "taskCount": 500, "new": 1}))

    assert orm.trigger == {"type": "TASK_COUNT", "taskCount": 500, "new": 1}


def test_label_set_response_ignores_fields_added_later():
    orm = OrmLabelSet.from_dict(label_set_response(nextCutAt="2026-10-28T00:00:00Z", scheduleError=None))

    assert orm.uuid == LABEL_SET_UUID


def test_summary_response_parses_without_selection():
    orm = LabelSetSummary.from_dict(summary_response())

    assert orm.uuid == LABEL_SET_UUID
    assert not hasattr(orm, "label_selection_mode")


def test_version_response_parses_camel_case_and_id():
    orm = LabelSetVersion.from_dict(version_response())

    assert orm.uuid == VERSION_UUID
    assert orm.label_set_uuid == LABEL_SET_UUID
    assert orm.version_number == 1
    assert orm.status is LabelSetVersionStatus.READY
    assert orm.trigger_type == "MANUAL"
    assert orm.capture_started_at == CREATED_AT
    assert orm.capture_finished_at == datetime(2026, 10, 27, 12, 0, 5, tzinfo=timezone.utc)
    assert orm.label_count == 42


def test_building_version_has_no_finish_time_or_count():
    orm = LabelSetVersion.from_dict(version_response(status="BUILDING", captureFinishedAt=None, labelCount=None))

    assert orm.status is LabelSetVersionStatus.BUILDING
    assert orm.capture_finished_at is None
    assert orm.label_count is None


def test_unknown_enum_values_parse_as_unknown():
    """A newer backend may add origins and statuses. Clients ignore unknown enum values rather than failing."""
    label_set = OrmLabelSet.from_dict(label_set_response(origin="MERGED"))
    version = LabelSetVersion.from_dict(version_response(status="CANCELLED"))

    assert label_set.origin is LabelSetOrigin.UNKNOWN
    assert version.status is LabelSetVersionStatus.UNKNOWN


def test_member_response_parses_camel_case():
    orm = LabelSetVersionMember.from_dict(
        {
            "labelHash": "label-hash",
            "labelVersion": 3,
            "backingItemUuid": None,
            "dataHash": DATA_HASH,
            "dataTitle": "scene_001.mp4",
        }
    )

    assert orm.label_hash == "label-hash"
    assert orm.label_version == 3
    assert orm.backing_item_uuid is None
    assert orm.data_hash == DATA_HASH
    assert orm.data_title == "scene_001.mp4"


# --- request serialisation -----------------------------------------------------------------------
#
# The backend rejects unknown keys, so these pin the exact key set as well as the casing.


def test_create_payload_defaults_to_manual_trigger_and_no_selection():
    payload = CreateLabelSetPayload(project_hash=PROJECT_HASH, name="nightly")

    assert payload.to_dict() == {
        "projectHash": str(PROJECT_HASH),
        "name": "nightly",
        "description": "",
        "trigger": {"type": "MANUAL"},
    }


def test_create_payload_serialises_selective_selection():
    payload = CreateLabelSetPayload(
        project_hash=PROJECT_HASH,
        name="nightly",
        label_selection_mode=SelectiveLabelSelection(data_hashes=[DATA_HASH]),
    )

    assert payload.to_dict()["labelSelectionMode"] == {"tag": "SELECTIVE", "dataHashes": [DATA_HASH]}


def test_create_payload_serialises_filtered_selection_with_every_key():
    """``dataTitleSearch`` and ``filterGraphNodeUuid`` are required by the backend, so defaults are sent."""
    payload = CreateLabelSetPayload(
        project_hash=PROJECT_HASH,
        name="nightly",
        label_selection_mode=FilteredLabelSelection(filter_labelling_status=LabelSetLabellingStatus.IN_PROGRESS),
    )

    assert payload.to_dict()["labelSelectionMode"] == {
        "tag": "FILTERED",
        "dataTitleSearch": "",
        "filterGraphNodeUuid": [],
        "filterLabellingStatus": "IN_PROGRESS",
    }


def test_filtered_selection_serialises_stage_uuids_as_strings():
    selection = FilteredLabelSelection(filter_graph_node_uuid=[STAGE_UUID])

    assert selection.to_dict()["filterGraphNodeUuid"] == [str(STAGE_UUID)]


def test_update_payload_has_no_project_hash():
    payload = UpdateLabelSetPayload(name="nightly", description="d", trigger=INTERVAL_TRIGGER)

    assert payload.to_dict() == {"name": "nightly", "description": "d", "trigger": INTERVAL_TRIGGER}


def test_cut_payload_omits_name_when_not_given():
    assert CutLabelSetVersionPayload().to_dict() == {}
    assert CutLabelSetVersionPayload(name="release").to_dict() == {"name": "release"}


def test_list_params_use_backend_query_names():
    assert ListLabelSetsParams(project_hash=PROJECT_HASH, limit=10).to_dict() == {
        "projectHash": str(PROJECT_HASH),
        "limit": 10,
    }
    assert ListLabelSetVersionsParams(limit=5, page_token="abc").to_dict() == {"limit": 5, "pageToken": "abc"}


# --- paging over ``items`` -----------------------------------------------------------------------


class _Item(BaseDTO):
    value: int


class _Params(BaseDTO):
    page_token: Optional[str] = None


def test_items_page_parses_items_and_token():
    page = ItemsPage[_Item].from_dict({"items": [{"value": 1}], "nextPageToken": "t2"})

    assert [item.value for item in page.items] == [1]
    assert page.next_page_token == "t2"


def test_items_paged_iterator_follows_next_page_token():
    client = ApiClient.__new__(ApiClient)
    seen_tokens: List[Optional[str]] = []
    pages: Iterator[ItemsPage[_Item]] = iter(
        [
            ItemsPage[_Item](items=[_Item(value=1), _Item(value=2)], next_page_token="t2"),
            ItemsPage[_Item](items=[_Item(value=3)], next_page_token=None),
        ]
    )

    def fake_get(path, params, result_type, allow_none=False):
        seen_tokens.append(params.page_token)
        return next(pages)

    client.get = fake_get  # type: ignore[method-assign]

    values = [item.value for item in client.get_items_paged_iterator("label-sets", _Params(), _Item)]

    assert values == [1, 2, 3]
    assert seen_tokens == [None, "t2"]


def test_items_paged_iterator_requires_page_token_param():
    client = ApiClient.__new__(ApiClient)

    with pytest.raises(ValueError):
        list(client.get_items_paged_iterator("label-sets", _Item(value=1), _Item))


# --- LabelSet wrapper ----------------------------------------------------------------------------


def test_properties_come_from_the_record():
    label_set, _ = make_label_set()

    assert label_set.uuid == LABEL_SET_UUID
    assert label_set.project_hash == PROJECT_HASH
    assert label_set.name == "nightly"
    assert label_set.description == "Labels for the nightly build"
    assert label_set.origin is LabelSetOrigin.WORKFLOW
    assert label_set.trigger == {"type": "MANUAL"}
    assert label_set.created_at == CREATED_AT
    assert label_set.label_selection_mode is None


def test_create_posts_expected_request():
    client = MagicMock(spec=ApiClient)
    client.post.return_value = OrmLabelSet.from_dict(label_set_response())

    label_set = LabelSet._create_label_set(
        client,
        project_hash=PROJECT_HASH,
        name="nightly",
        description="d",
        label_selection_mode=SelectiveLabelSelection(data_hashes=[DATA_HASH]),
    )

    args, kwargs = client.post.call_args
    assert args[0] == "label-sets"
    assert kwargs["payload"] == CreateLabelSetPayload(
        project_hash=PROJECT_HASH,
        name="nightly",
        description="d",
        label_selection_mode=SelectiveLabelSelection(data_hashes=[DATA_HASH]),
    )
    assert kwargs["result_type"] is OrmLabelSet
    assert kwargs["allow_retries"] is False
    assert label_set.uuid == LABEL_SET_UUID


def test_get_fetches_by_uuid():
    client = MagicMock(spec=ApiClient)
    client.get.return_value = OrmLabelSet.from_dict(label_set_response())

    label_set = LabelSet._get_label_set(client, LABEL_SET_UUID)

    client.get.assert_called_once_with(f"label-sets/{LABEL_SET_UUID}", params=None, result_type=OrmLabelSet)
    assert label_set.uuid == LABEL_SET_UUID


def test_list_pages_over_items_with_project_filter():
    client = MagicMock(spec=ApiClient)
    client.get_items_paged_iterator.return_value = iter([LabelSetSummary.from_dict(summary_response())])

    label_sets = list(LabelSet._list_label_sets(client, project_hash=PROJECT_HASH, page_size=10))

    args, kwargs = client.get_items_paged_iterator.call_args
    assert args[0] == "label-sets"
    assert kwargs["params"] == ListLabelSetsParams(project_hash=PROJECT_HASH, limit=10)
    assert kwargs["result_type"] is LabelSetSummary
    assert [label_set.uuid for label_set in label_sets] == [LABEL_SET_UUID]


def test_listed_set_fetches_the_full_record_when_the_selection_is_read():
    """The list endpoint omits the selection, so reading it costs one GET, and only one."""
    label_set, client = make_label_set(LabelSetSummary.from_dict(summary_response()))
    client.get.return_value = OrmLabelSet.from_dict(
        label_set_response(labelSelectionMode={"tag": "SELECTIVE", "dataHashes": [DATA_HASH]})
    )

    assert label_set.name == "nightly"
    client.get.assert_not_called()

    first = label_set.label_selection_mode
    second = label_set.label_selection_mode

    client.get.assert_called_once_with(f"label-sets/{LABEL_SET_UUID}", params=None, result_type=OrmLabelSet)
    assert isinstance(first, SelectiveLabelSelection)
    assert second is first


# --- update sends the current trigger and selection back ----------------------------------------
#
# PUT is a full replacement on the server: an omitted trigger resets to MANUAL and an omitted
# selection clears it. A rename must therefore carry both back unchanged.


def test_update_name_resends_trigger_description_and_selection():
    label_set, client = make_label_set(
        OrmLabelSet.from_dict(
            label_set_response(
                trigger=INTERVAL_TRIGGER,
                labelSelectionMode={"tag": "SELECTIVE", "dataHashes": [DATA_HASH]},
            )
        )
    )
    client.put.return_value = OrmLabelSet.from_dict(label_set_response(name="weekly", trigger=INTERVAL_TRIGGER))

    label_set.update(name="weekly")

    args, kwargs = client.put.call_args
    assert args[0] == f"label-sets/{LABEL_SET_UUID}"
    assert kwargs["payload"].to_dict() == {
        "name": "weekly",
        "description": "Labels for the nightly build",
        "trigger": INTERVAL_TRIGGER,
        "labelSelectionMode": {"tag": "SELECTIVE", "dataHashes": [DATA_HASH]},
    }
    assert kwargs["result_type"] is OrmLabelSet
    assert label_set.name == "weekly"


def test_update_description_keeps_name():
    label_set, client = make_label_set()
    client.put.return_value = OrmLabelSet.from_dict(label_set_response(description="new"))

    label_set.update(description="new")

    assert client.put.call_args.kwargs["payload"].to_dict() == {
        "name": "nightly",
        "description": "new",
        "trigger": {"type": "MANUAL"},
    }


def test_update_on_a_listed_set_fetches_the_full_record_first():
    """A summary has no selection, so updating from one would silently clear it without the fetch."""
    label_set, client = make_label_set(LabelSetSummary.from_dict(summary_response(trigger=INTERVAL_TRIGGER)))
    client.get.return_value = OrmLabelSet.from_dict(
        label_set_response(
            trigger=INTERVAL_TRIGGER,
            labelSelectionMode={"tag": "FILTERED", "dataTitleSearch": "x", "filterGraphNodeUuid": []},
        )
    )
    client.put.return_value = client.get.return_value

    label_set.update(name="weekly")

    client.get.assert_called_once()
    sent = client.put.call_args.kwargs["payload"].to_dict()
    assert sent["trigger"] == INTERVAL_TRIGGER
    assert sent["labelSelectionMode"] == {"tag": "FILTERED", "dataTitleSearch": "x", "filterGraphNodeUuid": []}


def test_set_label_selection_mode_replaces_selection_and_keeps_the_rest():
    label_set, client = make_label_set(OrmLabelSet.from_dict(label_set_response(trigger=INTERVAL_TRIGGER)))
    client.put.return_value = OrmLabelSet.from_dict(
        label_set_response(
            trigger=INTERVAL_TRIGGER,
            labelSelectionMode={"tag": "SELECTIVE", "dataHashes": [DATA_HASH]},
        )
    )

    label_set.set_label_selection_mode(SelectiveLabelSelection(data_hashes=[DATA_HASH]))

    assert client.put.call_args.kwargs["payload"].to_dict() == {
        "name": "nightly",
        "description": "Labels for the nightly build",
        "trigger": INTERVAL_TRIGGER,
        "labelSelectionMode": {"tag": "SELECTIVE", "dataHashes": [DATA_HASH]},
    }
    assert isinstance(label_set.label_selection_mode, SelectiveLabelSelection)


def test_set_label_selection_mode_none_omits_the_key():
    label_set, client = make_label_set(
        OrmLabelSet.from_dict(label_set_response(labelSelectionMode={"tag": "SELECTIVE", "dataHashes": [DATA_HASH]}))
    )
    client.put.return_value = OrmLabelSet.from_dict(label_set_response())

    label_set.set_label_selection_mode(None)

    assert "labelSelectionMode" not in client.put.call_args.kwargs["payload"].to_dict()
    assert label_set.label_selection_mode is None


# --- versions ------------------------------------------------------------------------------------


def test_cut_version_posts_name_and_returns_the_version():
    label_set, client = make_label_set()
    client.post.return_value = LabelSetVersion.from_dict(version_response(name="release"))

    version = label_set.cut_version(name="release")

    args, kwargs = client.post.call_args
    assert args[0] == f"label-sets/{LABEL_SET_UUID}/versions"
    assert kwargs["payload"] == CutLabelSetVersionPayload(name="release")
    assert kwargs["result_type"] is LabelSetVersion
    assert kwargs["allow_retries"] is False
    assert version.name == "release"


def test_list_versions_pages_over_items():
    label_set, client = make_label_set()
    client.get_items_paged_iterator.return_value = iter([LabelSetVersion.from_dict(version_response())])

    versions = list(label_set.list_versions(page_size=5))

    args, kwargs = client.get_items_paged_iterator.call_args
    assert args[0] == f"label-sets/{LABEL_SET_UUID}/versions"
    assert kwargs["params"] == ListLabelSetVersionsParams(limit=5)
    assert kwargs["result_type"] is LabelSetVersion
    assert [version.uuid for version in versions] == [VERSION_UUID]


def test_get_version_accepts_a_string_uuid():
    label_set, client = make_label_set()
    client.get.return_value = LabelSetVersion.from_dict(version_response())

    version = label_set.get_version(str(VERSION_UUID))

    client.get.assert_called_once_with(
        f"label-sets/{LABEL_SET_UUID}/versions/{VERSION_UUID}", params=None, result_type=LabelSetVersion
    )
    assert version.uuid == VERSION_UUID


def test_list_version_members_accepts_version_or_uuid():
    label_set, client = make_label_set()
    client.get_items_paged_iterator.return_value = iter([])
    version = LabelSetVersion.from_dict(version_response())

    list(label_set.list_version_members(version))
    list(label_set.list_version_members(str(VERSION_UUID)))
    list(label_set.list_version_members(VERSION_UUID))

    paths = [call.args[0] for call in client.get_items_paged_iterator.call_args_list]
    assert paths == [f"label-sets/{LABEL_SET_UUID}/versions/{VERSION_UUID}/members"] * 3
    assert client.get_items_paged_iterator.call_args.kwargs["result_type"] is LabelSetVersionMember
