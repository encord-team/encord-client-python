import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from typing import Any, Dict, Iterator
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter
from typing_extensions import assert_type

from encord.beta.workflow_v3 import (
    AnnotationStage,
    AnnotationTask,
    DataGroupSubsetTarget,
    DatasetSubsetTarget,
    DatasetTarget,
    DataUnitSliceTarget,
    DataUnitTarget,
    ExternalStage,
    ExternalTask,
    ReviewStage,
    ReviewTask,
    StageType,
    StartStage,
    Task,
    TaskSort,
    TaskStatus,
    UnknownTarget,
    Workflow,
)
from encord.configs import BearerConfig
from encord.exceptions import EncordException
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm import tasks_v3 as dto
from encord.orm.workflow_v3 import WorkflowV3DTO
from tests.workflow_v3.helpers import _workflow


def test_task_iteration_fetches_pages_lazily_without_detail_requests_or_collapsing_visits(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    later_visit = {**deepcopy(task_payload), "id": str(UUID(int=201))}
    api.get.side_effect = [
        Page[dto.TaskDTO].from_dict({"results": [task_payload], "nextPageToken": "opaque"}),
        Page[dto.TaskDTO].from_dict({"results": [later_visit]}),
    ]
    stage = workflow.get_stage(id=UUID(int=4))

    iterator = stage.get_tasks()
    api.get.assert_not_called()
    first = next(iterator)
    assert api.get.call_count == 1
    assert api.get.call_args.kwargs["params"].page_token is None
    second = next(iterator)

    assert api.get.call_count == 2
    assert api.get.call_args.kwargs["params"].page_token == "opaque"
    assert list(iterator) == []
    assert first.id != second.id
    assert first.target.id == second.target.id
    assert isinstance(first.target, DataUnitTarget)
    assert first.target.data_hash == "data-hash"
    assert first.target.dataset_hash == "dataset-hash"
    assert first._client is stage._client
    assert first.target._client is stage._client
    assert first.assignment.assigned_to == "user-hash"
    assert first.status is TaskStatus.ENTERED
    assert isinstance(first, ExternalTask)
    assert first.stage_type is StageType.EXTERNAL
    assert {"residence", "parent_task_id", "predecessor_task_id"}.isdisjoint(vars(first))
    assert {"claimed_by", "claim_expires_at"}.isdisjoint(vars(first.assignment))
    assert "workflow-v3/stages/" in api.get.call_args.args[0]


@pytest.mark.parametrize("task_id", ["", "not-a-uuid", "123"])
def test_singular_reads_reject_malformed_task_ids_with_context_before_making_a_request(
    workflow_v3_payload: Dict[str, Any], task_id: str
) -> None:
    workflow, api = _workflow(workflow_v3_payload)

    with pytest.raises(ValueError, match="Invalid task ID:") as error:
        workflow.get_task(id=task_id)

    assert repr(task_id) in str(error.value)
    assert isinstance(error.value.__cause__, ValueError)
    api.get.assert_not_called()


@pytest.mark.parametrize(
    "target_type,target_class,extra",
    [
        ("data_unit", DataUnitTarget, {"dataId": "data"}),
        ("data_unit_slice", DataUnitSliceTarget, {"dataId": "data", "qualifierName": "slice"}),
        ("dataset", DatasetTarget, {}),
        ("data_group_subset", DataGroupSubsetTarget, {"dataId": "group", "qualifierName": "subset"}),
        ("dataset_subset", DatasetSubsetTarget, {"qualifierName": "subset"}),
        ("future_target", UnknownTarget, {}),
    ],
)
def test_singular_reads_construct_typed_targets_without_requiring_membership(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], target_type, target_class, extra
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["target"].pop("dataId")
    task_payload["target"].update(targetType=target_type, **extra)
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)

    task = workflow.get_task(id=task_payload["id"])

    assert isinstance(task.target, target_class)
    assert task.target.id == UUID(task_payload["target"]["id"])
    assert task.target.project_id == UUID(task_payload["target"]["projectId"])
    assert task.target.dataset_hash == task_payload["target"]["datasetId"]
    assert not hasattr(task.target, "qualifier_keys")
    if target_type in {"dataset", "dataset_subset"}:
        assert not hasattr(task.target, "data_hash")
    if target_type == "future_target":
        assert task.target.raw_target_type == "future_target"
    assert api.get.call_count == 1
    assert api.get.call_args.args[0].endswith(f"tasks/{task.id}")
    with pytest.raises(FrozenInstanceError):
        task.priority = 1
    with pytest.raises(FrozenInstanceError):
        task.target.dataset_hash = "changed"


