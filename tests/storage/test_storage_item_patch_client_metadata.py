import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple, cast
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
import requests

import encord.orm.storage as orm_storage
from encord.exceptions import (
    AuthorisationError,
    ClientMetadataPatchPartiallyStartedError,
    ClientMetadataPatchTimeoutError,
    ClientMetadataPatchWaitError,
    RateLimitExceededError,
    UnknownException,
)
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.base_dto import RootModelDTO
from encord.storage import ClientMetadataPatchJobsByUrl, StorageItem
from encord.user_client import EncordUserClient

ITEM_UUID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_ITEM_UUID = UUID("00000000-0000-0000-0000-000000000002")
JOB_UUID = UUID("00000000-0000-0000-0000-00000000000a")


def _item(api_client: Any, client_metadata: Optional[str] = None, item_uuid: UUID = ITEM_UUID) -> StorageItem:
    orm_item = cast(
        orm_storage.StorageItem, SimpleNamespace(uuid=item_uuid, client_metadata=client_metadata, signed_url=None)
    )
    return StorageItem(api_client, orm_item)


def test_storage_item_patch_client_metadata_sends_merge_patch_and_keeps_merged_result() -> None:
    api_client = Mock()
    api_client.patch.return_value = RootModelDTO[Dict[str, Any]]({"keep": 1, "camera": {"fps": 60, "iso": 100}})
    item = _item(api_client, client_metadata=json.dumps({"keep": 1, "draft": True, "camera": {"iso": 100}}))
    assert item.client_metadata is not None  # parse and cache the old metadata

    item.patch_client_metadata({"draft": None, "camera": {"fps": 60}})

    api_client.patch.assert_called_once()
    call = api_client.patch.call_args
    assert call.args == (f"storage/items/{ITEM_UUID}/client-metadata",)
    assert call.kwargs["content_type"] == "application/merge-patch+json"
    assert call.kwargs["result_type"] is RootModelDTO[Dict[str, Any]]
    assert ApiClient._serialise_payload(api_client, call.kwargs["payload"]) == {"draft": None, "camera": {"fps": 60}}
    expected = {"keep": 1, "camera": {"fps": 60, "iso": 100}}
    assert item.client_metadata == expected
    assert json.loads(item._orm_item.client_metadata) == expected


def test_storage_item_refetch_after_patch_client_metadata_shows_server_metadata() -> None:
    api_client = Mock()
    api_client.patch.return_value = RootModelDTO[Dict[str, Any]]({"x": 1})
    item = _item(api_client, client_metadata=json.dumps({}))
    item.patch_client_metadata({"x": 1})
    assert item.client_metadata == {"x": 1}

    # Another client patched key `y` in the meantime.
    api_client.get.return_value = SimpleNamespace(uuid=ITEM_UUID, client_metadata=json.dumps({"x": 1, "y": 2}))
    item.refetch_data()

    assert item.client_metadata == {"x": 1, "y": 2}


@pytest.mark.parametrize(
    ("content_type", "expected_header"),
    [(None, "application/json"), ("application/merge-patch+json", "application/merge-patch+json")],
)
def test_api_client_patch_sends_json_body_with_requested_content_type(
    content_type: Optional[str], expected_header: str
) -> None:
    api_client = ApiClient.__new__(ApiClient)
    merge_patch: Dict[str, Any] = {"a": None, "b": {"c": None, "d": [1]}}

    with (
        patch.object(ApiClient, "_build_url", return_value="https://api.encord.com/v2/public/p"),
        patch.object(ApiClient, "_request") as request,
    ):
        api_client.patch(
            "p",
            params=None,
            payload=RootModelDTO[Dict[str, Any]](merge_patch),  # type: ignore[arg-type]
            result_type=None,
            content_type=content_type,
        )

    sent = request.call_args.args[0]
    assert sent.headers["Content-Type"] == expected_header
    assert json.loads(sent.body) == merge_patch


def _user_client(api_client: Mock) -> EncordUserClient:
    user_client = EncordUserClient.__new__(EncordUserClient)
    user_client._api_client = api_client
    return user_client


def _done(*failed: UUID) -> orm_storage.ClientMetadataPatchJobResult:
    return orm_storage.ClientMetadataPatchJobResult(
        status=orm_storage.ClientMetadataPatchJobStatus.DONE,
        failures=[
            orm_storage.ClientMetadataPatchResult(
                item_uuid=item_uuid, status=orm_storage.ClientMetadataPatchStatus.FAILED, error="Retry."
            )
            for item_uuid in failed
        ],
    )


