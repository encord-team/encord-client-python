from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock
from uuid import UUID

import encord.orm.storage as orm_storage
from encord.orm.storage import (
    MetadataIngestionConfig,
    SidecarMatcherSuffix,
    StorageFolderConfig,
)
from encord.storage import StorageFolder

FOLDER_UUID = UUID("00000000-0000-0000-0000-000000000006")

# A folder config as the server returns it. The SDK only models ``metadataIngestion``;
# everything else (here, Encord Index settings) must survive a read/modify/write cycle.
SERVER_CONFIG = {
    "indexFolderConfig": {"embeddingConfig": {}, "baseMetricsEnabled": True},
}


def _make_folder(api_client: Mock) -> StorageFolder:
    orm_folder = cast(orm_storage.StorageFolder, SimpleNamespace(uuid=FOLDER_UUID, parent=None))
    return StorageFolder(api_client, orm_folder)


def test_config_round_trips_with_camel_case_keys() -> None:
    config = StorageFolderConfig(metadata_ingestion=MetadataIngestionConfig())

    serialized = config.to_dict()
    assert serialized["metadataIngestion"]["matcher"] == {"mode": "suffix", "suffix": ".metadata.json"}
    assert StorageFolderConfig.from_dict(serialized).to_dict() == serialized


def test_unmodeled_config_keys_are_preserved_on_round_trip() -> None:
    # The server returns config the SDK does not model (e.g. indexFolderConfig,
    # labelImport). BaseDTOWithExtra must carry these through a read/write cycle
    # unchanged so enabling metadata ingestion cannot clobber them.
    payload = {
        **SERVER_CONFIG,
        "labelImport": {"ontologyHash": "00000000-0000-0000-0000-000000000009"},
    }
    config = StorageFolderConfig.from_dict(payload)
    assert config.metadata_ingestion is None

    config.metadata_ingestion = MetadataIngestionConfig()
    serialized = config.to_dict()
    assert serialized["indexFolderConfig"] == {"embeddingConfig": {}, "baseMetricsEnabled": True}
    assert serialized["labelImport"] == {"ontologyHash": "00000000-0000-0000-0000-000000000009"}


def test_suffix_matcher_round_trips() -> None:
    config = MetadataIngestionConfig(matcher=SidecarMatcherSuffix(suffix=".meta.json"))
    parsed = MetadataIngestionConfig.from_dict(config.to_dict())
    assert isinstance(parsed.matcher, SidecarMatcherSuffix)
    assert parsed.matcher.suffix == ".meta.json"


def test_get_folder_config_calls_read_endpoint() -> None:
    api_client = Mock()
    expected = StorageFolderConfig.from_dict(SERVER_CONFIG)
    api_client.get.return_value = expected
    folder = _make_folder(api_client)

    assert folder.get_folder_config() is expected
    api_client.get.assert_called_once_with(
        f"storage/folders/{FOLDER_UUID}/folder-config",
        params=None,
        result_type=StorageFolderConfig,
    )


def test_enable_metadata_ingestion_preserves_existing_config_and_posts() -> None:
    api_client = Mock()
    api_client.get.return_value = StorageFolderConfig.from_dict(SERVER_CONFIG)
    folder = _make_folder(api_client)

    folder.enable_metadata_ingestion(paused=True)

    args, kwargs = api_client.post.call_args
    assert args[0] == f"storage/folders/{FOLDER_UUID}/folder-config"
    assert kwargs["result_type"] is None
    sent = kwargs["payload"]
    # Unmodeled index settings preserved, metadata ingestion enabled.
    assert sent.to_dict()["indexFolderConfig"] == {"embeddingConfig": {}, "baseMetricsEnabled": True}
    assert sent.metadata_ingestion is not None
    assert sent.metadata_ingestion.paused is True
    assert isinstance(sent.metadata_ingestion.matcher, SidecarMatcherSuffix)


def test_enable_metadata_ingestion_accepts_custom_matcher() -> None:
    api_client = Mock()
    api_client.get.return_value = StorageFolderConfig.from_dict(SERVER_CONFIG)
    folder = _make_folder(api_client)

    folder.enable_metadata_ingestion(SidecarMatcherSuffix(suffix=".sidecar.json"))

    sent = api_client.post.call_args.kwargs["payload"]
    assert sent.metadata_ingestion.matcher.suffix == ".sidecar.json"
