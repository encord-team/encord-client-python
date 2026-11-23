from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import List
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from pydantic import ValidationError

from encord import Project
from encord.client import EncordClientProject
from encord.exceptions import AuthorisationError, ResourceNotFoundError, ServiceUnavailableError
from encord.http.constants import RequestsSettings
from encord.ontology import Ontology
from encord.orm import project_copy as dto
from encord.project_copy import (
    AllDatasets,
    ProjectCopyFailedError,
    ProjectCopyFile,
    ProjectCopyLoadError,
    ProjectCopyStatus,
    ProjectCopyTimeoutError,
    ProjectCopyWaitError,
    SelectedDatasets,
    SelectedFiles,
)

JOB_ID = UUID(int=1)
PROJECT_ID = UUID(int=2)
DATASET_ID = UUID(int=3)
DATA_ID = UUID(int=4)


def response(status="done", **kwargs):
    payload = {"status": status, **kwargs}
    if status != "failed":
        payload.setdefault("projectUuid", str(PROJECT_ID))
    return dto.ProjectCopyResultDTO.model_validate(payload)


@dataclass
class Clock:
    now: float = 0
    sleeps: List[float] = field(default_factory=list)

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    fake_time = SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep)
    monkeypatch.setattr("encord.project_copy.time", fake_time)
    return clock


@pytest.fixture
def api(user_client):
    api = MagicMock()
    api.requests_settings = RequestsSettings()
    user_client._api_client = api
    return api


@pytest.fixture
def load_project(monkeypatch):
    loader = MagicMock(return_value=MagicMock(spec=Project))
    monkeypatch.setattr("encord.project._load_project", loader)
    return loader


@pytest.mark.parametrize(
    "data,expected",
    [
        (AllDatasets(), {"type": "allDatasets"}),
        (SelectedDatasets([]), {"type": "datasets", "datasetUuids": []}),
        (
            SelectedDatasets([str(DATASET_ID), DATASET_ID]),
            {"type": "datasets", "datasetUuids": [str(DATASET_ID), str(DATASET_ID)]},
        ),
        (
            SelectedFiles([ProjectCopyFile(str(DATASET_ID), DATA_ID)], dataset_title="Picked"),
            {
                "type": "files",
                "files": [{"datasetUuid": str(DATASET_ID), "dataUuid": str(DATA_ID)}],
                "datasetTitle": "Picked",
            },
        ),
    ],
)
def test_start_serializes_each_selection_without_changing_its_meaning(project, data, expected):
    api = MagicMock()
    api.post.return_value = dto.ProjectCopyStartedDTO(job_uuid=JOB_ID, project_uuid=PROJECT_ID)
    project._api_client = api

    job = project.copy_project_start(data=data, title="Copy", description="", copy_labels=True, copy_collaborators=True)

    assert job.job_id == JOB_ID
    assert job.project_id == PROJECT_ID
    assert api.post.call_args.args == (f"projects/{project.project_hash}/copy-jobs",)
    assert api.post.call_args.kwargs["payload"].to_dict() == {
        "title": "Copy",
        "description": "",
        "data": expected,
        "copyLabels": True,
        "copyCollaborators": True,
    }
    assert api.post.call_args.kwargs["allow_retries"] is False
    api.get.assert_not_called()


def test_start_omits_unspecified_title_and_description(project):
    api = MagicMock()
    api.post.return_value = dto.ProjectCopyStartedDTO(job_uuid=JOB_ID, project_uuid=PROJECT_ID)
    project._api_client = api

    project.copy_project_start(data=AllDatasets())

    assert api.post.call_args.kwargs["payload"].to_dict() == {
        "data": {"type": "allDatasets"},
        "copyLabels": False,
        "copyCollaborators": False,
    }


@pytest.mark.parametrize("selection", [SelectedDatasets(["not-a-uuid"]), object()])
def test_invalid_selection_does_not_submit_a_copy(project, selection):
    api = MagicMock()
    project._api_client = api

    with pytest.raises((ValueError, TypeError)):
        project.copy_project_start(data=selection)

    api.post.assert_not_called()


def test_resuming_a_job_constructs_a_handle_without_a_request(user_client, api):
    job = user_client.get_project_copy_job(str(JOB_ID))

    assert job.job_id == JOB_ID
    assert job.project_id is None
    api.get.assert_not_called()
    api.post.assert_not_called()


@pytest.mark.parametrize(
    "status,kwargs",
    [("pending", {}), ("done", {}), ("failed", {}), ("pending", {"timeout_seconds": 0})],
)
def test_immediate_status_checks_once_and_preserves_job_identity(user_client, api, clock, status, kwargs):
    api.get.return_value = response(status, **({"error": "Copy failed"} if status == "failed" else {}))
    job = user_client.get_project_copy_job(JOB_ID)

    result = job.get_status(**kwargs)

    assert result.job_id == JOB_ID
    assert result.status == ProjectCopyStatus(status)
    assert result.error == ("Copy failed" if status == "failed" else None)
    assert result.project_id == (None if status == "failed" else PROJECT_ID)
    api.get.assert_called_once()
    assert api.get.call_args.args == (f"projects/copy-jobs/{JOB_ID}",)
    assert api.get.call_args.kwargs["params"].timeout_seconds == 0
    assert clock.sleeps == []


