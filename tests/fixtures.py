from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from encord import EncordUserClient, Project
from encord.client import EncordClientProject
from encord.http.querier import Querier
from encord.ontology import Ontology
from encord.orm.ontology import Ontology as OrmOntology
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
def ontology() -> Ontology:
    return Ontology(None, OrmOntology.from_dict(ONTOLOGY_BLURB), None)


@pytest.fixture
def user_client() -> EncordUserClient:
    return EncordUserClient.create_with_ssh_private_key(DUMMY_PRIVATE_KEY)


@pytest.fixture
@patch.object(EncordClientProject, "get_project")
@patch.object(Querier, "basic_getter")
def project(querier_mock: Querier, client_project_mock, user_client: EncordUserClient, ontology: Ontology) -> Project:
    querier_mock.return_value = OrmOntology.from_dict(ONTOLOGY_BLURB)

    client_project_mock.return_value = OrmProject(
        {"ontology_hash": "dummy-ontology-hash", "project_hash": "dummy-project-hash"}
    )

    return user_client.get_project("dummy-project-hash")
