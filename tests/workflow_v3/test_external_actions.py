import json
from copy import deepcopy
from typing import Any, Dict
from unittest.mock import patch
from uuid import UUID

import pytest
import requests
from requests import Response
from requests.adapters import HTTPAdapter

from encord.beta.workflow_v3 import (
    ExternalStage,
    ExternalTask,
    StaleTaskError,
    Task,
    TaskStatus,
    Workflow,
)
from encord.configs import BearerConfig
from encord.exceptions import AuthorisationError, InvalidArgumentsError, RequestException, ResourceNotFoundError
from encord.http.v2.api_client import ApiClient
from encord.orm import tasks_v3 as dto
from encord.orm.workflow_v3 import WorkflowV3DTO
from tests.workflow_v3.helpers import _workflow


@pytest.mark.parametrize(
    ("pathway_id", "pathway_name"),
    [(None, None), (UUID(int=104), None), (str(UUID(int=104)), None), (None, "Continue")],
)
def test_submit_uses_the_exact_visit_without_retries_or_mutating_its_snapshot(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], pathway_id, pathway_name
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    original = deepcopy(task_payload)
    assert isinstance(task, ExternalTask)

    result = task.submit(pathway_id=pathway_id, pathway_name=pathway_name)

    assert result is None
    api.post.assert_called_once_with(
        f"projects/{UUID(int=10000)}/workflow-v3/tasks/{task.id}/submit",
        params=None,
        payload=dto.SubmitTaskPayload(
            pathway=(
                dto.PathwayById(id=UUID(str(pathway_id)))
                if pathway_id is not None
                else dto.PathwayByName(name=pathway_name)
                if pathway_name is not None
                else None
            )
        ),
        result_type=None,
        allow_none=True,
        allow_retries=False,
    )
    assert api.get.call_count == 1
    assert task.status is TaskStatus.ENTERED
    assert task_payload == original


@pytest.mark.parametrize(("pathway_id", "pathway_name"), [(UUID(int=104), "Continue"), (None, ""), (None, " \t")])
def test_submit_rejects_conflicting_or_blank_selectors_before_sending(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], pathway_id, pathway_name
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    assert isinstance(task, ExternalTask)
    with pytest.raises(ValueError):
        task.submit(pathway_id=pathway_id, pathway_name=pathway_name)

    api.post.assert_not_called()


def test_submit_rejects_an_invalid_uuid_before_sending(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    assert isinstance(task, ExternalTask)

    with pytest.raises(ValueError):
        task.submit(pathway_id="not-a-uuid")

    api.post.assert_not_called()


@pytest.mark.parametrize(
    ("arguments", "expected_payload"),
    [
        ({}, {}),
        ({"pathway_id": str(UUID(int=104))}, {"pathway": {"id": str(UUID(int=104))}}),
        ({"pathway_name": "Continue"}, {"pathway": {"name": "Continue"}}),
        ({"pathway_name": str(UUID(int=104))}, {"pathway": {"name": str(UUID(int=104))}}),
    ],
)
def test_submit_serializes_the_explicit_selector_without_resolving_the_graph(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], arguments, expected_payload
) -> None:
    api = ApiClient(BearerConfig("test-token", domain="https://sdk-test.invalid"))
    workflow = Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload))
    with patch.object(api, "get", return_value=dto.TaskDTO.from_dict(task_payload)):
        task = workflow.get_task(id=task_payload["id"])
    assert isinstance(task, ExternalTask)
    response = Response()
    response.status_code = 204

    with patch.object(HTTPAdapter, "send", return_value=response) as transport:
        task.submit(**arguments)

    transport.assert_called_once()
    request = transport.call_args.args[0]
    assert request.method == "POST"
    assert json.loads(request.body) == expected_payload


@pytest.mark.parametrize(
    "status_code,error_type",
    [(400, InvalidArgumentsError), (403, AuthorisationError), (404, ResourceNotFoundError), (409, StaleTaskError)],
)
@pytest.mark.parametrize("bulk", [False, True])
def test_submission_preserves_distinct_action_errors_and_server_details(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], status_code, error_type, bulk
) -> None:
    api = ApiClient(BearerConfig("test-token", domain="https://sdk-test.invalid"))
    workflow = Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload))
    with patch.object(api, "get", return_value=dto.TaskDTO.from_dict(task_payload)):
        task = workflow.get_task(id=task_payload["id"])
    assert isinstance(task, ExternalTask)
    response = Response()
    response.status_code = status_code
    response._content = b'{"message": "Action refused by the backend"}'
    expected_message = "The requested resource was not found" if status_code == 404 else "Action refused by the backend"

    with patch.object(HTTPAdapter, "send", return_value=response) as transport:
        with pytest.raises(error_type, match=expected_message) as raised:
            if bulk:
                stage = workflow.get_stage(id=task.stage_id, type_=ExternalStage)
                stage.submit_tasks([task])
            else:
                task.submit()

    transport.assert_called_once()
    assert raised.value.context.domain == "https://sdk-test.invalid"
    if status_code == 409 or (status_code == 404 and bulk):
        assert str(task.stage_id if bulk else task.id) in str(raised.value)
        assert str(workflow._client.project_id) in str(raised.value)


