import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from deepdiff import DeepDiff

from encord.common.time_parser import parse_datetime
from encord.http.querier import Querier, RequestContext
from encord.project import Project
from tests.conftest import ontology, project, user_client

assert project and user_client and ontology  # Need to import all fixtures


def get_mocked_answer(payload: Any) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": 200, "response": payload}
    mock_response.content = json.dumps({"status": 200, "response": payload})
    return mock_response


@patch.object(Querier, "_execute")
def test_get_label_logs_filter_by_datetime(querier_mock: MagicMock, project: Project):
    after_time = parse_datetime("2023-01-01T21:00:00")
    before_time = parse_datetime("2023-01-02T21:00:00")
    querier_mock.return_value = ([], RequestContext())

    _ = project.get_label_logs(after=after_time, before=before_time)

    querier_mock.assert_called_once()

    request = querier_mock.call_args[0][0]
    request_data = json.loads(request.data)

    assert request_data["query_type"] == "labellog"
    assert not DeepDiff(
        request_data["values"]["payload"],
        {
            "start_timestamp": int(after_time.timestamp()),
            "end_timestamp": int(before_time.timestamp()),
            "include_user_email_and_interface_key": True,
        },
        ignore_order=True,
    )


@patch.object(Querier, "_execute")
def test_get_label_logs_filter_by_unix_timestamp(querier_mock: MagicMock, project: Project):
    after_timestamp = 22
    before_timestamp = 33
    querier_mock.return_value = ([], RequestContext())

    _ = project.get_label_logs(from_unix_seconds=after_timestamp, to_unix_seconds=before_timestamp)

    querier_mock.assert_called_once()

    request = querier_mock.call_args[0][0]
    request_data = json.loads(request.data)

    assert request_data["query_type"] == "labellog"
    assert not DeepDiff(
        request_data["values"]["payload"],
        {
            "start_timestamp": after_timestamp,
            "end_timestamp": before_timestamp,
            "include_user_email_and_interface_key": True,
        },
        ignore_order=True,
    )


@patch.object(Querier, "_execute")
def test_get_label_logs_raises_when_both_time_filter_specified(querier_mock: MagicMock, project: Project):
    with pytest.raises(ValueError):
        _ = project.get_label_logs(from_unix_seconds=22, after=datetime.now())

    with pytest.raises(ValueError):
        _ = project.get_label_logs(to_unix_seconds=22, before=datetime.now())

    querier_mock.assert_not_called()
