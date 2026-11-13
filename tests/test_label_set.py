from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock
from uuid import UUID

import pytest
from pydantic import ValidationError

from encord.exceptions import EncordException
from encord.http.v2.api_client import ApiClient
from encord.label_set import LabelSet, LabelSetVersion
from encord.orm.label_set import (
    AllSelection,
    CapturedSource,
    CreateLabelSetPayload,
    ExportFormat,
    LabelSetJob,
    LabelSetJobPending,
    LabelSetJobStatus,
    LabelSetJobUnknown,
    LabelSetOrigin,
    LabelSetVersionMember,
    LabelSetVersionStatus,
    ProjectSource,
    SetLabelSelectionPayload,
    StoredProjectSource,
    UnknownSelection,
    UnknownSource,
    UpdateLabelSetPayload,
    VersionExportJobDone,
    VersionExportJobFailed,
    VersionExportJobResponse,
    VersionJobDone,
    VersionJobFailed,
    VersionJobResponse,
    VersionOntology,
    WorkflowStageSelection,
)
from encord.orm.label_set import LabelSet as OrmLabelSet
from encord.orm.label_set import LabelSetVersion as OrmLabelSetVersion
from encord.user_client import EncordUserClient

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
LABEL_SET_ID = UUID("00000000-0000-0000-0000-000000000002")
VERSION_ID = UUID("00000000-0000-0000-0000-000000000003")
DATA_ID = UUID("00000000-0000-0000-0000-000000000004")
STAGE_ID = UUID("00000000-0000-0000-0000-000000000005")
JOB_ID = UUID("00000000-0000-0000-0000-00000000000a")
ONTOLOGY_ID = UUID("00000000-0000-0000-0000-00000000000b")
ONTOLOGY_VERSION_ID = UUID("00000000-0000-0000-0000-00000000000c")
SOURCE_ID = UUID("00000000-0000-0000-0000-00000000000d")
ITEM_ID = UUID("00000000-0000-0000-0000-00000000000f")
NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def _user_client(api_client: Mock) -> EncordUserClient:
    user_client = EncordUserClient(MagicMock(), MagicMock())  # type: ignore[arg-type]
    user_client._api_client = api_client
    return user_client


def _label_set_json(selection: Optional[Dict[str, Any]] = None, *, with_selection: bool = True) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "uuid": str(LABEL_SET_ID),
        "sources": [
            {"tag": "PROJECT", "uuid": str(SOURCE_ID), "projectUuid": str(PROJECT_ID), "branchName": "preds/model-7"}
        ],
        "name": "Model 7",
        "description": "",
        "origin": "import",
        "createdByEmail": "admin@example.com",
        "createdAt": NOW.isoformat(),
    }
    if with_selection:
        body["sources"][0]["labelSelectionMode"] = selection if selection is not None else {"tag": "ALL"}
    return body


def _orm_label_set(selection: Optional[Dict[str, Any]] = None) -> OrmLabelSet:
    return OrmLabelSet.from_dict(_label_set_json(selection))


def _orm_version(status: str = "ready") -> OrmLabelSetVersion:
    return OrmLabelSetVersion.from_dict(
        {
            "uuid": str(VERSION_ID),
            "labelSetUuid": str(LABEL_SET_ID),
            "sources": [
                {
                    "tag": "PROJECT",
                    "projectUuid": str(PROJECT_ID),
                    "branchName": "preds/model-7",
                    "ontologyUuid": str(ONTOLOGY_ID),
                    "ontologyVersionUuid": str(ONTOLOGY_VERSION_ID),
                }
            ],
            "versionNumber": 1,
            "name": "v1",
            "status": status,
            "createdByEmail": "admin@example.com",
            "captureStartedAt": NOW.isoformat(),
            "captureFinishedAt": NOW.isoformat(),
            "labelCount": 3,
        }
    )


def _label_set(api_client: Mock) -> LabelSet:
    return LabelSet(api_client, _orm_label_set())


def _version(api_client: Mock) -> LabelSetVersion:
    return LabelSetVersion(api_client, _orm_version())