def _pending() -> orm_storage.ClientMetadataPatchJobResult:
    return orm_storage.ClientMetadataPatchJobResult(
        status=orm_storage.ClientMetadataPatchJobStatus.PENDING, failures=[]
    )


def _start_jobs(api_client: Mock, monkeypatch: pytest.MonkeyPatch, count: int) -> List[UUID]:
    """Make each item its own job, as the API client returns these job UUIDs."""
    monkeypatch.setattr("encord.storage.STORAGE_BUNDLE_CREATE_LIMIT", 1)
    job_uuids = [UUID(int=100 + i) for i in range(count)]
    api_client.post.side_effect = [
        orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=job_uuid) for job_uuid in job_uuids
    ]
    return job_uuids


def test_start_client_metadata_patch_jobs_returns_the_items_each_job_patches_without_waiting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage.STORAGE_BUNDLE_CREATE_LIMIT", 2)
    api_client = Mock(spec=ApiClient)
    job_uuids = [UUID(int=100 + i) for i in range(3)]
    api_client.post.side_effect = [
        orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=job_uuid) for job_uuid in job_uuids
    ]
    item_uuids = [UUID(int=i) for i in range(1, 6)]

    jobs = _user_client(api_client).start_client_metadata_patch_jobs({u: {"a": 1} for u in item_uuids})

    assert jobs.item_uuids_by_job_uuid == {
        job_uuids[0]: item_uuids[:2],
        job_uuids[1]: item_uuids[2:4],
        job_uuids[2]: item_uuids[4:],
    }
    api_client.get.assert_not_called()
    sent = [[p.item_uuid for p in call.kwargs["payload"].patches] for call in api_client.post.call_args_list]
    assert sent == [item_uuids[:2], item_uuids[2:4], item_uuids[4:]]
    assert all(call.kwargs["allow_retries"] is False for call in api_client.post.call_args_list)


def test_patch_storage_items_client_metadata_waits_for_every_job_and_returns_all_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_client = Mock(spec=ApiClient)
    _start_jobs(api_client, monkeypatch, 3)
    api_client.get.side_effect = [_pending(), _done(UUID(int=1)), _done(), _done(UUID(int=3))]

    with patch("encord.storage.time.sleep") as sleep:
        failures = _user_client(api_client).patch_storage_items_client_metadata(
            {UUID(int=i): {"a": 1} for i in range(1, 4)}
        )

    assert [(failure.item_uuid, failure.error) for failure in failures] == [
        (UUID(int=1), "Retry."),
        (UUID(int=3), "Retry."),
    ]
    sleep.assert_called_once_with(1.0)  # polled the first job again while it was pending


def test_patch_storage_items_client_metadata_reports_every_item_of_a_failed_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage.STORAGE_BUNDLE_CREATE_LIMIT", 2)
    api_client = Mock(spec=ApiClient)
    api_client.post.side_effect = [orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=JOB_UUID)]
    api_client.get.return_value = orm_storage.ClientMetadataPatchJobResult(
        status=orm_storage.ClientMetadataPatchJobStatus.FAILED, failures=[]
    )

    failures = _user_client(api_client).patch_storage_items_client_metadata({ITEM_UUID: {"a": 1}, OTHER_ITEM_UUID: {}})

    assert [failure.item_uuid for failure in failures] == [ITEM_UUID, OTHER_ITEM_UUID]
    assert all(failure.status == orm_storage.ClientMetadataPatchStatus.FAILED for failure in failures)
    assert all(failure.error is not None and "may have been applied in part" in failure.error for failure in failures)


def test_patch_storage_items_client_metadata_waits_once_for_all_jobs_and_raises_with_those_still_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_client = Mock(spec=ApiClient)
    first_job, second_job, third_job = _start_jobs(api_client, monkeypatch, 3)
    clock = [0.0]
    # The first job finishes at t=50 with a failure, the second never does, and the third is already done.
    api_client.get.side_effect = lambda path, **_: (
        (_done(UUID(int=1)) if clock[0] >= 50 else _pending())
        if str(first_job) in path
        else _pending()
        if str(second_job) in path
        else _done()
    )

    def sleep(seconds: float) -> None:
        clock[0] += seconds

    with (
        patch("encord.storage.time.sleep", side_effect=sleep),
        patch("encord.storage.time.monotonic", side_effect=lambda: clock[0]),
        pytest.raises(ClientMetadataPatchTimeoutError) as raised,
    ):
        _user_client(api_client).patch_storage_items_client_metadata(
            {UUID(int=i): {"a": 1} for i in range(1, 4)}, timeout_seconds=60
        )

    # One 60 s deadline for all the jobs, not 60 s for each, and the job past it is still checked once.
    assert clock[0] <= 60
    assert raised.value.pending_job_uuids == [second_job]
    assert [failure.item_uuid for failure in raised.value.failures] == [UUID(int=1)]
    assert any(str(third_job) in call.args[0] for call in api_client.get.call_args_list)
    assert raised.value.started.item_uuids_by_job_uuid == {
        first_job: [UUID(int=1)],
        second_job: [UUID(int=2)],
        third_job: [UUID(int=3)],
    }


