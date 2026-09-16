import os
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

import encord.exceptions
from encord.configs import _ENCORD_SSH_KEY, _ENCORD_SSH_KEY_FILE
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.project import CreateOrganisationTagPayload, OrganisationTag, ProjectTag
from encord.user_client import EncordUserClient
from tests.conftest import PRIVATE_KEY_PEM


def teardown_function():
    if _ENCORD_SSH_KEY_FILE in os.environ:
        del os.environ[_ENCORD_SSH_KEY_FILE]
    if _ENCORD_SSH_KEY in os.environ:
        del os.environ[_ENCORD_SSH_KEY]


def test_initialise_without_env_variables_or_arguments():
    assert _ENCORD_SSH_KEY not in os.environ
    assert _ENCORD_SSH_KEY_FILE not in os.environ
    with pytest.raises(expected_exception=encord.exceptions.ResourceNotFoundError):
        EncordUserClient.create_with_ssh_private_key()


def test_initialise_with_wrong_ssh_file_path():
    os.environ[_ENCORD_SSH_KEY_FILE] = "some_wrong/file/path"
    with pytest.raises(expected_exception=encord.exceptions.ResourceNotFoundError):
        EncordUserClient.create_with_ssh_private_key()


def test_initialise_with_correct_ssh_file_path_from_env():
    with TemporaryDirectory() as tmpdir_name:
        tmp_dir_path = Path(tmpdir_name)
        tmp_key_path = tmp_dir_path / "key"

        with open(tmp_key_path, "w") as f:
            f.write(PRIVATE_KEY_PEM)

        os.environ[_ENCORD_SSH_KEY_FILE] = str(tmp_key_path.resolve())
        user_client = EncordUserClient.create_with_ssh_private_key()
        assert isinstance(user_client, EncordUserClient)


def test_initialise_with_correct_ssh_file_content():
    user_client = EncordUserClient.create_with_ssh_private_key(PRIVATE_KEY_PEM)
    assert isinstance(user_client, EncordUserClient)


def test_initialise_with_custom_user_agent():
    custom_agent_suffix = "CustomAgentSuffix/1.1.2"
    user_client = EncordUserClient.create_with_ssh_private_key(PRIVATE_KEY_PEM, user_agent_suffix=custom_agent_suffix)
    assert isinstance(user_client, EncordUserClient)
    user_agent_header = user_client._config.config._user_agent()
    assert custom_agent_suffix in user_agent_header


def test_initialise_with_correct_ssh_file_content_from_env():
    assert _ENCORD_SSH_KEY_FILE not in os.environ
    os.environ[_ENCORD_SSH_KEY] = PRIVATE_KEY_PEM
    user_client = EncordUserClient.create_with_ssh_private_key()
    assert isinstance(user_client, EncordUserClient)


def test_initialise_with_wrong_ssh_file_content():
    with pytest.raises(expected_exception=ValueError):
        EncordUserClient.create_with_ssh_private_key("Some random content.")


def test_initialise_with_wrong_ssh_file_content_from_env():
    assert _ENCORD_SSH_KEY_FILE not in os.environ
    os.environ[_ENCORD_SSH_KEY] = "Some random content."
    with pytest.raises(expected_exception=ValueError):
        EncordUserClient.create_with_ssh_private_key()


@pytest.mark.parametrize(
    "tag_names",
    [
        pytest.param([], id="none"),
        pytest.param(["my-tag"], id="one"),
        pytest.param(["alpha", "beta", "gamma"], id="many"),
    ],
)
@patch.object(ApiClient, "get")
def test_list_organisation_tags(api_get: MagicMock, user_client: EncordUserClient, tag_names: list[str]) -> None:
    tags = [OrganisationTag(uuid=uuid.uuid4(), name=name) for name in tag_names]
    api_get.return_value = Page(results=tags)

    result = user_client.list_organisation_tags()

    assert result == tags
    api_get.assert_called_once_with("organisation/organisation-tags", params=None, result_type=Page[OrganisationTag])


@patch.object(ApiClient, "get")
def test_list_project_tags_is_deprecated_and_delegates(api_get: MagicMock, user_client: EncordUserClient) -> None:
    tags = [OrganisationTag(uuid=uuid.uuid4(), name="my-tag")]
    api_get.return_value = Page(results=tags)

    with pytest.warns(DeprecationWarning, match="list_organisation_tags"):
        result = user_client.list_project_tags()

    assert result == tags
    api_get.assert_called_once_with("organisation/organisation-tags", params=None, result_type=Page[OrganisationTag])