def test_server_waits_shrink_to_the_remaining_overall_timeout(user_client, api, clock):
    def pending(*args, **kwargs):
        clock.now += kwargs["params"].timeout_seconds
        return response("pending")

    api.get.side_effect = pending
    job = user_client.get_project_copy_job(JOB_ID)

    result = job.get_status(timeout_seconds=90)

    assert [call.kwargs["params"].timeout_seconds for call in api.get.call_args_list] == [60, 30]
    assert result.status == ProjectCopyStatus.PENDING
    assert result.project_id == PROJECT_ID
    assert clock.now == 90
    assert clock.sleeps == []


def test_early_pending_responses_are_spaced_apart_without_exceeding_the_deadline(user_client, api, clock):
    api.get.return_value = response("pending")
    job = user_client.get_project_copy_job(JOB_ID)

    result = job.get_status(timeout_seconds=3)

    assert result.status == ProjectCopyStatus.PENDING
    assert api.get.call_count == 3
    assert clock.sleeps == [1, 1, 1]
    assert clock.now == 3


def test_a_short_http_read_timeout_limits_the_server_wait(user_client, api, clock):
    api.requests_settings = RequestsSettings(read_timeout=10)
    api.get.return_value = response()

    user_client.get_project_copy_job(JOB_ID).get_status(timeout_seconds=300)

    assert api.get.call_args.kwargs["params"].timeout_seconds == 9


def test_completion_stops_waiting_and_wait_for_project_loads_the_returned_project(
    user_client, api, clock, load_project
):
    api.get.side_effect = [response("pending"), response()]
    expected = load_project.return_value
    job = user_client.get_project_copy_job(JOB_ID)

    project = job.wait_for_project(timeout_seconds=300)

    assert project is expected
    assert api.get.call_count == 2
    load_project.assert_called_once_with(api, user_client.user_config.config, PROJECT_ID)
    assert clock.sleeps == [1]


def test_wait_for_project_gives_up_after_an_hour_by_default(user_client, api, clock, load_project):
    def pending(*args, **kwargs):
        clock.now += kwargs["params"].timeout_seconds
        return response("pending")

    api.get.side_effect = pending

    with pytest.raises(ProjectCopyTimeoutError):
        user_client.get_project_copy_job(JOB_ID).wait_for_project()

    assert clock.now == 60 * 60
    load_project.assert_not_called()


def test_wait_for_project_without_a_timeout_keeps_waiting_until_the_copy_finishes(
    user_client, api, clock, load_project
):
    pending_responses = 100

    def pending_then_done(*args, **kwargs):
        clock.now += kwargs["params"].timeout_seconds
        return response("pending" if api.get.call_count <= pending_responses else "done")

    api.get.side_effect = pending_then_done

    project = user_client.get_project_copy_job(JOB_ID).wait_for_project(timeout_seconds=None)

    assert project is load_project.return_value
    assert {call.kwargs["params"].timeout_seconds for call in api.get.call_args_list} == {60}
    assert api.get.call_count == pending_responses + 1
    assert clock.sleeps == []


@pytest.mark.parametrize("method", ["get_status", "wait_for_project"])
def test_negative_wait_is_rejected_before_any_request(user_client, api, method):
    job = user_client.get_project_copy_job(JOB_ID)

    with pytest.raises(ValueError, match="non-negative"):
        getattr(job, method)(timeout_seconds=-1)

    api.get.assert_not_called()


def test_failed_copy_raises_with_the_backend_message_and_never_loads_a_project(user_client, api, load_project):
    api.get.return_value = response("failed", error="Cannot copy this project")
    job = user_client.get_project_copy_job(JOB_ID)

    with pytest.raises(ProjectCopyFailedError, match="Cannot copy this project") as failure:
        job.wait_for_project(timeout_seconds=0)

    assert failure.value.job_id == JOB_ID
    assert failure.value.error == "Cannot copy this project"
    load_project.assert_not_called()


def test_timeout_retains_the_job_id_and_the_same_handle_can_be_waited_on_again(user_client, api, clock, load_project):
    api.get.side_effect = [response("pending"), response()]
    job = user_client.get_project_copy_job(JOB_ID)

    with pytest.raises(ProjectCopyTimeoutError) as failure:
        job.wait_for_project(timeout_seconds=0)

    assert failure.value.job_id == JOB_ID
    load_project.assert_not_called()
    job.wait_for_project(timeout_seconds=300)
    load_project.assert_called_once_with(api, user_client.user_config.config, PROJECT_ID)
    api.post.assert_not_called()


