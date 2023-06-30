from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from encord import EncordUserClient
from encord.client import EncordClientProject
from encord.objects.ontology_labels_impl import Ontology as OrmOntology
from encord.ontology import Ontology
from encord.orm.project import Project as OrmProject
from tests.test_data.ontology_blurb import ONTOLOGY_BLURB

DUMMY_PRIVATE_KEY = (
    Ed25519PrivateKey.generate()
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
)


@pytest.fixture
def ontology():
    ontology = Ontology(None, None, OrmOntology.from_dict(ONTOLOGY_BLURB))
    return ontology


@pytest.fixture
def user_client():
    client = EncordUserClient.create_with_ssh_private_key(DUMMY_PRIVATE_KEY)
    return client


@pytest.fixture
@patch.object(EncordClientProject, "get_project")
def project(client_project_mock, user_client: EncordUserClient, ontology: Ontology):
    client_project_mock.return_value = OrmProject(
        {"ontology_hash": "dummy-ontology-hash", "project_hash": "dummy-project-hash"}
    )
    project = user_client.get_project("dummy-project-hash")
    project._ontology = ontology
    return project