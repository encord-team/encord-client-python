"""Tests for the cloud-sync fields exposed on ``StorageFolder`` (FOU-1573)."""

import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock

from encord.common.time_parser import format_datetime_to_long_string
from encord.orm.storage import StorageFolder as OrmStorageFolder
from encord.orm.storage import StorageFolderType
from encord.storage import StorageFolder


def _folder_payload(**overrides: Any) -> Dict[str, Any]:
    """A folder-info wire payload (camelCase), with the given field overrides."""
    now = format_datetime_to_long_string(datetime.now())
    payload: Dict[str, Any] = {
        "uuid": str(uuid.uuid4()),
        "parent": None,
        "name": "folder",
        "description": "",
        "clientMetadata": None,
        "owner": "user@encord.com",
        "createdAt": now,
        "lastEditedAt": now,
        "userRole": "admin",
        "syncedDatasetHash": None,
        "pathToRoot": [],
    }
    payload.update(overrides)
    return payload


def _wrap(payload: Dict[str, Any]) -> StorageFolder:
    return StorageFolder(Mock(), OrmStorageFolder.from_dict(payload))


def test_regular_folder_defaults_and_backwards_compatibility() -> None:
    """A payload from a server predating these fields deserialises as a regular folder."""
    folder = _wrap(_folder_payload())

    assert folder.folder_type == StorageFolderType.GENERIC
    assert folder.is_cloud_synced is False
    assert folder.integration_hash is None
    assert folder.remote_url is None


def test_cloud_linked_folder_exposes_integration_and_remote_url() -> None:
    integration_hash = uuid.uuid4()
    remote_url = "gs://cloud-synced-folder/prefix"
    folder = _wrap(
        _folder_payload(
            folderType="cloudLinked",
            integrationHash=str(integration_hash),
            remoteUrl=remote_url,
        )
    )

    assert folder.folder_type == StorageFolderType.CLOUD_LINKED
    assert folder.is_cloud_synced is True
    assert folder.integration_hash == integration_hash
    assert folder.remote_url == remote_url


def test_unrecognized_folder_type_falls_back_to_unknown() -> None:
    """A folder type newer than this SDK version parses as UNKNOWN rather than erroring."""
    folder = _wrap(_folder_payload(folderType="someFutureFolderType"))

    assert folder.folder_type == StorageFolderType.UNKNOWN
    assert folder.is_cloud_synced is False
