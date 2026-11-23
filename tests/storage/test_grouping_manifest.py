from typing import Any, Dict, List, Optional
from uuid import UUID

import pytest

import encord.orm.storage as orm_storage
from encord.exceptions import (
    AuthorisationError,
    EncordException,
    GenericServerError,
    ResourceNotFoundError,
    TimeOutError,
)
from encord.orm.group_layout import LayoutSettings
from encord.storage import StorageFolder

FOLDER_UUID = UUID("00000000-0000-0000-0000-0000000000ff")


class _FakeApiClient:
    def __init__(self, response=None, *, post_response=None, get_error: Optional[Exception] = None) -> None:
        self.response = response
        self.post_response = post_response
        self.get_error = get_error
        self.captured: dict = {}

    def post(self, path, *, params, payload, result_type, allow_retries=True):
        self.captured = {
            "method": "POST",
            "path": path,
            "params": params,
            "payload": payload,
            "allow_retries": allow_retries,
        }
        response = self.post_response if self.post_response is not None else self.response
        if result_type is UUID:
            return UUID(response)
        return result_type.model_validate(response)

    def put(self, path, *, params, payload):
        self.captured = {"method": "PUT", "path": path, "params": params, "payload": payload}

    def get(self, path, *, params, result_type):
        self.captured = {"method": "GET", "path": path, "params": params}
        if self.get_error is not None:
            raise self.get_error
        response = self.response.pop(0) if isinstance(self.response, list) else self.response
        return result_type.model_validate(response)


class _FakeOrmFolder:
    uuid = FOLDER_UUID