def test_submit_propagates_a_timeout_without_replaying_or_marking_the_snapshot_done(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    api = ApiClient(BearerConfig("test-token", domain="https://sdk-test.invalid"))
    workflow = Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload))
    with patch.object(api, "get", return_value=dto.TaskDTO.from_dict(task_payload)):
        task = workflow.get_task(id=task_payload["id"])
    assert isinstance(task, ExternalTask)
    timeout = requests.ReadTimeout("Response lost after sending")

    with patch.object(HTTPAdapter, "send", autospec=True, side_effect=timeout) as transport:
        with pytest.raises(RequestException) as raised:
            task.submit()

    transport.assert_called_once()
    retry_policy = transport.call_args.args[0].max_retries
    assert retry_policy.read == retry_policy.status == retry_policy.other == 0
    assert raised.value.__cause__ is timeout
    assert task.status is TaskStatus.ENTERED


@pytest.mark.parametrize(
    ("stage_type", "can_submit"),
    [
        ("EXTERNAL", True),
        ("ANNOTATION", True),
        ("REVIEW", True),
        ("START", False),
        ("COMPLETE", False),
        ("FUTURE_STAGE", False),
    ],
)
def test_only_supported_task_types_expose_submission(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], stage_type: str, can_submit: bool
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["stageType"] = stage_type
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)

    task = workflow.get_task(id=task_payload["id"])

    assert not hasattr(Task, "submit")
    assert hasattr(task, "submit") is can_submit
    api.post.assert_not_called()


@pytest.mark.parametrize("status", list(TaskStatus))
def test_external_task_actions_remain_available_across_lifecycle_states_without_graph_lookup(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], status: TaskStatus
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload.update(stageId=str(UUID(int=999)), status=status.value)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    assert isinstance(task, ExternalTask)

    task.submit()

    api.post.assert_called_once()
    assert task.status is status


@pytest.mark.parametrize(
    ("arguments", "selector"),
    [
        ({}, None),
        ({"pathway_id": UUID(int=104)}, dto.PathwayById(id=UUID(int=104))),
        ({"pathway_name": "Continue"}, dto.PathwayByName(name="Continue")),
    ],
)
def test_stage_submission_sends_one_shared_pathway_and_returns_none(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], arguments, selector
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    stage = workflow.get_stage(id=task.stage_id, type_=ExternalStage)

    result = stage.submit_tasks([task], **arguments)

    api.post.assert_called_once_with(
        f"projects/{UUID(int=10000)}/workflow-v3/stages/{stage.id}/tasks/submit",
        params=None,
        payload=dto.SubmitTasksPayload(task_ids=[task.id], pathway=selector),
        result_type=None,
        allow_none=True,
        allow_retries=False,
    )
    assert result is None
    assert api.get.call_count == 1
    assert task.status is TaskStatus.ENTERED


@pytest.mark.parametrize("count", [0, 101])
def test_stage_submission_rejects_empty_or_oversized_batches_without_sending(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], count: int
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    stage = workflow.get_stage(id=task.stage_id, type_=ExternalStage)

    with pytest.raises(ValueError, match="between 1 and 100"):
        stage.submit_tasks([task] * count)

    api.post.assert_not_called()


@pytest.mark.parametrize("count", [2, 100])
def test_stage_submission_serializes_every_visit_id_and_accepts_an_empty_success_response(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], count: int
) -> None:
    api = ApiClient(BearerConfig("test-token", domain="https://sdk-test.invalid"))
    workflow = Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload))
    payloads = [{**task_payload, "id": str(UUID(int=1000 + index))} for index in range(count)]
    with patch.object(
        api,
        "get",
        side_effect=[dto.TaskDTO.from_dict(payload) for payload in payloads],
    ):
        tasks = [workflow.get_task(id=payload["id"]) for payload in payloads]
    stage = workflow.get_stage(id=tasks[0].stage_id, type_=ExternalStage)
    response = Response()
    response.status_code = 204

    with patch.object(HTTPAdapter, "send", return_value=response) as transport:
        result = stage.submit_tasks(tasks, pathway_name="Continue")

    transport.assert_called_once()
    request = transport.call_args.args[0]
    assert request.url.endswith(f"/stages/{stage.id}/tasks/submit")
    assert json.loads(request.body) == {
        "taskIds": [str(task.id) for task in tasks],
        "pathway": {"name": "Continue"},
    }
    assert result is None
