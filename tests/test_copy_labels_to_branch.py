from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from encord import Project
from encord.client import EncordClientProject
from encord.http.v2.api_client import ApiClient
from encord.orm.label_row import LabelRowMetadata
from tests.test_data.label_rows_metadata_blurb import LABEL_ROW_METADATA_BLURB

# Label hashes from the test blurb (3 entries total)
_LABEL_HASH_1 = "44e1bdfb-3c45-4edb-8a71-a969f22fd632"
_LABEL_HASH_2 = "2321fd7d-99cd-4d85-b371-9a9f59cf79a7"
_LABEL_HASH_3 = "f6dcda1a-8e0a-45b2-a3c5-d7ebfe93ad8a"
_ALL_LABEL_HASHES = {_LABEL_HASH_1, _LABEL_HASH_2, _LABEL_HASH_3}

_SOURCE_BRANCH = "main"
_TARGET_BRANCH = "copy-branch"


def _make_metadata(rows=LABEL_ROW_METADATA_BLURB):
    return [LabelRowMetadata.from_dict(r) for r in rows]


def _copy_result(copied_count: int) -> MagicMock:
    result = MagicMock()
    result.copied_count = copied_count
    return result


# ---------------------------------------------------------------------------
# Same-branch guard — no API calls expected
# ---------------------------------------------------------------------------


def test_copy_labels_same_branch_raises(project: Project):
    with pytest.raises(ValueError, match="must be different"):
        project.copy_labels_to_branch(
            target_branch=_SOURCE_BRANCH,
            source_branch=_SOURCE_BRANCH,
        )


# ---------------------------------------------------------------------------
# Basic copy — two label rows, one batch
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_basic(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    list_rows_mock.return_value = _make_metadata()
    api_post_mock.return_value = _copy_result(3)

    count = project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
    )

    assert count == 3
    api_post_mock.assert_called_once()
    # label_uuids in the payload should contain all 3 hashes
    payload = api_post_mock.call_args.kwargs["payload"]
    assert set(payload.label_uuids) == _ALL_LABEL_HASHES


# ---------------------------------------------------------------------------
# Uninitialised rows (label_hash=None) are skipped
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_skips_uninitialised_rows(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    # First row is uninitialised; only the remaining two should be copied
    uninitialised = {**LABEL_ROW_METADATA_BLURB[0], "label_hash": None}
    rows = [uninitialised, LABEL_ROW_METADATA_BLURB[1], LABEL_ROW_METADATA_BLURB[2]]
    list_rows_mock.return_value = [LabelRowMetadata.from_dict(r) for r in rows]
    api_post_mock.return_value = _copy_result(2)

    count = project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
    )

    assert count == 2
    payload = api_post_mock.call_args.kwargs["payload"]
    assert set(payload.label_uuids) == {_LABEL_HASH_2, _LABEL_HASH_3}


# ---------------------------------------------------------------------------
# No initialised rows — post should never be called
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_no_initialised_rows(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    uninitialised = [{**r, "label_hash": None} for r in LABEL_ROW_METADATA_BLURB]
    list_rows_mock.return_value = [LabelRowMetadata.from_dict(r) for r in uninitialised]

    count = project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
    )

    assert count == 0
    api_post_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Batching — batch_size=1 should produce one API call per row
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_batching(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    list_rows_mock.return_value = _make_metadata()
    api_post_mock.return_value = _copy_result(1)

    count = project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
        batch_size=1,
    )

    assert count == 3  # 1 per batch × 3 batches
    assert api_post_mock.call_count == 3

    all_sent = []
    for c in api_post_mock.call_args_list:
        all_sent.extend(c.kwargs["payload"].label_uuids)
        assert len(c.kwargs["payload"].label_uuids) == 1

    assert set(all_sent) == _ALL_LABEL_HASHES


# ---------------------------------------------------------------------------
# overwrite=True is forwarded in the payload
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_overwrite_flag(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    list_rows_mock.return_value = _make_metadata()
    api_post_mock.return_value = _copy_result(2)

    project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
        overwrite=True,
    )

    payload = api_post_mock.call_args.kwargs["payload"]
    assert payload.overwrite is True


# ---------------------------------------------------------------------------
# data_hashes filter is forwarded to list_label_rows_v2
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_data_hashes_filter(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    data_hash = "9b45984a-0046-4389-ba0d-b73b6b35ee82"
    list_rows_mock.return_value = _make_metadata([LABEL_ROW_METADATA_BLURB[0]])
    api_post_mock.return_value = _copy_result(1)

    count = project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
        data_hashes=[data_hash],
    )

    assert count == 1
    # The data_hash filter should have been passed through to list_label_rows
    list_rows_mock.assert_called_once()
    call_kwargs = list_rows_mock.call_args.kwargs
    assert data_hash in [str(h) for h in (call_kwargs.get("data_hashes") or [])]


# ---------------------------------------------------------------------------
# label_hashes filter is forwarded to list_label_rows_v2
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_label_hashes_filter(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    list_rows_mock.return_value = _make_metadata([LABEL_ROW_METADATA_BLURB[0]])
    api_post_mock.return_value = _copy_result(1)

    count = project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
        label_hashes=[_LABEL_HASH_1],
    )

    assert count == 1
    list_rows_mock.assert_called_once()
    call_kwargs = list_rows_mock.call_args.kwargs
    assert _LABEL_HASH_1 in [str(h) for h in (call_kwargs.get("label_hashes") or [])]


# ---------------------------------------------------------------------------
# UUID objects accepted alongside strings
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_accepts_uuid_objects(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    list_rows_mock.return_value = _make_metadata([LABEL_ROW_METADATA_BLURB[0]])
    api_post_mock.return_value = _copy_result(1)

    project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
        data_hashes=[UUID("9b45984a-0046-4389-ba0d-b73b6b35ee82")],
        label_hashes=[UUID(_LABEL_HASH_1)],
    )

    list_rows_mock.assert_called_once()


# ---------------------------------------------------------------------------
# source_branch and target_branch are forwarded correctly in payload
# ---------------------------------------------------------------------------


@patch.object(ApiClient, "post")
@patch.object(EncordClientProject, "list_label_rows")
def test_copy_labels_branch_names_in_payload(list_rows_mock: MagicMock, api_post_mock: MagicMock, project: Project):
    list_rows_mock.return_value = _make_metadata()
    api_post_mock.return_value = _copy_result(2)

    project.copy_labels_to_branch(
        target_branch=_TARGET_BRANCH,
        source_branch=_SOURCE_BRANCH,
    )

    payload = api_post_mock.call_args.kwargs["payload"]
    assert payload.source_branch_name == _SOURCE_BRANCH
    assert payload.target_branch_name == _TARGET_BRANCH