def test_patch_storage_items_client_metadata_raises_with_the_unchecked_jobs_when_a_check_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_client = Mock(spec=ApiClient)
    first_job, second_job, third_job = _start_jobs(api_client, monkeypatch, 3)
    error = UnknownException("An unknown error occurred.")
    api_client.get.side_effect = [_done(UUID(int=1)), error]

    with pytest.raises(ClientMetadataPatchWaitError) as raised:
        _user_client(api_client).patch_storage_items_client_metadata({UUID(int=i): {"a": 1} for i in range(1, 4)})

    assert raised.value.pending_job_uuids == [second_job, third_job]
    assert [failure.item_uuid for failure in raised.value.failures] == [UUID(int=1)]
    assert raised.value.__cause__ is error
    assert first_job not in raised.value.pending_job_uuids
    assert list(raised.value.started.item_uuids_by_job_uuid) == [first_job, second_job, third_job]


def test_patch_storage_items_client_metadata_does_not_wrap_a_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_client = Mock(spec=ApiClient)
    _start_jobs(api_client, monkeypatch, 1)
    api_client.get.side_effect = KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _user_client(api_client).patch_storage_items_client_metadata({ITEM_UUID: {"a": 1}})


def test_get_client_metadata_patch_job_gets_the_job() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.get.return_value = _done()

    assert _user_client(api_client).get_client_metadata_patch_job(JOB_UUID) == _done()
    assert api_client.get.call_args.args == (f"storage/items/client-metadata/patch-jobs/{JOB_UUID}",)


def test_start_client_metadata_patch_jobs_splits_jobs_to_stay_under_the_payload_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage._CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES", 400)
    api_client = Mock(spec=ApiClient)
    api_client.post.side_effect = [
        orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=UUID(int=100 + i)) for i in range(2)
    ]
    item_uuids = [UUID(int=i) for i in range(1, 5)]

    jobs = _user_client(api_client).start_client_metadata_patch_jobs({u: {"text": "x" * 60} for u in item_uuids})

    assert list(jobs.item_uuids_by_job_uuid.values()) == [item_uuids[:2], item_uuids[2:]]
    for call in api_client.post.call_args_list:
        body = (
            requests.Request(
                "POST", "https://api.encord.com", json=ApiClient._serialise_payload(api_client, call.kwargs["payload"])
            )
            .prepare()
            .body
        )
        assert body is not None and len(body) <= 400


def test_start_client_metadata_patch_jobs_rejects_a_patch_over_the_payload_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage._CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES", 100)
    api_client = Mock(spec=ApiClient)

    with pytest.raises(ValueError, match=str(ITEM_UUID)):
        _user_client(api_client).start_client_metadata_patch_jobs({ITEM_UUID: {"text": "x" * 100}})

    api_client.post.assert_not_called()


def _start_jobs_then_fail(api_client: Mock, monkeypatch: pytest.MonkeyPatch, started: int, error: Exception) -> None:
    """Each item is its own job; the first ``started`` jobs start, then the next one raises ``error``."""
    monkeypatch.setattr("encord.storage.STORAGE_BUNDLE_CREATE_LIMIT", 1)
    api_client.post.side_effect = [
        *(orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=UUID(int=100 + i)) for i in range(started)),
        error,
    ]


