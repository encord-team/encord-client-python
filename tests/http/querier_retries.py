from unittest import mock

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from requests.exceptions import ConnectionError

from encord.configs import SshConfig, UserConfig
from encord.constants.string_constants import TYPE_PROJECT
from encord.http.querier import Querier
from encord.orm.ontology import Ontology as OrmOntology
from tests.fixtures import ontology, project, user_client

assert project and user_client and ontology  # Silence "unused import" warning


@pytest.fixture()
def querier() -> Querier:
    PRIVATE_KEY = Ed25519PrivateKey.generate()
    user_config = UserConfig(PRIVATE_KEY)

    config = SshConfig(user_config, resource_type=TYPE_PROJECT, resource_id="project_hash")
    return Querier(config)


# @patch.object(Session, "send")
# def test_deserialise_payload_raises_on_wrong_payload(send: MagicMock, querier: Querier):
def test_deserialise_payload_raises_on_wrong_payload(querier: Querier):
    with mock.patch("requests.adapters.HTTPAdapter.send") as mock_send:
        mock_send.side_effect = ConnectionError(mock.MagicMock(), "Failed to establish a new connection")

        try:
            querier.basic_getter(OrmOntology, "xxx")
        except Exception:
            print("xxx")
