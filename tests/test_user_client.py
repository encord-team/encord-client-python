import os

import pytest

import encord.exceptions
from encord.configs import _ENCORD_SSH_KEY
from encord.user_client import EncordUserClient


@pytest.fixture
def ssh_key_file_path():
    # TODO: What is the proper way to do this?
    return "./ssh_private_test_key"


def test_initialise_without_env_variable_or_arguments():
    assert _ENCORD_SSH_KEY not in os.environ
    with pytest.raises(expected_exception=encord.exceptions.ResourceNotFoundError) as excinfo:
        EncordUserClient.create_with_ssh_private_key()


def test_initialise_with_wrong_ssh_file_path():
    os.environ[_ENCORD_SSH_KEY] = "some_wrong/file/path"
    with pytest.raises(expected_exception=encord.exceptions.ResourceNotFoundError) as excinfo:
        EncordUserClient.create_with_ssh_private_key()
    del os.environ[_ENCORD_SSH_KEY]


@pytest.mark.skip(reason="Not clear how to get an ssh key file for the purpose")
def test_initialise_with_correct_ssh_file_path(ssh_key_file_path):
    os.environ[_ENCORD_SSH_KEY] = ssh_key_file_path
    user_client = EncordUserClient.create_with_ssh_private_key()
    assert isinstance(user_client, EncordUserClient)


@pytest.mark.skip(reason="Not clear how to get an ssh key file for the purpose")
def test_initialise_with_correct_ssh_file_content(ssh_key_file_path):
    with open(ssh_key_file_path, 'r') as f:
        private_key = f.read()

    user_client = EncordUserClient.create_with_ssh_private_key(private_key)
    assert isinstance(user_client, EncordUserClient)


def test_initialise_with_wrong_ssh_file_content():
    with pytest.raises(expected_exception=ValueError) as excinfo:
        user_client = EncordUserClient.create_with_ssh_private_key("Some random content.")