@pytest.mark.parametrize(
    "error", [AuthorisationError("You cannot edit an item"), RateLimitExceededError(retry_after=1)]
)
def test_start_client_metadata_patch_jobs_reports_the_jobs_started_before_one_could_not_be(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    api_client = Mock(spec=ApiClient)
    _start_jobs_then_fail(api_client, monkeypatch, started=1, error=error)
    item_uuids = [UUID(int=i) for i in range(1, 4)]

    with pytest.raises(ClientMetadataPatchPartiallyStartedError) as raised:
        _user_client(api_client).start_client_metadata_patch_jobs({u: {"a": 1} for u in item_uuids})

    assert raised.value.started.item_uuids_by_job_uuid == {UUID(int=100): [item_uuids[0]]}
    assert raised.value.not_started_item_uuids == item_uuids[1:]
    assert raised.value.__cause__ is error
    assert api_client.post.call_count == 2  # the third job is never sent


def test_start_client_metadata_patch_jobs_raises_the_first_jobs_error_as_is() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.post.side_effect = AuthorisationError("You cannot edit an item")

    with pytest.raises(AuthorisationError):
        _user_client(api_client).start_client_metadata_patch_jobs({ITEM_UUID: {"a": 1}})


def test_patch_storage_items_client_metadata_raises_a_partial_start_without_waiting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_client = Mock(spec=ApiClient)
    _start_jobs_then_fail(api_client, monkeypatch, started=1, error=AuthorisationError("You cannot edit an item"))

    with pytest.raises(ClientMetadataPatchPartiallyStartedError) as raised:
        _user_client(api_client).patch_storage_items_client_metadata({ITEM_UUID: {"a": 1}, OTHER_ITEM_UUID: {"a": 1}})

    assert raised.value.not_started_item_uuids == [OTHER_ITEM_UUID]
    api_client.get.assert_not_called()


def test_start_client_metadata_patch_jobs_rejects_a_patch_over_the_payload_limit_before_starting_any_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage.STORAGE_BUNDLE_CREATE_LIMIT", 1)
    monkeypatch.setattr("encord.storage._CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES", 100)
    api_client = Mock(spec=ApiClient)

    # The too-large patch would be in the second job.
    with pytest.raises(ValueError, match=str(OTHER_ITEM_UUID)):
        _user_client(api_client).start_client_metadata_patch_jobs(
            {ITEM_UUID: {"a": 1}, OTHER_ITEM_UUID: {"text": "x" * 100}}
        )

    api_client.post.assert_not_called()


def test_client_metadata_patch_job_result_parses_values_added_after_this_sdk_version() -> None:
    job = orm_storage.ClientMetadataPatchJobResult.from_dict(
        {"status": "cancelled", "failures": [{"itemUuid": str(ITEM_UUID), "status": "skipped", "error": None}]}
    )

    assert job.status == orm_storage.ClientMetadataPatchJobStatus.UNKNOWN
    assert job.failures[0].status == orm_storage.ClientMetadataPatchStatus.UNKNOWN


def test_patch_storage_items_client_metadata_reports_every_item_of_a_job_with_an_unknown_status() -> None:
    api_client = Mock(spec=ApiClient)
    api_client.post.side_effect = [orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=JOB_UUID)]
    api_client.get.return_value = orm_storage.ClientMetadataPatchJobResult.from_dict(
        {"status": "cancelled", "failures": []}
    )

    failures = _user_client(api_client).patch_storage_items_client_metadata({ITEM_UUID: {"a": 1}})

    assert [(failure.item_uuid, failure.status) for failure in failures] == [
        (ITEM_UUID, orm_storage.ClientMetadataPatchStatus.FAILED)
    ]


def _lookup_pages(*pages: List[Tuple[str, UUID]]) -> List[Page[orm_storage.ItemUrlMatch]]:
    """The lookup's pages, each a list of (object URL, item UUID) matches; every page but the last has a token."""
    return [
        Page[orm_storage.ItemUrlMatch](
            results=[
                orm_storage.ItemUrlMatch(object_url=url, item_uuid=item_uuid, folder_uuid=FOLDER_UUID)
                for url, item_uuid in page
            ],
            next_page_token=f"page-{index + 1}" if index + 1 < len(pages) else None,
        )
        for index, page in enumerate(pages)
    ]


FOLDER_UUID = UUID("00000000-0000-0000-0000-0000000000f0")
URL_A = "gs://bucket/a.jpg"
URL_B = "gs://bucket/b.jpg"


