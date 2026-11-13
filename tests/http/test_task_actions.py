import json
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

import pytest

from encord.beta.workflow_v3 import (
    AnnotationStage,
    AnnotationTask,
    Assignment,
    DatasetTarget,
    ExternalStage,
    ExternalTask,
    ReviewStage,
    ReviewTask,
    StageType,
    StaleTaskError,
    Task,
    TaskStatus,
    Workflow,
)
from encord.beta.workflow_v3._client import WorkflowClient
from encord.beta.workflow_v3.settings import AnnotationStageSettingsV1, ExternalStageSettingsV1, ReviewStageSettingsV1
from encord.configs import BearerConfig
from encord.exceptions import (
    AuthorisationError,
    InvalidArgumentsError,
    RateLimitExceededError,
    ServiceUnavailableError,
    UnknownException,
)
from encord.http.constants import RequestsSettings
from encord.http.v2.api_client import ApiClient
from encord.orm.workflow_v3 import WorkflowV3DTO
from tests.http.conftest import MockResponse


@pytest.mark.parametrize(
    "status_code,error_type",
    [
        (429, RateLimitExceededError),
        (500, UnknownException),
        (502, ServiceUnavailableError),
        (503, ServiceUnavailableError),
        (504, ServiceUnavailableError),
    ],
)
@pytest.mark.parametrize(
    "operation",
    [
        "external_submit",
        "assign",
        "release",
        "submit",
        "submit_bulk",
        "annotation_bulk",
        "review",
        "review_bulk",
        "release_bulk",
    ],
)
def test_task_actions_never_replay_a_sent_mutation_on_retryable_http_errors(
    queued_response_server, status_code, error_type, operation
) -> None:
    server = queued_response_server(MockResponse(status_code=status_code), MockResponse(status_code=204))
    api = ApiClient(
        BearerConfig(
            "test-token", domain=server.domain, requests_settings=RequestsSettings(max_retries=3, backoff_factor=0)
        )
    )
    client = WorkflowClient(api, UUID(int=1))
    now = datetime.now(timezone.utc)
    task = ExternalTask(
        _client=client,
        id=UUID(int=2),
        stage_id=UUID(int=3),
        stage_type=StageType.EXTERNAL,
        target=DatasetTarget(client, UUID(int=4), client.project_id, "dataset", now, None),
        status=TaskStatus.ENTERED,
        priority=0.5,
        created_at=now,
        entered_at=now,
        processing_at=None,
        done_at=None,
        canceled_at=None,
        assignment=None,
    )

    with pytest.raises(error_type):
        if operation == "external_submit":
            task.submit()
        elif operation == "submit_bulk":
            stage = ExternalStage(client, task.stage_id, "External", ExternalStageSettingsV1(), ())
            stage.submit_tasks([task])
        elif operation == "annotation_bulk":
            stage = AnnotationStage(client, task.stage_id, "Annotate", AnnotationStageSettingsV1(), ())
            stage.submit_tasks([task])
        elif operation in ("review", "review_bulk"):
            manual = ReviewTask(**{**vars(task), "stage_type": StageType.REVIEW})
            if operation == "review":
                manual.submit()
            else:
                stage = ReviewStage(client, task.stage_id, "Review", ReviewStageSettingsV1(), ())
                stage.submit_tasks([manual])
        elif operation == "release_bulk":
            from encord.beta.workflow_v3._assignment_actions import release_tasks

            release_tasks(client, [task.id])
        else:
            manual = AnnotationTask(**{**vars(task), "stage_type": StageType.ANNOTATION})
            if operation == "assign":
                manual.assign("alice@example.com")
            elif operation == "submit":
                manual.submit()
            else:
                manual.release()

    assert server.handled_methods == ["POST"]
    assert task.status is TaskStatus.ENTERED


@pytest.fixture
def manual_task():
    client = WorkflowClient(ApiClient(BearerConfig("token")), UUID(int=1))
    now = datetime(2026, 10, 29, 10, tzinfo=timezone.utc)
    return AnnotationTask(
        _client=client,
        id=UUID(int=2),
        stage_id=UUID(int=3),
        stage_type=StageType.ANNOTATION,
        target=DatasetTarget(client, UUID(int=4), client.project_id, "dataset", now, None),
        status=TaskStatus.ENTERED,
        priority=0.5,
        created_at=now,
        entered_at=now,
        processing_at=None,
        done_at=None,
        canceled_at=None,
        assignment=Assignment("holder", "manager", now),
    )