def test_known_malformed_targets_are_not_downgraded_to_unknown(task_payload: Dict[str, Any]) -> None:
    task_payload["target"].pop("dataId")

    with pytest.raises(EncordException, match="dataId"):
        dto.TaskDTO.from_dict(task_payload)


@pytest.mark.parametrize(
    ("stage_type", "task_class"),
    [
        ("EXTERNAL", ExternalTask),
        ("ANNOTATION", AnnotationTask),
        ("REVIEW", ReviewTask),
        ("START", Task),
        ("PERCENTAGE_ROUTER", Task),
        ("COMPLETE", Task),
    ],
)
def test_task_class_uses_the_recorded_visit_type_when_its_stage_is_absent_from_the_graph(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any], stage_type, task_class
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload.update(stageType=stage_type, stageId=str(UUID(int=999)), status="done")
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)

    task = workflow.get_task(id=task_payload["id"])

    assert type(task) is task_class
    assert task.stage_type is StageType(stage_type)
    assert task.raw_stage_type is None
    assert task.status is TaskStatus.DONE
    assert api.get.call_count == 1


def test_queue_construction_uses_response_stage_type_instead_of_the_loaded_stage_type(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["stageType"] = "ANNOTATION"
    api.get.return_value = Page[dto.TaskDTO].from_dict({"results": [task_payload]})
    external = workflow.get_stage(id=UUID(int=4), type_=ExternalStage)

    [task] = list(external.get_tasks())

    assert type(task) is AnnotationTask
    assert task.stage_type is StageType.ANNOTATION


def test_unfamiliar_stage_types_are_generic_readable_tasks_with_their_original_type(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["stageType"] = "FUTURE_STAGE"
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)

    task = workflow.get_task(id=task_payload["id"])

    assert type(task) is Task
    assert task.stage_type is StageType.UNKNOWN
    assert task.raw_stage_type == "FUTURE_STAGE"
    assert not hasattr(task, "submit")


def test_stage_specific_retrieval_has_precise_static_task_types(workflow_v3_payload: Dict[str, Any]) -> None:
    api = MagicMock(spec=ApiClient)
    workflow = Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload))
    external = workflow.get_stage(id=UUID(int=4), type_=ExternalStage)
    annotation = workflow.get_stage(id=UUID(int=2), type_=AnnotationStage)
    review = workflow.get_stage(id=UUID(int=3), type_=ReviewStage)
    start = workflow.get_stage(id=UUID(int=1), type_=StartStage)

    assert_type(external.get_tasks(), Iterator[ExternalTask])
    assert_type(annotation.get_tasks(), Iterator[AnnotationTask])
    assert_type(review.get_tasks(), Iterator[ReviewTask])
    assert_type(start.get_tasks(), Iterator[Task])

    api.get.assert_not_called()