def _by_url_api_client(lookup_pages: List[Page[orm_storage.ItemUrlMatch]], failed: Dict[UUID, str]) -> Mock:
    api_client = Mock(spec=ApiClient)
    sent: List[Any] = []
    pages = list(lookup_pages)

    def post(path: str, *, payload: Any, **_: Any) -> Any:
        if path == "storage/items/lookup-by-url":
            return pages.pop(0)
        sent.extend(payload.patches)
        # Each job gets its own UUID: 101, 102, ... after a single lookup call.
        return orm_storage.CreateClientMetadataPatchJobResponse(
            job_uuid=UUID(int=100 + len(api_client.post.call_args_list) - 1)
        )

    api_client.post.side_effect = post
    api_client.get.side_effect = lambda *_, **__: orm_storage.ClientMetadataPatchJobResult(
        status=orm_storage.ClientMetadataPatchJobStatus.DONE,
        failures=[
            orm_storage.ClientMetadataPatchResult(
                item_uuid=patch.item_uuid,
                status=orm_storage.ClientMetadataPatchStatus.FAILED,
                error=failed[patch.item_uuid],
            )
            for patch in sent
            if patch.item_uuid in failed
        ],
    )
    return api_client


def test_start_client_metadata_patch_jobs_by_url_starts_a_job_patching_every_item_with_each_url() -> None:
    api_client = _by_url_api_client(_lookup_pages([(URL_A, ITEM_UUID), (URL_A, OTHER_ITEM_UUID)]), failed={})

    jobs = _user_client(api_client).start_client_metadata_patch_jobs_by_url(
        {URL_A: {"reviewed": True}, URL_B: {"x": None}}, folders=[FOLDER_UUID]
    )

    assert jobs.item_uuids_by_url == {URL_A: [ITEM_UUID, OTHER_ITEM_UUID], URL_B: []}
    assert jobs.item_uuids_by_job_uuid == {UUID(int=101): [ITEM_UUID, OTHER_ITEM_UUID]}
    api_client.get.assert_not_called()
    lookup_call, job_call = api_client.post.call_args_list
    assert ApiClient._serialise_payload(api_client, lookup_call.kwargs["payload"]) == {
        "objectUrls": [URL_A, URL_B],
        "folderUuids": [str(FOLDER_UUID)],
        "includeCloudSynced": False,
    }
    assert job_call.args == ("storage/items/client-metadata/patch-jobs",)
    assert ApiClient._serialise_payload(api_client, job_call.kwargs["payload"]) == {
        "patches": [
            {"itemUuid": str(ITEM_UUID), "mergePatch": {"reviewed": True}},
            {"itemUuid": str(OTHER_ITEM_UUID), "mergePatch": {"reviewed": True}},
        ]
    }


def test_start_client_metadata_patch_jobs_by_url_splits_jobs_to_stay_under_the_payload_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage._CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES", 200)
    api_client = _by_url_api_client(_lookup_pages([(URL_A, ITEM_UUID), (URL_A, OTHER_ITEM_UUID)]), failed={})

    jobs = _user_client(api_client).start_client_metadata_patch_jobs_by_url({URL_A: {"text": "x" * 60}})

    job_calls = api_client.post.call_args_list[1:]
    assert [[p.item_uuid for p in call.kwargs["payload"].patches] for call in job_calls] == [
        [ITEM_UUID],
        [OTHER_ITEM_UUID],
    ]
    assert jobs.item_uuids_by_job_uuid == {UUID(int=101): [ITEM_UUID], UUID(int=102): [OTHER_ITEM_UUID]}


def test_patch_storage_items_client_metadata_by_url_waits_and_returns_the_patches_not_applied() -> None:
    api_client = _by_url_api_client(
        _lookup_pages([(URL_A, ITEM_UUID), (URL_A, OTHER_ITEM_UUID)]), failed={OTHER_ITEM_UUID: "Retry."}
    )

    result = _user_client(api_client).patch_storage_items_client_metadata_by_url({URL_A: {"a": 1}, URL_B: {"a": 1}})

    assert result.item_uuids_by_url == {URL_A: [ITEM_UUID, OTHER_ITEM_UUID], URL_B: []}
    assert [(failure.item_uuid, failure.error) for failure in result.failures] == [(OTHER_ITEM_UUID, "Retry.")]
    lookup_payload = api_client.post.call_args_list[0].kwargs["payload"]
    assert ApiClient._serialise_payload(api_client, lookup_payload) == {
        "objectUrls": [URL_A, URL_B],
        "includeCloudSynced": False,
    }