@pytest.fixture
def review_task(manual_task):
    return ReviewTask(**{**vars(manual_task), "stage_type": StageType.REVIEW})


@pytest.mark.parametrize("bulk", [False, True])
@pytest.mark.parametrize(
    ("arguments", "payload"),
    [
        ({}, {}),
        ({"pathway_id": UUID(int=8)}, {"pathway": {"id": "00000000-0000-0000-0000-000000000008"}}),
        ({"pathway_id": str(UUID(int=8))}, {"pathway": {"id": "00000000-0000-0000-0000-000000000008"}}),
        ({"pathway_name": "Approve", "comment": "Reviewed"}, {"pathway": {"name": "Approve"}, "comment": "Reviewed"}),
    ],
)
def test_review_submission_sends_exact_ids_and_preserves_snapshots(
    mock_http_client, review_task, bulk, arguments, payload
):
    mock_http_client.respond_with(MockResponse(status_code=204))
    before = vars(review_task).copy()
    stage = ReviewStage(review_task._client, review_task.stage_id, "Review", ReviewStageSettingsV1(), ())

    second = replace(review_task, id=UUID(int=9))
    result = stage.submit_tasks([review_task, second], **arguments) if bulk else review_task.submit(**arguments)

    [request] = mock_http_client.sent_requests
    assert request.method == "POST"
    if bulk:
        assert request.url.endswith(f"/stages/{stage.id}/tasks/submit")
        assert json.loads(request.body) == {
            "taskIds": ["00000000-0000-0000-0000-000000000002", "00000000-0000-0000-0000-000000000009"],
            **payload,
        }
    else:
        assert request.url.endswith(f"/tasks/{review_task.id}/submit")
        assert json.loads(request.body) == payload
    assert result is None
    assert vars(review_task) == before
    assert not hasattr(review_task, "approve")
    assert not hasattr(review_task, "reject")


@pytest.mark.parametrize("bulk", [False, True])
@pytest.mark.parametrize(
    ("status", "error_type"), [(400, InvalidArgumentsError), (403, AuthorisationError), (409, StaleTaskError)]
)
def test_review_submission_preserves_backend_errors(mock_http_client, review_task, bulk, status, error_type):
    mock_http_client.respond_with(MockResponse(status_code=status, json_body={"message": "Review refused"}))
    stage = ReviewStage(review_task._client, review_task.stage_id, "Review", ReviewStageSettingsV1(), ())

    with pytest.raises(error_type, match="Review refused"):
        if bulk:
            stage.submit_tasks([review_task])
        else:
            review_task.submit()

    assert len(mock_http_client.sent_requests) == 1


@pytest.mark.parametrize("count", [0, 101])
def test_review_stage_rejects_empty_or_oversized_batches_without_sending(mock_http_client, review_task, count):
    stage = ReviewStage(review_task._client, review_task.stage_id, "Review", ReviewStageSettingsV1(), ())

    with pytest.raises(ValueError, match="between 1 and 100"):
        stage.submit_tasks([review_task] * count)

    assert mock_http_client.sent_requests == []


@pytest.mark.parametrize("assigned", [False, True])
def test_release_sends_no_snapshot_assignment_and_repeated_release_is_not_rejected_locally(
    mock_http_client, manual_task, assigned
):
    mock_http_client.respond_with(MockResponse(status_code=204))
    task = manual_task if assigned else replace(manual_task, assignment=None)

    task.release()
    task.release()

    assert len(mock_http_client.sent_requests) == 2
    for request in mock_http_client.sent_requests:
        assert request.body in (None, b"", "")
        assert request.method == "POST"
        assert request.url.endswith(f"/tasks/{task.id}/release")


