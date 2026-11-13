import pytest

from encord.beta.workflow_v3 import (
    AnnotationTask,
    ManualTask,
    ReviewTask,
    StaleTaskError,
    TaskStatus,
)
from encord.exceptions import (
    EncordException,
    ResourceExistsError,
)
from encord.orm import tasks_v3 as dto
from tests.workflow_v3.helpers import _workflow


@pytest.mark.parametrize("keyword", [False, True], ids=["positional", "keyword"])
@pytest.mark.parametrize(
    "stage_type,task_class",
    [
        ("ANNOTATION", AnnotationTask),
        ("REVIEW", ReviewTask),
    ],
)
def test_manual_assignment_returns_none_without_refreshing_or_mutating_the_snapshot(
    workflow_v3_payload, task_payload, keyword, stage_type, task_class
) -> None:
    assignee = "alice@example.com"
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["stageType"] = stage_type
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    original = workflow.get_task(id=task_payload["id"])
    assert isinstance(original, ManualTask)
    assert type(original) is task_class
    assignment = original.assignment
    api.reset_mock()
    api.post.return_value = None

    assigned = original.assign(assignee=assignee) if keyword else original.assign(assignee)

    assert assigned is None
    assert original.assignment is assignment
    api.get.assert_not_called()
    assert api.post.call_args.args[0].endswith(f"tasks/{original.id}/assign")
    assert api.post.call_args.kwargs["payload"].assignee == assignee
    assert api.post.call_args.kwargs["allow_retries"] is False
    assert api.post.call_args.kwargs["result_type"] is None
    assert api.post.call_args.kwargs["allow_none"] is True


@pytest.mark.parametrize("payload", [{}, {"assignee": None}])
def test_assignment_payload_requires_an_email(payload) -> None:
    with pytest.raises(EncordException, match="assignee"):
        dto.AssignTaskPayload.from_dict(payload)


@pytest.mark.parametrize(
    "assignment",
    [
        None,
        {"assignedTo": None, "assignedAt": None},
        {
            "assignedTo": "user-hash",
            "assignedAt": "2026-10-23T10:00:02Z",
        },
    ],
)
def test_release_identifies_only_the_visit_even_for_unassigned_or_historical_snapshots(
    workflow_v3_payload, task_payload, assignment
) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload.update(stageType="ANNOTATION", assignment=assignment, status="done")
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    original = workflow.get_task(id=task_payload["id"])
    assert isinstance(original, AnnotationTask)
    api.reset_mock()
    before = original.assignment

    original.release()

    assert api.post.call_args.args[0].endswith(f"tasks/{original.id}/release")
    assert api.post.call_args.kwargs["payload"] is None
    assert original.assignment is before
    assert original.status is TaskStatus.DONE
    assert api.post.call_args.kwargs["allow_retries"] is False
    assert api.post.call_args.kwargs["result_type"] is None
    api.get.assert_not_called()


@pytest.mark.parametrize("operation,args", [("assign", ("alice@example.com",)), ("release", ())])
def test_manual_actions_report_stale_visits_with_context(workflow_v3_payload, task_payload, operation, args) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["stageType"] = "ANNOTATION"
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)
    task = workflow.get_task(id=task_payload["id"])
    conflict = ResourceExistsError("Opaque error message")
    api.post.side_effect = conflict

    with pytest.raises(StaleTaskError) as error:
        getattr(task, operation)(*args)

    assert error.value.__cause__ is conflict
    assert error.value.context is conflict.context
    assert "Opaque error message" in error.value.message
    assert str(task.id) in error.value.message
    assert str(task._client.project_id) in error.value.message


@pytest.mark.parametrize("stage_type", ["START", "EXTERNAL", "COMPLETE", "FUTURE_STAGE"])
def test_nonmanual_work_has_no_assignment_or_release_methods(workflow_v3_payload, task_payload, stage_type) -> None:
    workflow, api = _workflow(workflow_v3_payload)
    task_payload["stageType"] = stage_type
    api.get.return_value = dto.TaskDTO.from_dict(task_payload)

    task = workflow.get_task(id=task_payload["id"])

    assert not hasattr(task, "assign")
    assert not hasattr(task, "release")
