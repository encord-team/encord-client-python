import json
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from pydantic import ValidationError

from encord.configs import BearerConfig
from encord.exceptions import EncordException, RateLimitExceededError, ServiceUnavailableError
from encord.http.constants import RequestsSettings
from encord.http.v2.api_client import ApiClient
from encord.project_copy import AllDatasets, ProjectCopyStatus, ProjectCopyWaitError
from tests.http.conftest import MockResponse

JOB_ID = UUID(int=1)
PROJECT_ID = UUID(int=2)


def test_start_and_result_use_the_public_copy_job_endpoints(project, mock_http_client):
    api = ApiClient(BearerConfig("token", domain="https://example.invalid"))
    project._api_client = api
    mock_http_client.respond_with(
        MockResponse(status_code=202, json_body={"jobUuid": str(JOB_ID), "projectUuid": str(PROJECT_ID)})
    )

    job = project.copy_project_start(data=AllDatasets(), title="Copy")
    mock_http_client.respond_with(MockResponse(json_body={"status": "done", "projectUuid": str(PROJECT_ID)}))
    result = job.get_status(timeout_seconds=0)

    start, check = mock_http_client.sent_requests
    assert start.method == "POST"
    assert urlparse(start.url).path == f"/v2/public/projects/{project.project_hash}/copy-jobs"
    assert json.loads(start.body) == {
        "title": "Copy",
        "data": {"type": "allDatasets"},
        "copyLabels": False,
        "copyCollaborators": False,
    }
    assert check.method == "GET"
    assert urlparse(check.url).path == f"/v2/public/projects/copy-jobs/{JOB_ID}"
    assert parse_qs(urlparse(check.url).query) == {"timeoutSeconds": ["0"]}
    assert result.status == ProjectCopyStatus.DONE
    assert result.job_id == JOB_ID
    assert result.project_id == PROJECT_ID


@pytest.mark.parametrize(
    "status_code,error_type",
    [
        (429, RateLimitExceededError),
        (503, ServiceUnavailableError),
    ],
)
def test_start_never_replays_a_sent_copy_request(project, queued_response_server, status_code, error_type):
    server = queued_response_server(
        MockResponse(status_code=status_code),
        MockResponse(status_code=202, json_body={"jobUuid": str(JOB_ID), "projectUuid": str(PROJECT_ID)}),
    )
    project._api_client = ApiClient(
        BearerConfig("token", domain=server.domain, requests_settings=RequestsSettings(max_retries=3, backoff_factor=0))
    )

    with pytest.raises(error_type):
        project.copy_project_start(data=AllDatasets())

    assert server.handled_methods == ["POST"]


def test_result_reads_use_the_clients_transient_failure_retries(user_client, queued_response_server):
    server = queued_response_server(
        MockResponse(status_code=503),
        MockResponse(json_body={"status": "done", "projectUuid": str(PROJECT_ID)}),
    )
    user_client._api_client = ApiClient(
        BearerConfig("token", domain=server.domain, requests_settings=RequestsSettings(max_retries=3, backoff_factor=0))
    )

    result = user_client.get_project_copy_job(JOB_ID).get_status(timeout_seconds=0)

    assert result.status == ProjectCopyStatus.DONE
    assert server.handled_methods == ["GET", "GET"]


def test_malformed_status_response_raises_sdk_error_with_job_context(user_client, mock_http_client):
    user_client._api_client = ApiClient(BearerConfig("token", domain="https://example.invalid"))
    mock_http_client.respond_with(MockResponse(json_body={"status": "done"}))

    with pytest.raises(EncordException, match=f"invalid status response.*{JOB_ID}") as failure:
        user_client.get_project_copy_job(JOB_ID).get_status()

    assert isinstance(failure.value.__cause__, ValidationError)


def test_waiting_on_a_malformed_status_response_preserves_job_id_and_cause(user_client, mock_http_client):
    user_client._api_client = ApiClient(BearerConfig("token", domain="https://example.invalid"))
    mock_http_client.respond_with(MockResponse(json_body={"status": "done"}))

    with pytest.raises(ProjectCopyWaitError) as failure:
        user_client.get_project_copy_job(JOB_ID).wait_for_project(timeout_seconds=300)

    assert failure.value.job_id == JOB_ID
    assert isinstance(failure.value.__cause__, EncordException)