def test_create_label_set_sends_the_sources_and_origin_and_wraps_the_result() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.post.return_value = _orm_label_set()

    label_set = _user_client(api_client).create_label_set(
        "Model 7",
        sources=[ProjectSource(project_id=PROJECT_ID, branch_name="preds/model-7")],
        origin=LabelSetOrigin.IMPORT,
    )

    assert api_client.post.call_args.args == ("label-sets",)
    payload = api_client.post.call_args.kwargs["payload"]
    assert isinstance(payload, CreateLabelSetPayload)
    assert payload.to_dict() == {
        "sources": [
            {
                "tag": "PROJECT",
                "projectUuid": str(PROJECT_ID),
                "branchName": "preds/model-7",
                "labelSelectionMode": {"tag": "ALL"},
            }
        ],
        "name": "Model 7",
        "description": "",
        "origin": "import",
    }
    assert api_client.post.call_args.kwargs["allow_retries"] is False
    assert label_set.id == LABEL_SET_ID
    assert label_set.origin == LabelSetOrigin.IMPORT
    source = label_set.sources[0]
    assert isinstance(source, StoredProjectSource)
    assert (source.id, source.project_id, source.branch_name) == (SOURCE_ID, PROJECT_ID, "preds/model-7")
    assert source.label_selection == AllSelection()
    api_client.get.assert_not_called()


def test_create_label_set_sends_a_stage_selection_as_the_platform_stores_it() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.post.return_value = _orm_label_set()

    _user_client(api_client).create_label_set(
        "Training",
        sources=[
            ProjectSource(project_id=PROJECT_ID, label_selection=WorkflowStageSelection(workflow_stage_ids=[STAGE_ID]))
        ],
    )

    sent = api_client.post.call_args.kwargs["payload"].to_dict()
    assert "labelSelectionMode" not in sent
    assert sent["sources"][0]["projectUuid"] == str(PROJECT_ID)
    # The platform requires every filter of the stored shape, so the ones the SDK does not set are sent unset.
    assert sent["sources"][0]["labelSelectionMode"] == {
        "tag": "FILTERED",
        "dataTitleSearch": "",
        "filterGraphNodeUuid": [str(STAGE_ID)],
        "filterLabelingStatus": None,
    }


def test_create_label_set_refuses_the_unknown_origin_before_sending() -> None:
    api_client = Mock(spec=ApiClient)

    # UNKNOWN is a read-side placeholder; the platform has no such origin and would answer 422.
    with pytest.raises(ValueError, match="LabelSetOrigin.UNKNOWN"):
        _user_client(api_client).create_label_set(
            "Copy", sources=[ProjectSource(project_id=PROJECT_ID)], origin=LabelSetOrigin.UNKNOWN
        )

    api_client.post.assert_not_called()


def test_get_label_set_parses_a_stage_selection() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _orm_label_set(
        {"tag": "FILTERED", "dataTitleSearch": "", "filterGraphNodeUuid": [str(STAGE_ID)], "filterLabelingStatus": None}
    )

    label_set = _user_client(api_client).get_label_set(LABEL_SET_ID)

    assert api_client.get.call_args.args == (f"label-sets/{LABEL_SET_ID}",)
    source = label_set.sources[0]
    assert isinstance(source, StoredProjectSource)
    assert source.label_selection == WorkflowStageSelection(workflow_stage_ids=[STAGE_ID])


def test_list_label_sets_pages_and_leaves_the_selection_to_refetch_data() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get_paged_iterator.return_value = iter([OrmLabelSet.from_dict(_label_set_json(with_selection=False))])
    api_client.get.return_value = _orm_label_set(
        {"tag": "FILTERED", "dataTitleSearch": "", "filterGraphNodeUuid": [str(STAGE_ID)], "filterLabelingStatus": None}
    )

    label_sets = list(_user_client(api_client).list_label_sets(project_id=PROJECT_ID, page_size=10))

    assert api_client.get_paged_iterator.call_args.args == ("label-sets",)
    params = api_client.get_paged_iterator.call_args.kwargs["params"]
    assert params.to_dict() == {"projectUuid": str(PROJECT_ID), "pageSize": 10}
    assert [label_set.name for label_set in label_sets] == ["Model 7"]
    source = label_sets[0].sources[0]
    assert isinstance(source, StoredProjectSource)
    assert (source.id, source.project_id, source.branch_name) == (SOURCE_ID, PROJECT_ID, "preds/model-7")
    # The source metadata is available, but its omitted selection must not look like "capture all".
    with pytest.raises(EncordException, match="refetch_data"):
        source.label_selection
    api_client.get.assert_not_called()
    label_sets[0].refetch_data()
    assert api_client.get.call_args.args == (f"label-sets/{LABEL_SET_ID}",)
    refreshed_source = label_sets[0].sources[0]
    assert isinstance(refreshed_source, StoredProjectSource)
    assert refreshed_source.label_selection == WorkflowStageSelection(workflow_stage_ids=[STAGE_ID])