@pytest.mark.parametrize(
    ("selector", "wire"),
    [
        ({}, {}),
        ({"pathway_id": UUID(int=8)}, {"pathway": {"id": "00000000-0000-0000-0000-000000000008"}}),
        ({"pathway_name": "Finish", "comment": "Ready"}, {"pathway": {"name": "Finish"}, "comment": "Ready"}),
    ],
)
def test_annotation_stage_submits_exact_visits_with_one_shared_selector_and_comment(
    mock_http_client, manual_task, selector, wire
):
    stage = AnnotationStage(manual_task._client, manual_task.stage_id, "Annotate", AnnotationStageSettingsV1(), ())
    second = replace(manual_task, id=UUID(int=9))
    mock_http_client.respond_with(MockResponse(status_code=204))

    result = stage.submit_tasks([manual_task, second], **selector)

    [request] = mock_http_client.sent_requests
    assert request.url.endswith(f"/stages/{stage.id}/tasks/submit")
    assert json.loads(request.body) == {
        "taskIds": ["00000000-0000-0000-0000-000000000002", "00000000-0000-0000-0000-000000000009"],
        **wire,
    }
    assert result is None
    assert manual_task.status is second.status is TaskStatus.ENTERED


@pytest.mark.parametrize("count", [0, 101])
def test_annotation_stage_rejects_empty_or_oversized_batches_without_sending(mock_http_client, manual_task, count):
    stage = AnnotationStage(manual_task._client, manual_task.stage_id, "Annotate", AnnotationStageSettingsV1(), ())

    with pytest.raises(ValueError, match="between 1 and 100"):
        stage.submit_tasks([manual_task] * count)

    assert mock_http_client.sent_requests == []


@pytest.mark.parametrize(
    ("status", "error_type"), [(400, InvalidArgumentsError), (403, AuthorisationError), (409, StaleTaskError)]
)
def test_annotation_stage_submission_preserves_backend_errors(mock_http_client, manual_task, status, error_type):
    stage = AnnotationStage(manual_task._client, manual_task.stage_id, "Annotate", AnnotationStageSettingsV1(), ())
    mock_http_client.respond_with(MockResponse(status_code=status, json_body={"message": "Batch refused"}))

    with pytest.raises(error_type, match="Batch refused"):
        stage.submit_tasks([manual_task])

    assert len(mock_http_client.sent_requests) == 1


@pytest.mark.parametrize("operation,args", [("assign", ("alice@example.com",)), ("release", ())])
def test_manual_action_conflicts_report_a_stale_visit(mock_http_client, manual_task, operation, args):
    mock_http_client.respond_with(MockResponse(status_code=409, json_body={"message": "Opaque conflict"}))

    with pytest.raises(StaleTaskError) as error:
        getattr(manual_task, operation)(*args)

    assert type(error.value) is StaleTaskError
    assert "Opaque conflict" in error.value.message
    assert len(mock_http_client.sent_requests) == 1


@pytest.mark.parametrize("operation,args", [("assign", ("alice@example.com",)), ("release", ())])
@pytest.mark.parametrize("status_code,error_type", [(400, InvalidArgumentsError), (403, AuthorisationError)])
def test_manual_actions_preserve_invalid_action_and_permission_errors(
    mock_http_client, manual_task, operation, args, status_code, error_type
):
    mock_http_client.respond_with(MockResponse(status_code=status_code, json_body={"message": "Cannot act"}))

    with pytest.raises(error_type):
        getattr(manual_task, operation)(*args)

    assert len(mock_http_client.sent_requests) == 1


def test_assignment_sends_the_required_email_without_extra_requests(mock_http_client, manual_task):
    mock_http_client.respond_with(MockResponse(status_code=204))

    result = manual_task.assign("alice@example.com")

    assert result is None
    [request] = mock_http_client.sent_requests
    assert request.method == "POST"
    assert request.url.endswith(f"/tasks/{manual_task.id}/assign")
    assert json.loads(request.body) == {"assignee": "alice@example.com"}


@pytest.mark.parametrize(
    ("selector", "payload"),
    [
        ({}, {}),
        ({"pathway_id": UUID(int=8)}, {"pathway": {"id": str(UUID(int=8))}}),
        ({"pathway_id": str(UUID(int=8))}, {"pathway": {"id": str(UUID(int=8))}}),
        ({"pathway_name": "Finish", "comment": "Ready"}, {"pathway": {"name": "Finish"}, "comment": "Ready"}),
    ],
)
def test_annotation_submission_sends_one_request_and_leaves_its_snapshot_unchanged(
    mock_http_client, manual_task, selector, payload
):
    mock_http_client.respond_with(MockResponse(status_code=204))
    before = vars(manual_task).copy()

    result = manual_task.submit(**selector)

    assert result is None
    assert vars(manual_task) == before
    [request] = mock_http_client.sent_requests
    assert request.method == "POST"
    assert request.url.endswith(f"/tasks/{manual_task.id}/submit")
    assert json.loads(request.body) == payload