@patch.object(ApiClient, "get_paged_iterator")
def test_list_projects_tags_anyof_accepts_organisation_tag_instances(
    api_get_paged: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])
    tags = [OrganisationTag(uuid=uuid.uuid4(), name=name) for name in ["alpha", "beta"]]

    list(user_client.list_projects(tags_anyof=tags))

    _, call_kwargs = api_get_paged.call_args
    assert call_kwargs["params"].tags_anyof == ["alpha", "beta"]


def test_project_tag_is_an_alias_of_organisation_tag() -> None:
    assert ProjectTag is OrganisationTag


@patch.object(ApiClient, "post")
def test_create_organisation_tag_posts_expected_payload(api_post: MagicMock, user_client: EncordUserClient) -> None:
    created = OrganisationTag(uuid=uuid.uuid4(), name="batch-3")
    api_post.return_value = created

    result = user_client.create_organisation_tag("batch-3", description="Batch 3 of the rollout")

    assert result == created
    api_post.assert_called_once_with(
        "organisation/organisation-tags",
        params=None,
        payload=CreateOrganisationTagPayload(name="batch-3", description="Batch 3 of the rollout"),
        result_type=OrganisationTag,
    )


def test_create_organisation_tag_payload_omits_missing_description() -> None:
    assert CreateOrganisationTagPayload(name="batch-3").to_dict() == {"name": "batch-3"}
    assert CreateOrganisationTagPayload(name="batch-3", description="d").to_dict() == {
        "name": "batch-3",
        "description": "d",
    }


@pytest.mark.parametrize("as_str", [False, True], ids=["UUID", "str"])
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_delete_organisation_tag_by_uuid_does_not_list(
    api_delete: MagicMock, api_get: MagicMock, user_client: EncordUserClient, as_str: bool
) -> None:
    tag_uuid = uuid.uuid4()

    user_client.delete_organisation_tag(tag_uuid=str(tag_uuid) if as_str else tag_uuid)

    api_get.assert_not_called()
    api_delete.assert_called_once_with(f"organisation/organisation-tags/{tag_uuid}", params=None, result_type=None)


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_delete_organisation_tag_by_instance_does_not_list(
    api_delete: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    tag = OrganisationTag(uuid=uuid.uuid4(), name="batch-3")

    user_client.delete_organisation_tag(tag)

    api_get.assert_not_called()
    api_delete.assert_called_once_with(f"organisation/organisation-tags/{tag.uuid}", params=None, result_type=None)


@pytest.mark.parametrize("bad_tag", [pytest.param("batch-3", id="str"), pytest.param(uuid.uuid4(), id="UUID")])
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_delete_organisation_tag_rejects_positional_identifiers(
    api_delete: MagicMock, api_get: MagicMock, user_client: EncordUserClient, bad_tag: object
) -> None:
    with pytest.raises(TypeError, match="OrganisationTag"):
        user_client.delete_organisation_tag(bad_tag)  # type: ignore[arg-type]

    api_get.assert_not_called()
    api_delete.assert_not_called()


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_delete_organisation_tag_by_name_resolves_uuid_from_listing(
    api_delete: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    other = OrganisationTag(uuid=uuid.uuid4(), name="batch-2")
    target = OrganisationTag(uuid=uuid.uuid4(), name="batch-3")
    api_get.return_value = Page(results=[other, target])

    user_client.delete_organisation_tag(tag_name="batch-3")

    api_get.assert_called_once_with("organisation/organisation-tags", params=None, result_type=Page[OrganisationTag])
    api_delete.assert_called_once_with(f"organisation/organisation-tags/{target.uuid}", params=None, result_type=None)


@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_delete_organisation_tag_by_unknown_name_raises(
    api_delete: MagicMock, api_get: MagicMock, user_client: EncordUserClient
) -> None:
    api_get.return_value = Page(results=[OrganisationTag(uuid=uuid.uuid4(), name="batch-2")])

    with pytest.raises(encord.exceptions.ResourceNotFoundError):
        user_client.delete_organisation_tag(tag_name="batch-3")

    api_delete.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [pytest.param({}, id="neither"), pytest.param({"tag_name": "batch-3", "tag_uuid": uuid.uuid4()}, id="both")],
)
@patch.object(ApiClient, "get")
@patch.object(ApiClient, "delete")
def test_delete_organisation_tag_requires_exactly_one_identifier(
    api_delete: MagicMock, api_get: MagicMock, user_client: EncordUserClient, kwargs: dict
) -> None:
    with pytest.raises(ValueError, match="Exactly one of"):
        user_client.delete_organisation_tag(**kwargs)

    api_get.assert_not_called()
    api_delete.assert_not_called()