def test_update_patches_only_the_fields_given() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _orm_label_set()

    _label_set(api_client).update(name="Renamed")

    assert api_client.patch.call_args.args == (f"label-sets/{LABEL_SET_ID}",)
    payload = api_client.patch.call_args.kwargs["payload"]
    assert isinstance(payload, UpdateLabelSetPayload)
    assert payload.to_dict() == {"name": "Renamed"}


def test_update_clears_the_description_with_an_empty_string() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _orm_label_set()

    _label_set(api_client).update(description="")

    assert api_client.patch.call_args.kwargs["payload"].to_dict() == {"description": ""}


def test_update_with_nothing_to_change_sends_nothing() -> None:
    api_client = Mock(spec=ApiClient)

    _label_set(api_client).update()

    api_client.patch.assert_not_called()
    api_client.get.assert_not_called()


def test_set_label_selection_to_all_sends_the_explicit_tag() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _orm_label_set()

    _label_set(api_client).set_label_selection(str(SOURCE_ID), AllSelection())

    assert api_client.patch.call_args.args == (f"label-sets/{LABEL_SET_ID}/sources/{SOURCE_ID}",)
    payload = api_client.patch.call_args.kwargs["payload"]
    assert isinstance(payload, SetLabelSelectionPayload)
    # The platform never takes null for a selection; every label on the branch is an explicit shape.
    assert payload.to_dict() == {"labelSelectionMode": {"tag": "ALL"}}


def test_set_label_selection_sends_the_selection_whole() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _orm_label_set()

    _label_set(api_client).set_label_selection(SOURCE_ID, WorkflowStageSelection(workflow_stage_ids=[STAGE_ID]))

    assert api_client.patch.call_args.args == (f"label-sets/{LABEL_SET_ID}/sources/{SOURCE_ID}",)
    assert api_client.patch.call_args.kwargs["payload"].to_dict() == {
        "labelSelectionMode": {
            "tag": "FILTERED",
            "dataTitleSearch": "",
            "filterGraphNodeUuid": [str(STAGE_ID)],
            "filterLabelingStatus": None,
        }
    }


def test_create_version_job_posts_without_retries_and_returns_the_job_id() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.post.return_value = LabelSetJob(job_id=JOB_ID)

    job_id = _label_set(api_client).create_version_job("v1")

    assert job_id == JOB_ID
    assert api_client.post.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions",)
    assert api_client.post.call_args.kwargs["payload"].to_dict() == {"name": "v1"}
    assert api_client.post.call_args.kwargs["allow_retries"] is False
    api_client.get.assert_not_called()


def test_set_label_selection_targets_the_requested_source_of_a_listed_set() -> None:
    api_client = Mock(spec=ApiClient)
    body = _label_set_json(with_selection=False)
    second_source_id = UUID("00000000-0000-0000-0000-00000000000e")
    body["sources"].append({**body["sources"][0], "uuid": str(second_source_id), "branchName": "main"})
    api_client.get.return_value = _orm_label_set()
    label_set = LabelSet(api_client, OrmLabelSet.from_dict(body))

    label_set.set_label_selection(second_source_id, AllSelection())

    assert api_client.patch.call_args.args == (f"label-sets/{LABEL_SET_ID}/sources/{second_source_id}",)
    assert api_client.patch.call_args.kwargs["payload"].to_dict() == {"labelSelectionMode": {"tag": "ALL"}}
    # Only the post-write refresh fetches the set; selecting a source does not require a preliminary fetch.
    assert api_client.get.call_count == 1


def test_set_label_selection_rejects_a_malformed_source_id_before_sending() -> None:
    api_client = Mock(spec=ApiClient)

    with pytest.raises(ValueError):
        _label_set(api_client).set_label_selection("not-a-uuid", AllSelection())

    api_client.patch.assert_not_called()
    api_client.get.assert_not_called()


def test_get_version_job_reads_once_by_default() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = VersionJobResponse(LabelSetJobPending())

    job = _label_set(api_client).get_version_job(str(JOB_ID))

    assert job == LabelSetJobPending()
    assert api_client.get.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions/jobs/{JOB_ID}",)
    assert api_client.get.call_count == 1


def test_get_version_job_waits_with_backoff_until_done(monkeypatch: pytest.MonkeyPatch) -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.side_effect = [
        VersionJobResponse(LabelSetJobPending()),
        VersionJobResponse(LabelSetJobPending()),
        VersionJobResponse(VersionJobDone(version_id=VERSION_ID)),
    ]
    sleeps: List[float] = []
    monkeypatch.setattr("encord.label_set.time.sleep", sleeps.append)

    job = _label_set(api_client).get_version_job(JOB_ID, timeout_seconds=600)

    assert job == VersionJobDone(version_id=VERSION_ID)
    assert sleeps == [1.0, 2.0]
    assert api_client.get.call_count == 3


