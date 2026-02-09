from datetime import datetime
from uuid import UUID

import pytest

from encord.analytics.task_actions import TaskAction, TaskActionType


def test_task_action_type_enum_values():
    """Test all TaskActionType enum values exist."""
    assert TaskActionType.ASSIGN.value == "assign"
    assert TaskActionType.APPROVE.value == "approve"
    assert TaskActionType.SUBMIT.value == "submit"
    assert TaskActionType.MOVE.value == "move"
    assert TaskActionType.REJECT.value == "reject"
    assert TaskActionType.RELEASE.value == "release"
    assert TaskActionType.SKIP.value == "skip"


def test_task_action_camel_case_serialization():
    """Test TaskAction serializes with camelCase."""
    now = datetime.now()
    action = TaskAction(
        timestamp=now,
        action_type=TaskActionType.SUBMIT,
        project_uuid=UUID("12345678-1234-5678-1234-567812345678"),
        workflow_stage_uuid=UUID("87654321-4321-8765-4321-876543218765"),
        task_uuid=UUID("11111111-1111-1111-1111-111111111111"),
        data_unit_uuid=UUID("22222222-2222-2222-2222-222222222222"),
        actor_email="test@example.com",
    )

    data = action.model_dump(by_alias=True)
    assert "actionType" in data
    assert "projectUuid" in data
    assert "workflowStageUuid" in data
    assert "taskUuid" in data
    assert "dataUnitUuid" in data
    assert "actorEmail" in data