def test_canceled_task_fields_and_filters_preserve_backend_wire_spelling(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload.update(status="cancelled", cancelledAt="2026-01-02T03:04:05Z")
    record = dto.TaskDTO.from_dict(task_payload)
    api.get.return_value = record

    task = workflow.get_task(id=task_payload["id"])
    params = dto.TasksQueryParams(statuses=[TaskStatus.CANCELED])

    assert task.status is TaskStatus.CANCELED
    assert task.canceled_at is not None
    assert task.canceled_at.isoformat() == "2026-01-02T03:04:05+00:00"
    assert record.to_dict()["cancelledAt"] == "2026-01-02T03:04:05Z"
    assert params.to_dict() == {"statuses": ["cancelled"]}


def test_unfamiliar_status_is_readable_but_cannot_be_sent_as_a_filter(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload.update(status="future_status")
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)

    task = workflow.get_task(id=task_payload["id"])

    assert task.status is TaskStatus.UNKNOWN
    api.reset_mock()
    with pytest.raises(ValueError, match="known TaskStatus"):
        workflow.get_stage(id=UUID(int=4)).get_tasks(statuses=[TaskStatus.UNKNOWN])
    api.get.assert_not_called()


@pytest.mark.parametrize(
    "arguments,error_message",
    [
        ({"statuses": ["entered"]}, "known TaskStatus"),
        ({"statuses": [TaskStatus.UNKNOWN]}, "known TaskStatus"),
        ({"sort": "priority"}, "TaskSort"),
        ({"sort": TaskStatus.ENTERED}, "TaskSort"),
    ],
)
def test_invalid_task_filters_raise_at_call_time_without_making_a_request(
    workflow_v3_payload: Dict[str, Any], arguments: Dict[str, Any], error_message: str
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    stage = workflow.get_stage(id=UUID(int=4))

    with pytest.raises(ValueError, match=error_message):
        stage.get_tasks(**arguments)

    api.get.assert_not_called()


def test_task_filters_are_copied_at_call_time_without_fetching_until_iteration(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = Page[dto.TaskDTO].from_dict({"results": []})
    stage = workflow.get_stage(id=UUID(int=4))
    statuses = [TaskStatus.ENTERED]

    iterator = stage.get_tasks(statuses=statuses, sort=TaskSort.CREATED_AT)
    statuses[:] = [TaskStatus.UNKNOWN]

    api.get.assert_not_called()
    assert list(iterator) == []
    api.get.assert_called_once()
    assert api.get.call_args.kwargs["params"].to_dict() == {"statuses": ["entered"], "sort": "createdAt"}


def test_filters_are_forwarded_and_each_iteration_owns_its_pagination_state(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.return_value = Page[dto.TaskDTO].from_dict({"results": []})
    stage = workflow.get_stage(id=UUID(int=4))

    assert (
        list(
            stage.get_tasks(
                statuses=[TaskStatus.PROCESSING_FAILED, TaskStatus.ENTERING_FAILED],
                sort=TaskSort.CREATED_AT,
            )
        )
        == []
    )
    first_params = api.get.call_args.kwargs["params"]
    assert list(stage.get_tasks()) == []

    assert first_params.to_dict() == {"statuses": ["processingFailed", "enteringFailed"], "sort": "createdAt"}
    assert api.get.call_args.kwargs["params"] is not first_params


def test_pagination_errors_surface_during_iteration_without_replaying_a_read(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    api.get.side_effect = [
        Page[dto.TaskDTO].from_dict({"results": [task_payload], "nextPageToken": "opaque"}),
        RuntimeError("page unavailable"),
    ]
    iterator = workflow.get_stage(id=UUID(int=4)).get_tasks()
    next(iterator)

    with pytest.raises(RuntimeError, match="page unavailable"):
        next(iterator)
    assert api.get.call_count == 2


def test_http_transport_serializes_filters_and_cursor_and_parses_two_pages_and_detail(
    workflow_v3_payload: Dict[str, Any], task_payload: Dict[str, Any]
) -> None:
    api = ApiClient(BearerConfig("test-token", domain="https://sdk-test.invalid"))
    workflow = Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload))
    later_visit = {**deepcopy(task_payload), "id": str(UUID(int=201)), "status": "processingFailed"}
    payloads = iter(
        [
            {"results": [task_payload], "nextPageToken": "opaque+/="},
            {"results": [later_visit], "nextPageToken": None},
            later_visit,
        ]
    )

    def send(request: PreparedRequest, **kwargs: Any) -> Response:
        response = Response()
        response.status_code = 200
        response.request = request
        assert request.url is not None
        response.url = request.url
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(next(payloads)).encode()
        return response

    with patch.object(HTTPAdapter, "send", side_effect=send) as transport:
        iterator = workflow.get_stage(id=UUID(int=4)).get_tasks(
            statuses=[TaskStatus.ENTERED, TaskStatus.PROCESSING_FAILED], sort=TaskSort.CREATED_AT
        )
        transport.assert_not_called()
        visits = list(iterator)
        detail = workflow.get_task(id=visits[1].id)

    requests = [call.args[0] for call in transport.call_args_list]
    first_query = {"statuses": ["entered", "processingFailed"], "sort": ["createdAt"]}
    assert len(requests) == 3
    assert [request.method for request in requests] == ["GET", "GET", "GET"]
    assert parse_qs(urlparse(requests[0].url).query) == first_query
    assert parse_qs(urlparse(requests[1].url).query) == {**first_query, "pageToken": ["opaque+/="]}
    assert urlparse(requests[0].url).path == (
        f"/v2/public/projects/{UUID(int=10000)}/workflow-v3/stages/{UUID(int=4)}/tasks"
    )
    assert urlparse(requests[1].url).path == urlparse(requests[0].url).path
    assert requests[2].url.endswith(f"/workflow-v3/tasks/{UUID(int=201)}")
    assert [visit.id for visit in visits] == [UUID(int=200), UUID(int=201)]
    assert detail == visits[1]
    assert isinstance(detail.target, DataUnitTarget)
    assert detail.target.data_hash == "data-hash"
    assert detail.target.dataset_hash == "dataset-hash"
    assert detail.status is TaskStatus.PROCESSING_FAILED