def test_start_client_metadata_patch_jobs_by_url_reads_every_page_of_the_lookup() -> None:
    api_client = _by_url_api_client(_lookup_pages([(URL_A, ITEM_UUID)], [(URL_A, OTHER_ITEM_UUID)]), failed={})

    jobs = _user_client(api_client).start_client_metadata_patch_jobs_by_url({URL_A: {"a": 1}, URL_B: {"a": 1}})

    assert jobs.item_uuids_by_url == {URL_A: [ITEM_UUID, OTHER_ITEM_UUID], URL_B: []}
    first_page_call, second_page_call, _job_call = api_client.post.call_args_list
    assert second_page_call.kwargs["payload"] == first_page_call.kwargs["payload"]
    assert (first_page_call.kwargs["params"].page_token, second_page_call.kwargs["params"].page_token) == (
        None,
        "page-1",
    )


def test_start_client_metadata_patch_jobs_by_url_reports_the_items_found_when_a_later_job_could_not_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("encord.storage.STORAGE_BUNDLE_CREATE_LIMIT", 1)
    api_client = Mock(spec=ApiClient)
    (lookup_page,) = _lookup_pages([(URL_A, ITEM_UUID), (URL_A, OTHER_ITEM_UUID)])
    api_client.post.side_effect = [
        lookup_page,
        orm_storage.CreateClientMetadataPatchJobResponse(job_uuid=UUID(int=101)),
        AuthorisationError("You cannot edit an item"),
    ]

    with pytest.raises(ClientMetadataPatchPartiallyStartedError) as raised:
        _user_client(api_client).start_client_metadata_patch_jobs_by_url({URL_A: {"a": 1}})

    started = raised.value.started
    assert isinstance(started, ClientMetadataPatchJobsByUrl)
    assert started.item_uuids_by_url == {URL_A: [ITEM_UUID, OTHER_ITEM_UUID]}
    assert started.item_uuids_by_job_uuid == {UUID(int=101): [ITEM_UUID]}
    assert raised.value.not_started_item_uuids == [OTHER_ITEM_UUID]
    assert isinstance(raised.value.__cause__, AuthorisationError)


def test_patch_storage_items_client_metadata_by_url_reports_the_items_found_when_the_wait_times_out() -> None:
    api_client = _by_url_api_client(_lookup_pages([(URL_A, ITEM_UUID), (URL_A, OTHER_ITEM_UUID)]), failed={})
    api_client.get.side_effect = lambda *_, **__: _pending()

    with pytest.raises(ClientMetadataPatchTimeoutError) as raised:
        _user_client(api_client).patch_storage_items_client_metadata_by_url(
            {URL_A: {"a": 1}, URL_B: {"a": 1}}, timeout_seconds=0
        )

    started = raised.value.started
    assert isinstance(started, ClientMetadataPatchJobsByUrl)
    assert started.item_uuids_by_url == {URL_A: [ITEM_UUID, OTHER_ITEM_UUID], URL_B: []}
    assert started.item_uuids_by_job_uuid == {UUID(int=101): [ITEM_UUID, OTHER_ITEM_UUID]}
    assert raised.value.pending_job_uuids == [UUID(int=101)]


def test_patch_client_metadata_by_url_rejects_empty_folders_before_sending_anything() -> None:
    api_client = Mock(spec=ApiClient)
    user_client = _user_client(api_client)

    with pytest.raises(ValueError, match="folders"):
        user_client.start_client_metadata_patch_jobs_by_url({URL_A: {"a": 1}}, folders=[])
    with pytest.raises(ValueError, match="folders"):
        user_client.patch_storage_items_client_metadata_by_url({URL_A: {"a": 1}}, folders=[])

    api_client.post.assert_not_called()


def test_patch_client_metadata_by_url_rejects_an_empty_url_before_sending_anything() -> None:
    api_client = Mock(spec=ApiClient)
    user_client = _user_client(api_client)

    with pytest.raises(ValueError, match="URL"):
        user_client.start_client_metadata_patch_jobs_by_url({URL_A: {"a": 1}, "": {"a": 1}})
    with pytest.raises(ValueError, match="URL"):
        user_client.patch_storage_items_client_metadata_by_url({"": {"a": 1}})

    api_client.post.assert_not_called()


def test_patch_client_metadata_by_url_takes_folders_and_timeout_only_by_keyword() -> None:
    user_client = _user_client(Mock(spec=ApiClient))
    with pytest.raises(TypeError):
        user_client.patch_storage_items_client_metadata_by_url({URL_A: {"a": 1}}, [FOLDER_UUID])  # type: ignore[misc]
    with pytest.raises(TypeError):
        user_client.start_client_metadata_patch_jobs_by_url({URL_A: {"a": 1}}, [FOLDER_UUID])  # type: ignore[misc]
