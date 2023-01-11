import os

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import encord.exceptions
from encord.configs import _ENCORD_SSH_KEY, _ENCORD_SSH_KEY_FILE
from encord.user_client import EncordUserClient

PRIVATE_KEY = (
    Ed25519PrivateKey.generate()
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
)


@pytest.fixture
def ssh_key_file_path():
    return os.path.join(os.path.dirname(__file__), "resources/test_key")


@pytest.fixture
def ssh_key_content():
    return PRIVATE_KEY


def teardown_function():
    if _ENCORD_SSH_KEY_FILE in os.environ:
        del os.environ[_ENCORD_SSH_KEY_FILE]
    if _ENCORD_SSH_KEY in os.environ:
        del os.environ[_ENCORD_SSH_KEY]


def test_initialise_without_env_variables_or_arguments():
    assert _ENCORD_SSH_KEY not in os.environ
    assert _ENCORD_SSH_KEY_FILE not in os.environ
    with pytest.raises(expected_exception=encord.exceptions.ResourceNotFoundError) as excinfo:
        EncordUserClient.create_with_ssh_private_key()


def test_initialise_with_wrong_ssh_file_path():
    os.environ[_ENCORD_SSH_KEY_FILE] = "some_wrong/file/path"
    with pytest.raises(expected_exception=encord.exceptions.ResourceNotFoundError) as excinfo:
        EncordUserClient.create_with_ssh_private_key()


def test_initialise_with_correct_ssh_file_path_from_env(ssh_key_file_path):
    os.environ[_ENCORD_SSH_KEY_FILE] = ssh_key_file_path
    user_client = EncordUserClient.create_with_ssh_private_key()
    assert isinstance(user_client, EncordUserClient)


def test_initialise_with_correct_ssh_file_content(ssh_key_content):
    user_client = EncordUserClient.create_with_ssh_private_key(ssh_key_content)
    assert isinstance(user_client, EncordUserClient)


def test_initialise_with_correct_ssh_file_content_from_env(ssh_key_content):
    assert _ENCORD_SSH_KEY_FILE not in os.environ
    os.environ[_ENCORD_SSH_KEY] = ssh_key_content
    user_client = EncordUserClient.create_with_ssh_private_key()
    assert isinstance(user_client, EncordUserClient)


def test_initialise_with_wrong_ssh_file_content():
    with pytest.raises(expected_exception=ValueError) as excinfo:
        user_client = EncordUserClient.create_with_ssh_private_key("Some random content.")


def test_initialise_with_wrong_ssh_file_content_from_env():
    assert _ENCORD_SSH_KEY_FILE not in os.environ
    os.environ[_ENCORD_SSH_KEY] = "Some random content."
    with pytest.raises(expected_exception=ValueError) as excinfo:
        user_client = EncordUserClient.create_with_ssh_private_key()
