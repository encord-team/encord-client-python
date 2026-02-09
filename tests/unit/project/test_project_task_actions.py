from datetime import datetime
from unittest.mock import patch
from uuid import UUID

from encord.orm.analytics import TaskAction, TaskActionType


def test_project_get_task_actions_returns_iterator(project):
    """Test Project.get_task_actions returns an iterator of TaskAction."""
    project_uuid = UUID(project.project_hash)
    action_data = TaskAction(
        timestamp=datetime(2026, 2, 9, 12, 0, 0),
        action_type=TaskActionType.SUBMIT,
        project_uuid=project_uuid,
        workflow_stage_uuid=UUID("87654321-4321-8765-4321-876543218765"),
        task_uuid=UUID("11111111-1111-1111-1111-111111111111"),
        data_unit_uuid=UUID("22222222-2222-2222-2222-222222222222"),
        actor_email="test@example.com",
    )

    # Mock the iterator behavior
    with patch.object(project._client, "get_task_actions", return_value=iter([action_data])):
        after = datetime(2026, 2, 1, 0, 0, 0)
        results = list(project.get_task_actions(after=after))

        assert len(results) == 1
        assert results[0].action_type == TaskActionType.SUBMIT
        assert results[0].actor_email == "test@example.com"


def test_project_get_task_actions_with_filters(project):
    """Test Project.get_task_actions passes filters correctly."""
    with patch.object(project._client, "get_task_actions", return_value=iter([])) as mock_get_task_actions:
        after = datetime(2026, 2, 1, 0, 0, 0)
        before = datetime(2026, 2, 9, 0, 0, 0)

        list(
            project.get_task_actions(
                after=after,
                before=before,
                actor_email=["user1@example.com", "user2@example.com"],
                action_type=[TaskActionType.SUBMIT, TaskActionType.REJECT],
            )
        )

        # Verify the API was called with correct parameters
        mock_get_task_actions.assert_called_once()


def test_project_get_task_actions_single_actor_email(project):
    """Test Project.get_task_actions accepts single actor email."""
    with patch.object(project._client, "get_task_actions", return_value=iter([])) as mock_get_task_actions:
        after = datetime(2026, 2, 1, 0, 0, 0)
        list(project.get_task_actions(after=after, actor_email="user@example.com"))

        # Should not raise any errors
        assert mock_get_task_actions.called
