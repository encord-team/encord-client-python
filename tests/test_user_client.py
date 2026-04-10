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
from encord.orm.project import ProjectTag
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
def test_list_project_tags(api_get: MagicMock, user_client: EncordUserClient, tag_names: list[str]) -> None:
    tags = [ProjectTag(uuid=uuid.uuid4(), name=name) for name in tag_names]
    api_get.return_value = Page(results=tags)

    result = user_client.list_project_tags()

    assert result == tags
    api_get.assert_called_once()


@patch.object(ApiClient, "get_paged_iterator")
def test_list_projects_tags_anyof_accepts_project_tag_instances(
    api_get_paged: MagicMock, user_client: EncordUserClient
) -> None:
    api_get_paged.return_value = iter([])
    tags = [ProjectTag(uuid=uuid.uuid4(), name=name) for name in ["alpha", "beta"]]

    list(user_client.list_projects(tags_anyof=tags))

    _, call_kwargs = api_get_paged.call_args
    assert call_kwargs["params"].tags_anyof == ["alpha", "beta"]
