from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from encord import Project
from encord.common.time_parser import parse_datetime
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.analytics import (
    CollaboratorTimer,
    CollaboratorTimerParams,
    CollaboratorTimersGroupBy,
)
from encord.utilities.project_user import ProjectUserRole
from tests.fixtures import ontology, project, user_client

assert user_client and project and ontology

COLLABORATOR_TIMERS_PATH = Path("analytics/collaborators/timers")


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
