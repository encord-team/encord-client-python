"""Tests for the organisation-tag filter on the storage folder-listing methods.

Covers the four entry points that hit the backend's tag-filterable folder endpoints:
``EncordUserClient.list_storage_folders`` / ``find_storage_folders`` and
``StorageFolder.list_subfolders`` / ``find_subfolders``. Each accepts
``organisation_tags_allof`` as tag-name strings or :class:`OrganisationTag` instances and
forwards it to the ``organisation_tag_names_allof`` query field (allOf semantics).

String tag names are validated against the organisation's tags before any folders are fetched.
"""

import uuid
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from encord.exceptions import ResourceNotFoundError
from encord.http.v2.api_client import ApiClient
from encord.orm.project import OrganisationTag
from encord.orm.storage import ListFoldersParams
from encord.storage import StorageFolder
from encord.user_client import EncordUserClient


def _captured_params(api_get_paged: MagicMock) -> ListFoldersParams:
    # StorageFolder._list_folders calls api_client.get_paged_iterator(path, params, result_type)
    args, _ = api_get_paged.call_args
    return args[1]


def _folder(api_client: MagicMock) -> StorageFolder:
    orm_folder = MagicMock()
    orm_folder.uuid = uuid.uuid4()
    return StorageFolder(api_client, orm_folder)


def _known_tags_page(*names: str) -> MagicMock:
    """Build a stand-in for the paged org-tags response the validator reads via ``.results``."""
    page = MagicMock()
    page.results = [OrganisationTag(uuid=uuid.uuid4(), name=name) for name in names]
    return page


def _mock_known_tags(api_get: MagicMock, *names: str) -> None:
    api_get.return_value = _known_tags_page(*names)


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "get_paged_iterator")
def test_list_storage_folders_accepts_tag_name_strings(
    api_get_paged: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])
    _mock_known_tags(api_get, "alpha", "beta", "gamma")

    list(user_client.list_storage_folders(organisation_tags_allof=["alpha", "beta"]))

    assert _captured_params(api_get_paged).organisation_tag_names_allof == ["alpha", "beta"]


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "get_paged_iterator")
def test_find_storage_folders_accepts_organisation_tag_instances(
    api_get_paged: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])
    tags = [OrganisationTag(uuid=uuid.uuid4(), name=name) for name in ["alpha", "beta"]]

    list(user_client.find_storage_folders(organisation_tags_allof=tags))

    assert _captured_params(api_get_paged).organisation_tag_names_allof == ["alpha", "beta"]
    # OrganisationTag instances are already known-valid: no org-tags lookup should be issued.
    api_get.assert_not_called()


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "get_paged_iterator")
def test_list_storage_folders_omits_filter_when_not_given(
    api_get_paged: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])

    list(user_client.list_storage_folders())

    params = _captured_params(api_get_paged)
    assert params.organisation_tag_names_allof is None
    # Omitted from the serialised query string entirely (exclude_none).
    assert "organisationTagNamesAllof" not in params.to_dict()
    # No filter means no need to validate tag names.
    api_get.assert_not_called()


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "get_paged_iterator")
def test_unknown_tag_name_raises_naming_the_bad_tag(
    api_get_paged: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])
    _mock_known_tags(api_get, "alpha", "beta")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        list(user_client.list_storage_folders(organisation_tags_allof=["alpha", "typo"]))

    message = str(exc_info.value)
    assert "'typo'" in message
    # The valid name is not misreported as missing.
    assert "'alpha'" not in message
    # The request is never sent when a name is unknown.
    api_get_paged.assert_not_called()


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "get_paged_iterator")
def test_multiple_unknown_tag_names_are_all_reported(
    api_get_paged: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])
    _mock_known_tags(api_get, "FDE")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        list(user_client.list_storage_folders(organisation_tags_allof=["Joseph", "FDE", "Acme"]))

    message = str(exc_info.value)
    assert "'Joseph'" in message
    assert "'Acme'" in message
    assert "'FDE'" not in message


def _captured_subfolder_params(list_folders: MagicMock) -> ListFoldersParams:
    # StorageFolder._list_folders(api_client, path, params)
    args, _ = list_folders.call_args
    return args[2]


def _subfolder(known_tag_names: List[str]) -> StorageFolder:
    api_client = MagicMock(spec=ApiClient)
    api_client.get.return_value = _known_tags_page(*known_tag_names)
    return _folder(api_client)


@patch.object(StorageFolder, "_list_folders", return_value=iter([]))
def test_list_subfolders_forwards_tag_filter(list_folders: MagicMock) -> None:
    folder = _subfolder(["alpha"])

    list(folder.list_subfolders(organisation_tags_allof=["alpha"]))

    assert _captured_subfolder_params(list_folders).organisation_tag_names_allof == ["alpha"]


@patch.object(StorageFolder, "_list_folders", return_value=iter([]))
def test_find_subfolders_forwards_tag_filter_recursively(list_folders: MagicMock) -> None:
    folder = _folder(MagicMock(spec=ApiClient))
    tags = [OrganisationTag(uuid=uuid.uuid4(), name="alpha")]

    list(folder.find_subfolders(organisation_tags_allof=tags))

    params = _captured_subfolder_params(list_folders)
    assert params.organisation_tag_names_allof == ["alpha"]
    assert params.is_recursive is True


@patch.object(StorageFolder, "_list_folders", return_value=iter([]))
def test_list_subfolders_unknown_tag_name_raises(list_folders: MagicMock) -> None:
    folder = _subfolder(["alpha"])

    with pytest.raises(ResourceNotFoundError, match="'typo'"):
        list(folder.list_subfolders(organisation_tags_allof=["typo"]))

    list_folders.assert_not_called()


def test_filter_serialises_to_expected_camel_case_query_key() -> None:
    params = ListFoldersParams(organisation_tag_names_allof=["alpha", "beta"])

    assert params.to_dict()["organisationTagNamesAllof"] == ["alpha", "beta"]
