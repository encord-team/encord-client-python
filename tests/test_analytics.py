from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID

from encord import Project
from encord.common.time_parser import parse_datetime
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.analytics import (
    CollaboratorTimer,
    CollaboratorTimerParams,
    CollaboratorTimersGroupBy,
    TimeSpent,
)
from encord.orm.workflow import WorkflowStageType
from encord.utilities.project_user import ProjectUserRole
from encord.workflow_v3 import StageType

COLLABORATOR_TIMERS_PATH = "analytics/collaborators/timers"


def _time_spent_payload() -> dict:
    return {
        "periodStartTime": "2026-11-09T10:00:00Z",
        "periodEndTime": "2026-11-09T11:00:00Z",
        "timeSpentSeconds": 60,
        "userEmail": "annotator@example.com",
        "projectUserRole": "ANNOTATOR",
        "dataUuid": "10000000-0000-0000-0000-000000000001",
        "dataTitle": "image.jpg",
        "datasetUuid": "20000000-0000-0000-0000-000000000002",
        "datasetTitle": "Dataset",
        "workflowTaskUuid": "30000000-0000-0000-0000-000000000003",
    }


def test_time_spent_parses_exact_tms3_stage() -> None:
    payload = _time_spent_payload() | {
        "workflowStage": None,
        "workflowV3Stage": {
            "id": "40000000-0000-0000-0000-000000000004",
            "name": "Pre-label",
            "stageType": "EXTERNAL",
        },
    }

    time_spent = TimeSpent.from_dict(payload)

    assert time_spent.workflow_stage is None
    assert time_spent.workflow_v3_stage is not None
    assert time_spent.workflow_v3_stage.id == UUID("40000000-0000-0000-0000-000000000004")
    assert time_spent.workflow_v3_stage.name == "Pre-label"
    assert time_spent.workflow_v3_stage.stage_type is StageType.EXTERNAL


def test_time_spent_keeps_legacy_and_exact_stage_for_compatible_tms3_node() -> None:
    stage_id = "40000000-0000-0000-0000-000000000004"
    payload = _time_spent_payload() | {
        "workflowStage": {"uuid": stage_id, "title": "Annotate", "stageType": "ANNOTATION"},
        "workflowV3Stage": {"id": stage_id, "name": "Annotate", "stageType": "ANNOTATION"},
    }

    time_spent = TimeSpent.from_dict(payload)

    assert time_spent.workflow_stage is not None
    assert time_spent.workflow_stage.stage_type is WorkflowStageType.ANNOTATION
    assert time_spent.workflow_v3_stage is not None
    assert time_spent.workflow_v3_stage.stage_type is StageType.ANNOTATION


def test_time_spent_tolerates_a_new_tms3_stage_type() -> None:
    payload = _time_spent_payload() | {
        "workflowStage": None,
        "workflowV3Stage": {
            "id": "40000000-0000-0000-0000-000000000004",
            "name": "Future work",
            "stageType": "FUTURE_STAGE",
        },
    }

    time_spent = TimeSpent.from_dict(payload)

    assert time_spent.workflow_v3_stage is not None
    assert time_spent.workflow_v3_stage.stage_type is StageType.UNKNOWN


def test_time_spent_from_an_older_server_has_no_exact_stage() -> None:
    stage_id = "40000000-0000-0000-0000-000000000004"
    payload = _time_spent_payload() | {
        "workflowStage": {"uuid": stage_id, "title": "Annotate", "stageType": "ANNOTATION"}
    }

    time_spent = TimeSpent.from_dict(payload)

    assert time_spent.workflow_v3_stage is None
    assert time_spent.period_start_time == datetime(2026, 11, 9, 10, tzinfo=timezone.utc)


def construct_timer(
    user_email="noone@nowhere.com", user_role=ProjectUserRole.ADMIN, data_title="data title 1", time_seconds=22.0
) -> CollaboratorTimer:
    return CollaboratorTimer(
        user_email=user_email,
        user_role=user_role,
        data_title=data_title,
        time_seconds=time_seconds,
    )


@patch.object(ApiClient, "get")
def test_project_collaborator_timers_empty_page(api_client_get: MagicMock, project: Project):
    after_time = parse_datetime("2023-01-01T21:00:00")

    api_client_get.return_value = Page[CollaboratorTimer](results=[])

    timers = list(project.list_collaborator_timers(after=after_time))

    api_client_get.assert_called_once()
    assert [] == timers


@patch.object(ApiClient, "get")
def test_project_collaborator_timers_single_page(api_client_get: MagicMock, project: Project):
    after_time = parse_datetime("2023-01-01T21:00:00")

    return_value = Page[CollaboratorTimer](
        results=[
            construct_timer(data_title="data title 1"),
            construct_timer(data_title="data title 2"),
        ]
    )

    api_client_get.return_value = return_value

    timers = list(project.list_collaborator_timers(after=after_time))
    api_client_get.assert_called_once_with(
        COLLABORATOR_TIMERS_PATH,
        params=CollaboratorTimerParams(
            project_hash=project.project_hash,
            after=after_time,
            before=None,
            group_by=CollaboratorTimersGroupBy.DATA_UNIT,
            page_size=100,
        ),
        result_type=Page[CollaboratorTimer],
        allow_none=False,
    )

    assert return_value.results == timers


@patch.object(ApiClient, "get")
def test_project_collaborator_timers_multi_page(api_client_get: MagicMock, project: Project):
    after_time = parse_datetime("2023-01-01T21:00:00")

    return_value_page_1 = Page[CollaboratorTimer](
        results=[
            construct_timer(data_title="data title 1"),
            construct_timer(data_title="data title 2"),
        ],
        next_page_token="page-token-1",
    )

    return_value_page_2 = Page[CollaboratorTimer](
        results=[
            construct_timer(data_title="data title 3"),
            construct_timer(data_title="data title 4"),
        ]
    )

    api_client_get.side_effect = [return_value_page_1, return_value_page_2]

    timers = list(project.list_collaborator_timers(after=after_time))

    assert api_client_get.call_count == 2
    assert timers == return_value_page_1.results + return_value_page_2.results

    # Check that the get method was called with the correct page token
    second_call_args, second_call_kwargs = api_client_get.call_args_list[1]
    assert second_call_kwargs["params"].page_token == "page-token-1"
