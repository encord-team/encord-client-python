from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID

from encord.analytics.task_actions import TaskAction, TaskActionType, _TaskActionsClient


def test_task_actions_client_get_task_actions_single_page():
    """Test _TaskActionsClient.get_task_actions returns iterator of TaskAction."""
    mock_api_client = MagicMock()

    # Mock API response
    action_data = TaskAction(
        timestamp=datetime(2026, 2, 9, 12, 0, 0),
        action_type=TaskActionType.SUBMIT,
        project_uuid=UUID("12345678-1234-5678-1234-567812345678"),
        workflow_stage_uuid=UUID("87654321-4321-8765-4321-876543218765"),
        task_uuid=UUID("11111111-1111-1111-1111-111111111111"),
        data_unit_uuid=UUID("22222222-2222-2222-2222-222222222222"),
        actor_email="test@example.com",
    )

    mock_api_client.get_paged_iterator.return_value = iter([action_data])

    client = _TaskActionsClient(api_client=mock_api_client)
    project_uuid = UUID("12345678-1234-5678-1234-567812345678")
    after = datetime(2026, 2, 1, 0, 0, 0)

    results = list(client.get_task_actions(
        project_uuid=project_uuid,
        after=after,
        before=None,
        actor_email=None,
        action_type=None,
        workflow_stage_uuid=None,
        data_unit_uuid=None,
    ))

    assert len(results) == 1
    assert results[0].action_type == TaskActionType.SUBMIT
    assert results[0].actor_email == "test@example.com"


def test_task_actions_client_normalizes_filters_to_lists():
    """Test _TaskActionsClient normalizes single values to lists."""
    mock_api_client = MagicMock()
    mock_api_client.get_paged_iterator.return_value = iter([])

    client = _TaskActionsClient(api_client=mock_api_client)
    project_uuid = UUID("12345678-1234-5678-1234-567812345678")
    after = datetime(2026, 2, 1, 0, 0, 0)

    # Call with single string email
    list(client.get_task_actions(
        project_uuid=project_uuid,
        after=after,
        before=None,
        actor_email="test@example.com",  # Single string
        action_type=TaskActionType.SUBMIT,  # Single enum
        workflow_stage_uuid=UUID("87654321-4321-8765-4321-876543218765"),  # Single UUID
        data_unit_uuid=None,
    ))

    # Verify that get_paged_iterator was called with lists
    call_kwargs = mock_api_client.get_paged_iterator.call_args[1]
    params = call_kwargs["params"]

    assert isinstance(params.actor_email, list)
    assert params.actor_email == ["test@example.com"]
    assert isinstance(params.action_type, list)
    assert params.action_type == [TaskActionType.SUBMIT]
    assert isinstance(params.workflow_stage_uuid, list)


def test_task_actions_client_uses_current_time_for_before():
    """Test _TaskActionsClient uses current time as before if not provided."""
    mock_api_client = MagicMock()
    mock_api_client.get_paged_iterator.return_value = iter([])

    client = _TaskActionsClient(api_client=mock_api_client)
    project_uuid = UUID("12345678-1234-5678-1234-567812345678")
    after = datetime(2026, 2, 1, 0, 0, 0)

    list(client.get_task_actions(
        project_uuid=project_uuid,
        after=after,
        before=None,  # Not provided
        actor_email=None,
        action_type=None,
        workflow_stage_uuid=None,
        data_unit_uuid=None,
    ))

    call_kwargs = mock_api_client.get_paged_iterator.call_args[1]
    params = call_kwargs["params"]

    # before should be set to approximately now
    assert params.before is not None
    assert isinstance(params.before, datetime)
