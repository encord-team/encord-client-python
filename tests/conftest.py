import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from encord import EncordUserClient, Project
from encord.client import EncordClientProject
from encord.ontology import Ontology
from encord.orm.ontology import Ontology as OrmOntology
from encord.orm.project import ProjectDTO, ProjectStatus, ProjectType
from encord.utilities.ontology_user import OntologyUserRole
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.test_data.ontology_blurb import ONTOLOGY_BLURB

PRIVATE_KEY = Ed25519PrivateKey.generate()

PRIVATE_KEY_PEM = PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.OpenSSH,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")


@pytest.fixture
def ontology() -> Ontology:
    return Ontology(OrmOntology.from_dict(ONTOLOGY_BLURB), MagicMock())


@pytest.fixture
def all_types_ontology() -> Ontology:
    orm_ontology = OrmOntology(
        title="All Types ontology",
        structure=all_types_structure,
        ontology_hash="all-types-ontology-hash",
        created_at=datetime(2020, 5, 17),
        last_edited_at=datetime(2020, 5, 17),
        description="All Types ontology fixture for testing",
        user_role=OntologyUserRole.ADMIN,
    )

    return Ontology(orm_ontology, MagicMock())


@pytest.fixture
def user_client() -> EncordUserClient:
    return EncordUserClient.create_with_ssh_private_key(PRIVATE_KEY_PEM)


@pytest.fixture
@patch.object(EncordClientProject, "get_project_v2")
@patch.object(EncordUserClient, "get_ontology")
def project(
    client_ontology_mock: MagicMock,
    client_project_mock: MagicMock,
    user_client: EncordUserClient,
    ontology: Ontology,
) -> Project:
    client_ontology_mock.return_value = ontology

    client_project_mock.return_value = ProjectDTO(
        project_hash=uuid.uuid4(),
        project_type=ProjectType.MANUAL_QA,
        status=ProjectStatus.IN_PROGRESS,
        title="Dummy project",
        description="",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        ontology_hash="dummy-ontology-hash",
        editor_ontology=ONTOLOGY_BLURB,
        workflow=None,
    )

    return user_client.get_project("dummy-project-hash")