def _patch_clock(monkeypatch: pytest.MonkeyPatch) -> List[float]:
    """Replace the clock so that sleeping advances time at once. Returns the list of sleeps."""
    now = [0.0]
    sleeps: List[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    monkeypatch.setattr("encord.storage.time.sleep", fake_sleep)
    monkeypatch.setattr("encord.storage.time.monotonic", lambda: now[0])
    return sleeps


def _make_folder(api_client) -> StorageFolder:
    folder = StorageFolder.__new__(StorageFolder)
    folder._api_client = api_client
    folder._orm_folder = _FakeOrmFolder()
    return folder


def test_get_grouping_manifest_returns_saved_manifest() -> None:
    fake_client = _FakeApiClient(
        {
            "version": "1.0",
            "dataGroups": [
                {
                    "id": "my-group",
                    "name": "My Group",
                    "layoutType": "default-grid",
                    "members": [{"path": "images/*.png"}],
                }
            ],
        }
    )
    folder = _make_folder(fake_client)

    result = folder.get_grouping_manifest()

    assert fake_client.captured["method"] == "GET"
    assert fake_client.captured["path"] == f"storage/folders/{FOLDER_UUID}/grouping-manifest"
    assert result is not None
    assert result.data_groups[0].id == "my-group"
    assert result.data_groups[0].members == [orm_storage.MemberRule.from_path("images/*.png")]


def test_get_grouping_manifest_returns_none_when_the_folder_has_no_manifest() -> None:
    fake_client = _FakeApiClient(get_error=ResourceNotFoundError("The requested resource was not found."))
    folder = _make_folder(fake_client)

    result = folder.get_grouping_manifest()

    assert result is None


def test_get_grouping_manifest_raises_other_errors() -> None:
    fake_client = _FakeApiClient(get_error=AuthorisationError("Not allowed."))
    folder = _make_folder(fake_client)

    with pytest.raises(AuthorisationError, match="Not allowed"):
        folder.get_grouping_manifest()


def test_save_grouping_manifest_puts_manifest() -> None:
    fake_client = _FakeApiClient()
    folder = _make_folder(fake_client)
    manifest = orm_storage.GroupingManifest(
        data_groups=[
            orm_storage.DataGroupRule(
                id="my-group", name="My Group", members=[orm_storage.MemberRule.from_path("images/*.png")]
            )
        ]
    )

    folder.save_grouping_manifest(manifest)

    assert fake_client.captured["method"] == "PUT"
    assert fake_client.captured["path"] == f"storage/folders/{FOLDER_UUID}/grouping-manifest"
    assert fake_client.captured["payload"].to_dict() == {
        "version": "1.0",
        "dataGroups": [
            {
                "id": "my-group",
                "name": "My Group",
                "layoutType": "default-grid",
                "members": [{"path": "images/*.png"}],
            }
        ],
    }


def test_apply_grouping_manifest_start_returns_job_uuid() -> None:
    job_uuid = UUID("00000000-0000-0000-0000-0000000000aa")
    fake_client = _FakeApiClient({"jobUuid": str(job_uuid)})
    folder = _make_folder(fake_client)

    result = folder.apply_grouping_manifest_start()

    assert result == job_uuid
    assert fake_client.captured["method"] == "POST"
    assert fake_client.captured["path"] == f"storage/folders/{FOLDER_UUID}/grouping-manifest/jobs"
    assert fake_client.captured["payload"] is None
    assert fake_client.captured["allow_retries"] is False


@pytest.mark.parametrize(
    "dest_folder_uuid",
    [
        pytest.param(UUID("00000000-0000-0000-0000-0000000000fe"), id="groups-created"),
        pytest.param(None, id="no-ungrouped-items"),
    ],
)
def test_apply_grouping_manifest_get_result_returns_result_when_done(dest_folder_uuid: Optional[UUID]) -> None:
    job_uuid = UUID("00000000-0000-0000-0000-0000000000aa")
    fake_client = _FakeApiClient(
        {
            "status": "done",
            "destFolderUuid": str(dest_folder_uuid) if dest_folder_uuid else None,
            "groupsCreated": 5,
            "groupsSkippedAlreadyExist": 4,
            "groupsSkippedBelowThreshold": 3,
            "groupsSkippedMissingRequired": 2,
            "groupsSkippedMultilayerValidation": 1,
        }
    )
    folder = _make_folder(fake_client)

    result = folder.apply_grouping_manifest_get_result(job_uuid)

    assert fake_client.captured["method"] == "GET"
    assert fake_client.captured["path"] == f"storage/folders/{FOLDER_UUID}/grouping-manifest/jobs/{job_uuid}"
    assert result.dest_folder_uuid == dest_folder_uuid
    assert result.groups_created == 5
    assert result.groups_skipped_already_exist == 4
    assert result.groups_skipped_below_threshold == 3
    assert result.groups_skipped_missing_required == 2
    assert result.groups_skipped_multilayer_validation == 1


def test_apply_grouping_manifest_get_result_raises_server_error_when_failed() -> None:
    job_uuid = UUID("00000000-0000-0000-0000-0000000000aa")
    fake_client = _FakeApiClient({"status": "failed", "error": "Could not dispatch grouping run"})
    folder = _make_folder(fake_client)

    with pytest.raises(GenericServerError, match=f"{job_uuid}.*Could not dispatch grouping run"):
        folder.apply_grouping_manifest_get_result(job_uuid)


def test_apply_grouping_manifest_get_result_polls_with_backoff_while_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: List[float] = []
    monkeypatch.setattr("encord.storage.time.sleep", sleeps.append)
    done = {
        "status": "done",
        "destFolderUuid": None,
        "groupsCreated": 0,
        "groupsSkippedAlreadyExist": 0,
        "groupsSkippedBelowThreshold": 0,
        "groupsSkippedMissingRequired": 0,
        "groupsSkippedMultilayerValidation": 0,
    }
    fake_client = _FakeApiClient([{"status": "pending"}] * 7 + [done])
    folder = _make_folder(fake_client)

    result = folder.apply_grouping_manifest_get_result(UUID("00000000-0000-0000-0000-0000000000aa"))

    assert result.groups_created == 0
    assert sleeps == [1, 2, 4, 8, 16, 30, 30]


@pytest.mark.parametrize(
    ("timeout_kwargs", "expected_seconds_waited"),
    [
        pytest.param({"timeout_seconds": 10}, 10, id="explicit-timeout"),
        pytest.param({}, 3600, id="default-timeout"),
    ],
)
def test_apply_grouping_manifest_get_result_raises_timeout_error_when_still_pending(
    monkeypatch: pytest.MonkeyPatch, timeout_kwargs: Dict[str, int], expected_seconds_waited: int
) -> None:
    job_uuid = UUID("00000000-0000-0000-0000-0000000000aa")
    sleeps = _patch_clock(monkeypatch)
    folder = _make_folder(_FakeApiClient({"status": "pending"}))

    with pytest.raises(
        TimeOutError, match=rf"{job_uuid}.*not cancelled.*apply_grouping_manifest_get_result\({job_uuid}\)"
    ):
        folder.apply_grouping_manifest_get_result(job_uuid, **timeout_kwargs)

    assert sum(sleeps) == expected_seconds_waited


def test_apply_grouping_manifest_starts_a_job_and_returns_its_result() -> None:
    job_uuid = UUID("00000000-0000-0000-0000-0000000000aa")
    fake_client = _FakeApiClient(
        {
            "status": "done",
            "destFolderUuid": None,
            "groupsCreated": 7,
            "groupsSkippedAlreadyExist": 0,
            "groupsSkippedBelowThreshold": 0,
            "groupsSkippedMissingRequired": 0,
            "groupsSkippedMultilayerValidation": 0,
        },
        post_response={"jobUuid": str(job_uuid)},
    )
    folder = _make_folder(fake_client)

    result = folder.apply_grouping_manifest()

    assert result.groups_created == 7
    assert fake_client.captured["path"] == f"storage/folders/{FOLDER_UUID}/grouping-manifest/jobs/{job_uuid}"


@pytest.mark.parametrize(
    ("timeout_kwargs", "expected_seconds_waited"),
    [
        pytest.param({"timeout_seconds": 10}, 10, id="explicit-timeout"),
        pytest.param({}, 3600, id="default-timeout"),
    ],
)
def test_apply_grouping_manifest_times_out_while_the_job_is_pending(
    monkeypatch: pytest.MonkeyPatch, timeout_kwargs: Dict[str, int], expected_seconds_waited: int
) -> None:
    job_uuid = UUID("00000000-0000-0000-0000-0000000000aa")
    sleeps = _patch_clock(monkeypatch)
    folder = _make_folder(_FakeApiClient({"status": "pending"}, post_response={"jobUuid": str(job_uuid)}))

    with pytest.raises(TimeOutError, match=str(job_uuid)):
        folder.apply_grouping_manifest(**timeout_kwargs)

    assert sum(sleeps) == expected_seconds_waited


@pytest.mark.parametrize(
    ("constructor_name", "arguments", "expected_wire"),
    [
        pytest.param(
            "from_path",
            {"path": "images/*.png", "exclude": ["*.tmp"]},
            {"path": "images/*.png", "exclude": ["*.tmp"]},
            id="path",
        ),
        pytest.param("from_path", {"path": "images/*.png"}, {"path": "images/*.png"}, id="path-without-exclude"),
        pytest.param(
            "from_regex",
            {"regex": r"img_(?P<n>\d+)\.png", "exclude": ["*.tmp"]},
            {"regex": r"img_(?P<n>\d+)\.png", "exclude": ["*.tmp"]},
            id="regex",
        ),
        pytest.param(
            "from_simple_pattern",
            {"simple_pattern": "data/{session}/frame{n:int}.png", "exclude": ["*.tmp"]},
            {"simplePattern": "data/{session}/frame{n:int}.png", "exclude": ["*.tmp"]},
            id="simple-pattern",
        ),
    ],
)
def test_member_rule_constructor_sets_one_matcher(
    constructor_name: str, arguments: Dict[str, Any], expected_wire: Dict[str, Any]
) -> None:
    rule = getattr(orm_storage.MemberRule, constructor_name)(**arguments)

    assert rule.to_dict() == expected_wire


@pytest.mark.parametrize(
    "matchers",
    [
        pytest.param({}, id="no-matcher"),
        pytest.param({"path": "images/*.png", "regex": "img_.*"}, id="two-matchers"),
    ],
)
def test_member_rule_requires_exactly_one_matcher(matchers: Dict[str, str]) -> None:
    with pytest.raises(ValueError, match="exactly one of 'path', 'regex' or 'simple_pattern'"):
        orm_storage.MemberRule(**matchers)


@pytest.mark.parametrize(
    "wire",
    [
        pytest.param(
            {
                "id": "my-group",
                "name": "My Group",
                "layoutType": "default-grid",
                "members": [{"path": "images/a.png"}, {"regex": "images/b_.*"}],
            },
            id="members-as-list",
        ),
        pytest.param(
            {
                "id": "my-list",
                "name": "My List",
                "layoutType": "default-list",
                "members": [{"path": "images/a.png"}],
            },
            id="default-list-layout",
        ),
        pytest.param(
            {
                "id": "pairs",
                "name": "Pairs",
                "layoutType": "custom",
                "members": {"camera": {"path": "cam/a.png"}, "lidar": {"path": "lidar/a.pcd"}},
                "conditions": {
                    "minGroupSize": 3,
                    "requiredMembers": ["camera", "lidar"],
                    "allowUndersizedGroups": True,
                },
            },
            id="with-conditions",
        ),
        pytest.param(
            {
                "id": "stacked",
                "name": "Stacked",
                "layoutType": "custom",
                "members": {
                    "camera": {"path": "cam/a.png"},
                    "left": {"path": "l/a.png"},
                    "right": {"path": "r/a.png"},
                },
                "layout": {
                    "direction": "row",
                    "first": {"type": "data_unit", "key": "camera"},
                    "second": {
                        "direction": "column",
                        "splitPercentage": 30,
                        "first": {
                            "type": "data_unit_list",
                            "keys": ["left"],
                            "carouselPosition": "left",
                            "carouselSize": 30,
                        },
                        "second": {"type": "data_unit_list", "keys": ["right"]},
                    },
                },
            },
            id="with-layout",
        ),
        pytest.param(
            {
                "id": "one",
                "name": "One",
                "layoutType": "custom",
                "members": {"camera": {"path": "cam/a.png"}},
                "layout": {"type": "data_unit", "key": "camera"},
            },
            id="single-tile-layout",
        ),
        pytest.param(
            {
                "id": "many",
                "name": "Many",
                "layoutType": "custom",
                "members": {"camera": {"path": "cam/a.png"}},
                "layout": {"type": "data_unit_list", "keys": ["camera"], "carouselPosition": "top"},
            },
            id="single-carousel-layout",
        ),
        pytest.param(
            {
                "id": "{session}_{sensor}",
                "name": "Session {session}",
                "layoutType": "custom",
                "members": {"camera": {"regex": "(?P<session>s\\\\d+)/(?P<sensor>cam)\\\\.png"}},
                "groupBy": ["session"],
                "clientMetadata": {"source": "rig-1", "run": 7},
                "settings": {
                    "fixedLayout": True,
                    "tileSettings": {"camera": {"title": "Front", "isReadOnly": True}},
                    "hasMultilayerLabels": True,
                },
            },
            id="with-group-by-metadata-and-settings",
        ),
        pytest.param(
            {
                "id": "{session}",
                "name": "Session {session}",
                "layoutType": "custom",
                "members": {"camera": {"path": "cam/a.png"}, "lidar": {"simplePattern": "lidar/{session}.pcd"}},
            },
            id="members-as-dict",
        ),
    ],
)
def test_data_group_rule_round_trips_members(wire: Dict[str, Any]) -> None:
    rule = orm_storage.DataGroupRule.from_dict(wire)

    assert rule.to_dict() == wire


def test_data_group_rule_layout_type_defaults_to_default_grid() -> None:
    rule = orm_storage.DataGroupRule.from_dict({"id": "g", "name": "G", "members": [{"path": "a.png"}]})

    assert rule.layout_type == "default-grid"


@pytest.mark.parametrize(
    "missing_key",
    [pytest.param("id", id="no-id"), pytest.param("name", id="no-name"), pytest.param("members", id="no-members")],
)
def test_data_group_rule_requires_id_name_and_members(missing_key: str) -> None:
    wire = {"id": "g", "name": "G", "members": [{"path": "a.png"}]}
    del wire[missing_key]

    with pytest.raises(EncordException, match=f"{missing_key}\\n *Field required"):
        orm_storage.DataGroupRule.from_dict(wire)


def test_group_conditions_defaults() -> None:
    assert orm_storage.GroupConditions().to_dict() == {"minGroupSize": 2, "allowUndersizedGroups": False}


def test_data_group_rule_nested_fields_are_typed() -> None:
    wire_layout = {
        "direction": "row",
        "first": {
            "direction": "column",
            "first": {"type": "data_unit", "key": "a"},
            "second": {"type": "data_unit", "key": "b"},
        },
        "second": {"type": "data_unit_list", "keys": ["c"], "carouselPosition": "top"},
    }

    rule = orm_storage.DataGroupRule.from_dict(
        {
            "id": "g",
            "name": "G",
            "layoutType": "custom",
            "members": {"a": {"path": "a"}},
            "layout": wire_layout,
            "settings": {"tileSettings": {"a": {"isReadOnly": True}}},
        }
    )

    assert isinstance(rule.layout, orm_storage.ManifestGridLayout)
    assert isinstance(rule.layout.first, orm_storage.ManifestGridLayout)
    assert rule.layout.first.second.key == "b"  # type: ignore[union-attr]
    assert isinstance(rule.layout.second, orm_storage.ManifestCarouselTile)
    assert rule.layout.second.carousel_position == "top"
    assert isinstance(rule.settings, LayoutSettings)
    assert rule.settings.tile_settings is not None
    assert rule.settings.tile_settings["a"].is_read_only is True


def test_grouping_manifest_round_trips() -> None:
    wire = {
        "version": "1.0",
        "dataGroups": [
            {
                "id": "images",
                "name": "Images",
                "layoutType": "default-grid",
                "members": [{"path": "images/*.png"}],
            },
            {
                "id": "{session}",
                "name": "Session {session}",
                "layoutType": "custom",
                "members": {"camera": {"simplePattern": "{session}/cam.png"}},
                "layout": {"type": "data_unit", "key": "camera"},
            },
        ],
    }

    manifest = orm_storage.GroupingManifest.from_dict(wire)

    assert manifest.to_dict() == wire
    assert isinstance(manifest.data_groups[0], orm_storage.DataGroupRule)


def test_grouping_manifest_defaults() -> None:
    manifest = orm_storage.GroupingManifest.from_dict({})

    assert manifest.version == "1.0"
    assert manifest.data_groups == []


def test_storage_folder_has_no_preview_grouping_manifest() -> None:
    assert not hasattr(StorageFolder, "preview_grouping_manifest")
