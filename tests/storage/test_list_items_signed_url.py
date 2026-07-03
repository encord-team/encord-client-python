import json
from datetime import datetime
from typing import Optional
from unittest.mock import patch
from uuid import UUID

import encord.orm.storage as orm_storage
import encord.storage as storage_module
from encord.http.v2.payloads import Page
from encord.orm.storage import (
    StorageItem as OrmStorageItem,
)
from encord.orm.storage import (
    StorageItemType,
    StorageItemWithClientMetadataSignedUrl,
    StorageLocationName,
)
from encord.storage import StorageFolder

FOLDER_UUID = UUID("00000000-0000-0000-0000-0000000000ff")


def _item_blob(index: int, *, client_metadata: str, signed_url: Optional[str]) -> dict:
    blob = {
        "uuid": str(UUID(int=index)),
        "parent": str(FOLDER_UUID),
        "item_type": StorageItemType.IMAGE.value,
        "name": f"item-{index}",
        "client_metadata": client_metadata,
        "owner": "someone@encord.com",
        "created_at": datetime(2024, 1, 1).isoformat(),
        "last_edited_at": datetime(2024, 1, 2).isoformat(),
        "backed_data_units_count": 1,
        "storage_location": StorageLocationName.S3.value,
        "integration_hash": None,
        "url": None,
        "signed_url": None,
        "file_size": None,
        "mime_type": None,
        "duration": None,
        "fps": None,
        "height": None,
        "width": None,
        "dicom_instance_uid": None,
        "dicom_study_uid": None,
        "dicom_series_uid": None,
        "frame_count": None,
        "audio_sample_rate": None,
        "audio_bit_depth": None,
        "audio_codec": None,
        "audio_num_channels": None,
    }
    if signed_url is not None:
        blob["client_metadata_signed_url"] = signed_url
    return blob


class _FakeApiClient:
    def __init__(self, pages):
        self._pages = pages
        self.requests_settings = object()
        self.get_calls = []
        self.paged_iterator_calls = []

    def get(self, path, params, result_type):
        self.get_calls.append((path, params, result_type))
        return self._pages.pop(0)

    def get_paged_iterator(self, path, params, result_type):
        self.paged_iterator_calls.append((path, params, result_type))
        for page in self._pages:
            yield from page.results


class _FakeOrmFolder:
    uuid = FOLDER_UUID


def _make_folder(api_client):
    folder = StorageFolder.__new__(StorageFolder)
    folder._api_client = api_client
    folder._orm_folder = _FakeOrmFolder()
    return folder


def test_list_items_resolves_client_metadata_via_signed_url():
    page = Page(
        results=[
            StorageItemWithClientMetadataSignedUrl.from_dict(
                _item_blob(i, client_metadata="", signed_url=f"https://bucket/cm-{i}.json")
            )
            for i in range(3)
        ],
        next_page_token=None,
    )
    resolved = {f"https://bucket/cm-{i}.json": {"idx": i} for i in range(3)}
    api_client = _FakeApiClient([page])

    with patch.object(storage_module, "download_signed_urls_as_json", return_value=resolved) as download_mock:
        items = list(
            _make_folder(api_client).list_items(
                include_client_metadata=True,
                resolve_client_metadata_locally=True,
            )
        )

    # Each item exposes the resolved (downloaded + inlined) client_metadata.
    for i, item in enumerate(items):
        assert item.client_metadata == {"idx": i}

    # Paged via .get() with the signed-URL subclass, never the default paged iterator.
    assert api_client.paged_iterator_calls == []
    result_type = api_client.get_calls[0][2]
    assert result_type is Page[StorageItemWithClientMetadataSignedUrl]

    # All signed URLs were handed to the downloader in one batch.
    download_mock.assert_called_once()
    (urls_arg,) = download_mock.call_args.args
    assert sorted(urls_arg) == sorted(resolved.keys())


def test_list_items_paginates_and_resolves_each_page():
    pages = [
        Page(
            results=[
                StorageItemWithClientMetadataSignedUrl.from_dict(
                    _item_blob(0, client_metadata="", signed_url="https://bucket/cm-0.json")
                )
            ],
            next_page_token="next",
        ),
        Page(
            results=[
                StorageItemWithClientMetadataSignedUrl.from_dict(
                    _item_blob(1, client_metadata="", signed_url="https://bucket/cm-1.json")
                )
            ],
            next_page_token=None,
        ),
    ]
    api_client = _FakeApiClient(pages)

    def fake_download(urls, *, requests_settings):
        return {url: {"url": url} for url in urls}

    with patch.object(storage_module, "download_signed_urls_as_json", side_effect=fake_download) as download_mock:
        items = list(
            _make_folder(api_client).list_items(
                include_client_metadata=True,
                resolve_client_metadata_locally=True,
            )
        )

    assert [item.client_metadata for item in items] == [
        {"url": "https://bucket/cm-0.json"},
        {"url": "https://bucket/cm-1.json"},
    ]
    # One .get() per page, one download batch per page.
    assert len(api_client.get_calls) == 2
    assert download_mock.call_count == 2


def test_list_items_leaves_items_without_urls_untouched():
    page = Page(
        results=[
            StorageItemWithClientMetadataSignedUrl.from_dict(
                _item_blob(0, client_metadata="", signed_url="https://bucket/cm.json")
            ),
            StorageItemWithClientMetadataSignedUrl.from_dict(
                _item_blob(1, client_metadata=json.dumps({"inline": True}), signed_url="")
            ),
        ],
        next_page_token=None,
    )
    resolved = {"https://bucket/cm.json": {"fetched": True}}
    api_client = _FakeApiClient([page])

    with patch.object(storage_module, "download_signed_urls_as_json", return_value=resolved):
        items = list(
            _make_folder(api_client).list_items(
                include_client_metadata=True,
                resolve_client_metadata_locally=True,
            )
        )

    assert items[0].client_metadata == {"fetched": True}
    # The item without a resolvable URL keeps whatever client_metadata it already had.
    assert items[1].client_metadata == {"inline": True}


def test_list_items_without_flag_uses_default_iterator_and_skips_resolution():
    page = Page(
        results=[
            OrmStorageItem.from_dict(_item_blob(0, client_metadata=json.dumps({"inline": True}), signed_url=None))
        ],
        next_page_token=None,
    )
    api_client = _FakeApiClient([page])

    with patch.object(storage_module, "download_signed_urls_as_json") as download_mock:
        items = list(_make_folder(api_client).list_items(include_client_metadata=True))
        download_mock.assert_not_called()

    assert items[0].client_metadata == {"inline": True}
    # Default path goes through the paged iterator with the base type.
    assert api_client.get_calls == []
    assert api_client.paged_iterator_calls[0][2] is orm_storage.StorageItem
