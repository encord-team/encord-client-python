import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import encord.exceptions
from encord.configs import _ENCORD_SSH_KEY, _ENCORD_SSH_KEY_FILE
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