def test_get_version_job_returns_the_failure_reason() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = VersionJobResponse(VersionJobFailed(error="No labels to capture"))

    job = _label_set(api_client).get_version_job(JOB_ID, timeout_seconds=600)

    assert job == VersionJobFailed(error="No labels to capture")


def test_get_version_job_reports_pending_when_the_wait_ends(monkeypatch: pytest.MonkeyPatch) -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = VersionJobResponse(LabelSetJobPending())
    clock = iter([0.0, 0.0, 10.0])
    monkeypatch.setattr("encord.label_set.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("encord.label_set.time.sleep", lambda _: None)

    # The job is not cancelled and nothing is raised. The caller still holds the id and can read it again.
    job = _label_set(api_client).get_version_job(JOB_ID, timeout_seconds=5)

    assert job == LabelSetJobPending()
    assert api_client.get.call_count == 2


def test_get_version_job_raises_an_encord_exception_for_a_state_it_cannot_parse() -> None:
    api_client = Mock(spec=ApiClient)
    # The API client validates a root model directly, so a failed state without its error raises pydantic's error.
    api_client.get.side_effect = lambda *args, **kwargs: VersionJobResponse.model_validate({"status": "failed"})

    with pytest.raises(EncordException, match="job state"):
        _label_set(api_client).get_version_job(JOB_ID, timeout_seconds=600)


def test_get_export_job_raises_an_encord_exception_for_a_state_it_cannot_parse() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.side_effect = lambda *args, **kwargs: VersionExportJobResponse.model_validate({"status": "done"})

    with pytest.raises(EncordException, match="job state"):
        _version(api_client).get_export_job(JOB_ID)


def test_get_version_loads_the_ready_version() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _orm_version()

    version = _label_set(api_client).get_version(VERSION_ID)

    assert api_client.get.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions/{VERSION_ID}",)
    assert version.id == VERSION_ID
    assert version.status == LabelSetVersionStatus.READY
    assert version.label_count == 3
    assert version.capture_started_at == NOW and version.capture_finished_at == NOW
    assert version.sources == [
        CapturedSource(
            project_id=PROJECT_ID,
            branch_name="preds/model-7",
            ontology_id=ONTOLOGY_ID,
            ontology_version_id=ONTOLOGY_VERSION_ID,
        )
    ]


def test_version_job_parses_each_state_by_its_status() -> None:
    assert VersionJobResponse.model_validate({"status": "pending"}).root == LabelSetJobPending()
    assert VersionJobResponse.model_validate({"status": "done", "versionUuid": str(VERSION_ID)}).root == (
        VersionJobDone(version_id=VERSION_ID)
    )
    assert VersionJobResponse.model_validate({"status": "failed", "error": "boom"}).root == (
        VersionJobFailed(error="boom")
    )
    # A done state must name its version; the platform never sends one without.
    with pytest.raises(ValidationError):
        VersionJobResponse.model_validate({"status": "done"})


def test_get_version_job_returns_an_unknown_status_without_waiting_on_it(monkeypatch: pytest.MonkeyPatch) -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = VersionJobResponse.model_validate({"status": "cancelled"})
    monkeypatch.setattr("encord.label_set.time.sleep", lambda _: None)

    job = _label_set(api_client).get_version_job(JOB_ID, timeout_seconds=600)

    assert job == LabelSetJobUnknown(status=LabelSetJobStatus.UNKNOWN)
    assert api_client.get.call_count == 1


def test_list_members_pages_under_the_version() -> None:
    api_client = Mock(spec=ApiClient)
    member = LabelSetVersionMember.from_dict(
        {"labelUuid": str(DATA_ID), "labelVersion": 2, "backingItemUuid": str(ITEM_ID), "dataTitle": "video 1"}
    )
    api_client.get_paged_iterator.return_value = iter([member])

    members = list(_version(api_client).list_members(page_size=50))

    assert api_client.get_paged_iterator.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions/{VERSION_ID}/members",)
    assert api_client.get_paged_iterator.call_args.kwargs["params"].to_dict() == {"pageSize": 50}
    assert members == [member]
    assert members[0].backing_item_id == ITEM_ID


def test_get_ontology_parses_the_frozen_definition() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = VersionOntology(
        editor={
            "objects": [
                {
                    "id": "1",
                    "name": "Car",
                    "color": "#ff0000",
                    "shape": "bounding_box",
                    "featureNodeHash": "aaaaaaaa",
                    "attributes": [],
                }
            ],
            "classifications": [],
        },
    )

    structure = _version(api_client).get_ontology()

    assert api_client.get.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions/{VERSION_ID}/ontology",)
    assert [obj.name for obj in structure.objects] == ["Car"]


def test_create_export_job_posts_the_format_without_retries() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.post.return_value = LabelSetJob(job_id=JOB_ID)

    job_id = _version(api_client).create_export_job(ExportFormat.COCO)

    assert job_id == JOB_ID
    assert api_client.post.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions/{VERSION_ID}/exports",)
    assert api_client.post.call_args.kwargs["payload"].to_dict() == {"format": "coco"}
    assert api_client.post.call_args.kwargs["allow_retries"] is False


def test_get_export_job_waits_and_returns_the_signed_url(monkeypatch: pytest.MonkeyPatch) -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.side_effect = [
        VersionExportJobResponse(LabelSetJobPending()),
        VersionExportJobResponse(VersionExportJobDone(signed_url="https://signed/export.zip")),
    ]
    monkeypatch.setattr("encord.label_set.time.sleep", lambda _: None)

    job = _version(api_client).get_export_job(JOB_ID, timeout_seconds=600)

    assert api_client.get.call_args.args == (f"label-sets/{LABEL_SET_ID}/versions/{VERSION_ID}/exports/jobs/{JOB_ID}",)
    assert job == VersionExportJobDone(signed_url="https://signed/export.zip")


def test_get_export_job_returns_the_failure() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = VersionExportJobResponse(VersionExportJobFailed())

    assert _version(api_client).get_export_job(JOB_ID) == VersionExportJobFailed()


def test_enums_parse_values_added_after_this_sdk_version() -> None:
    label_set = OrmLabelSet.from_dict({**_label_set_json(), "origin": "agent"})
    version = OrmLabelSetVersion.from_dict({**_orm_version().to_dict(), "status": "archived"})

    assert label_set.origin == LabelSetOrigin.UNKNOWN
    assert version.status == LabelSetVersionStatus.UNKNOWN


@pytest.mark.parametrize(
    "stored",
    [
        {"tag": "SELECTIVE", "dataUuids": [str(DATA_ID)]},
        {"tag": "FILTERED", "dataTitleSearch": "cat", "filterGraphNodeUuid": [], "filterLabelingStatus": None},
        {"tag": "FILTERED", "dataTitleSearch": "", "filterGraphNodeUuid": [], "filterLabelingStatus": "labeled"},
        {"tag": "SAVED_FILTER", "filterPresetUuid": str(DATA_ID)},
    ],
    ids=["data units", "title filter", "status filter", "shape added later"],
)
def test_a_selection_the_sdk_cannot_set_parses_as_unknown(stored: Dict[str, Any]) -> None:
    label_set = _orm_label_set(stored)

    assert label_set.name == "Model 7"
    source = label_set.sources[0]
    assert isinstance(source, StoredProjectSource)
    selection = source.label_selection
    assert isinstance(selection, UnknownSelection)
    assert selection.tag == stored["tag"]
    assert selection.to_dict(exclude_none=False) == stored


def test_a_source_kind_added_after_this_sdk_version_parses_as_unknown() -> None:
    later = {"tag": "DATASET", "datasetUuid": str(DATA_ID)}

    label_set = OrmLabelSet.from_dict({**_label_set_json(), "sources": [later]})
    version = OrmLabelSetVersion.from_dict({**_orm_version().to_dict(), "sources": [later]})

    assert label_set.name == "Model 7"
    assert version.version_number == 1
    for source in (label_set.sources[0], version.sources[0]):
        assert isinstance(source, UnknownSource)
        assert source.to_dict() == later


def test_a_project_source_with_a_malformed_body_fails_to_parse() -> None:
    # A known tag missing a required field is a platform fault and must not pass as an unknown kind.
    with pytest.raises(EncordException):
        OrmLabelSet.from_dict({**_label_set_json(), "sources": [{"tag": "PROJECT", "branchName": "main"}]})


def test_a_stage_selection_with_a_malformed_body_fails_to_parse() -> None:
    # A stage selection missing its stages is a platform fault and must not pass as a selection the SDK cannot set.
    with pytest.raises(EncordException):
        _orm_label_set({"tag": "FILTERED", "dataTitleSearch": "", "filterLabelingStatus": None})


def test_the_all_selection_parses_as_its_own_shape() -> None:
    source = _orm_label_set({"tag": "ALL"}).sources[0]

    assert isinstance(source, StoredProjectSource)
    assert source.label_selection == AllSelection()
    assert not isinstance(source.label_selection, UnknownSelection)