@pytest.mark.parametrize(
    "selector",
    [
        {"pathway_id": UUID(int=8), "pathway_name": "Finish"},
        {"pathway_name": ""},
        {"pathway_name": "   "},
    ],
)
def test_submission_rejects_conflicting_or_blank_selectors_before_sending(mock_http_client, manual_task, selector):
    with pytest.raises(ValueError):
        manual_task.submit(**selector)

    assert mock_http_client.sent_requests == []


def test_submission_rejects_an_invalid_uuid_before_sending(mock_http_client, manual_task):
    with pytest.raises(ValueError):
        manual_task.submit(pathway_id="not-a-uuid")

    assert mock_http_client.sent_requests == []


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (400, InvalidArgumentsError),
        (403, AuthorisationError),
        (409, StaleTaskError),
    ],
)
def test_annotation_submission_preserves_standard_errors_and_stale_visit_identity(
    mock_http_client, manual_task, status, error_type
):
    mock_http_client.respond_with(MockResponse(status_code=status, json_body={"message": "Backend refusal"}))

    with pytest.raises(error_type) as raised:
        manual_task.submit()

    assert "Backend refusal" in raised.value.message
    assert raised.value.context is not None
    assert len(mock_http_client.sent_requests) == 1
    if status == 409:
        assert str(manual_task.id) in raised.value.message
        assert str(manual_task._client.project_id) in raised.value.message


@pytest.mark.parametrize(
    "message",
    [
        "Pathway Rules Failed: COMMENT_REQUIRED: A comment is required.",
        "Pathway Rules Failed: NO_PENDING_LABEL_REVIEWS: Pending reviews. COMMENT_REQUIRED: Comment missing.",
    ],
)
def test_annotation_validation_failures_preserve_the_backend_message(mock_http_client, manual_task, message):
    mock_http_client.respond_with(MockResponse(status_code=400, json_body={"message": message}))

    with pytest.raises(InvalidArgumentsError) as raised:
        manual_task.submit()

    assert type(raised.value) is InvalidArgumentsError
    assert raised.value.message == message
    assert raised.value.context is not None


def test_only_annotation_review_and_external_tasks_expose_submission():
    assert hasattr(AnnotationTask, "submit")
    assert not hasattr(Task, "submit")
    assert hasattr(ReviewTask, "submit")
    assert hasattr(ExternalTask, "submit")


def test_bulk_release_returns_none_and_sends_task_ids_without_changing_snapshots(mock_http_client, manual_task):
    workflow = Workflow(
        manual_task._client.api_client,
        manual_task._client.project_id,
        WorkflowV3DTO(id=UUID(int=8), stages=(), pathways=()),
    )
    mock_http_client.respond_with(MockResponse(status_code=204))
    assignment = manual_task.assignment

    result = workflow.release_tasks([manual_task])

    assert result is None
    assert manual_task.assignment == assignment
    [request] = mock_http_client.sent_requests
    assert request.method == "POST"
    assert request.url.endswith("/workflow-v3/tasks/release")
    assert json.loads(request.body) == {"taskIds": [str(manual_task.id)]}


@pytest.mark.parametrize(
    "status_code,error_type", [(409, StaleTaskError), (403, AuthorisationError), (400, InvalidArgumentsError)]
)
def test_bulk_release_preserves_permission_and_validation_errors_and_maps_stale_tasks(
    mock_http_client, manual_task, status_code, error_type
):
    workflow = Workflow(
        manual_task._client.api_client,
        manual_task._client.project_id,
        WorkflowV3DTO(id=UUID(int=8), stages=(), pathways=()),
    )
    mock_http_client.respond_with(MockResponse(status_code=status_code, json_body={"message": "Cannot release"}))

    with pytest.raises(error_type, match="Cannot release"):
        workflow.release_tasks([manual_task])

    assert len(mock_http_client.sent_requests) == 1