def test_status_request_failure_reaches_the_caller_unchanged(user_client, api):
    error = AuthorisationError("No access")
    api.get.side_effect = error
    job = user_client.get_project_copy_job(JOB_ID)

    with pytest.raises(AuthorisationError) as failure:
        job.get_status()

    assert failure.value is error


def test_chained_start_and_wait_preserves_job_id_and_can_resume_after_a_request_failure(
    project, user_client, api, clock, load_project
):
    error = ServiceUnavailableError("Unavailable")
    project._api_client = api
    api.post.return_value = dto.ProjectCopyStartedDTO(job_uuid=JOB_ID, project_uuid=PROJECT_ID)
    api.get.side_effect = [response("pending"), error]

    with pytest.raises(ProjectCopyWaitError) as failure:
        project.copy_project_start(data=AllDatasets()).wait_for_project(timeout_seconds=300)

    assert failure.value.job_id == JOB_ID
    assert failure.value.__cause__ is error
    load_project.assert_not_called()

    api.get.side_effect = None
    api.get.return_value = response()
    copied_project = user_client.get_project_copy_job(failure.value.job_id).wait_for_project(timeout_seconds=0)

    assert copied_project is load_project.return_value
    assert api.post.call_count == 1


def test_project_loading_failure_retains_the_successful_copy_project_id(user_client, api, load_project):
    api.get.return_value = response()
    error = ResourceNotFoundError("Project unavailable")
    load_project.side_effect = error
    job = user_client.get_project_copy_job(JOB_ID)

    with pytest.raises(ProjectCopyLoadError) as failure:
        job.wait_for_project(timeout_seconds=0)

    assert failure.value.job_id == JOB_ID
    assert failure.value.project_id == PROJECT_ID
    assert failure.value.__cause__ is error
    api.post.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "pending"},
        {"status": "done"},
        {"status": "failed"},
    ],
)
def test_malformed_results_cannot_be_parsed_as_an_unknown_status(payload):
    with pytest.raises(ValidationError):
        dto.ProjectCopyResultDTO.model_validate(payload)


def test_unfamiliar_status_is_readable_and_retains_its_fields(user_client, api, clock):
    api.get.return_value = response("verifying")

    result = user_client.get_project_copy_job(JOB_ID).get_status(timeout_seconds=300)

    assert result.job_id == JOB_ID
    assert result.status == ProjectCopyStatus.UNKNOWN
    assert result.raw_status == "verifying"
    assert result.project_id == PROJECT_ID
    api.get.assert_called_once()
    assert clock.sleeps == []


def test_unfamiliar_status_never_loads_a_project_or_waits_indefinitely(user_client, api, clock, load_project):
    api.get.return_value = response("verifying")

    with pytest.raises(ProjectCopyWaitError, match=f"{JOB_ID}.*unrecognized status 'verifying'") as failure:
        user_client.get_project_copy_job(JOB_ID).wait_for_project(timeout_seconds=None)

    assert failure.value.job_id == JOB_ID
    load_project.assert_not_called()
    api.get.assert_called_once()
    assert clock.sleeps == []


@pytest.mark.parametrize("origin", ["started_copy", "resumed_copy", "user_client"])
def test_project_loading_uses_the_same_identity_context_and_ontology_for_every_origin(
    project, user_client, ontology, origin
):
    api = MagicMock()
    api.requests_settings = RequestsSettings()
    api.post.return_value = dto.ProjectCopyStartedDTO(job_uuid=JOB_ID, project_uuid=PROJECT_ID)
    api.get.return_value = response()
    project._api_client = api
    user_client._api_client = api
    copied_data = project._project_instance.model_copy(update={"project_hash": PROJECT_ID})

    with (
        patch.object(EncordClientProject, "get_project_v2", return_value=copied_data),
        patch.object(Ontology, "_from_api_payload", return_value=ontology) as parse_ontology,
    ):
        if origin == "started_copy":
            copied_project = project.copy_project_start(data=AllDatasets()).wait_for_project(timeout_seconds=0)
        elif origin == "resumed_copy":
            copied_project = user_client.get_project_copy_job(JOB_ID).wait_for_project(timeout_seconds=0)
        else:
            copied_project = user_client.get_project(PROJECT_ID)

    assert isinstance(copied_project, Project)
    assert copied_project.project_hash == str(PROJECT_ID)
    assert copied_project._client._querier.resource_id == str(PROJECT_ID)
    assert copied_project._client._config is project._client._config
    assert copied_project._api_client is api
    assert copied_project._ontology_internal is ontology
    parse_ontology.assert_called_once_with(api.get.return_value, api)
    assert api.get.call_args.args == (f"ontologies/{copied_data.ontology_hash}",)
