import uuid
from datetime import datetime
from unittest.mock import MagicMock

from encord.client import EncordClientDataset
from encord.dataset import Dataset
from encord.http.v2.payloads import Page
from encord.ontology import Ontology
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset import DatasetUserRole
from encord.orm.storage import StorageFolder, StorageUserRole
from encord.storage import StorageFolder as SdkStorageFolder
from encord.utilities.ontology_user import OntologyUserRole


def test_dataset_users_use_v2_api() -> None:
    dataset_hash = uuid.uuid4()
    api_client = MagicMock()
    api_client.post.return_value = Page(results=[])
    querier = MagicMock(resource_id=dataset_hash)
    client = EncordClientDataset(querier=querier, config=MagicMock(), api_client=api_client)
    dataset = Dataset(client, MagicMock(spec=OrmDataset, dataset_hash=str(dataset_hash)))

    dataset.add_users(["user@example.com"], DatasetUserRole.USER)
    list(dataset.list_users())
    dataset.remove_users(["user@example.com"])

    api_client.post.assert_called_once()
    assert api_client.post.call_args.args[0] == f"datasets/{dataset_hash}/users"
    api_client.get_paged_iterator.assert_called_once()
    assert api_client.get_paged_iterator.call_args.args[0] == f"datasets/{dataset_hash}/users"
    api_client.delete.assert_called_once()
    assert api_client.delete.call_args.args[0] == f"datasets/{dataset_hash}/users"


def test_ontology_users_use_v2_api(ontology: Ontology) -> None:
    ontology.api_client.get.return_value = Page(results=[])

    ontology.add_users(["user@example.com"], OntologyUserRole.USER)
    list(ontology.list_users())
    ontology.remove_users(["user@example.com"])

    ontology.api_client.post.assert_called_once()
    assert ontology.api_client.post.call_args.args[0] == f"ontologies/{ontology.ontology_hash}/users"
    ontology.api_client.get.assert_called_once()
    assert ontology.api_client.get.call_args.args[0] == f"ontologies/{ontology.ontology_hash}/users"
    ontology.api_client.delete.assert_called_once()
    assert ontology.api_client.delete.call_args.args[0] == f"ontologies/{ontology.ontology_hash}/users"


def test_storage_folder_users_use_v2_api() -> None:
    folder_uuid = uuid.uuid4()
    api_client = MagicMock()
    api_client.get.return_value = Page(results=[])
    folder = SdkStorageFolder(
        api_client,
        StorageFolder(
            uuid=folder_uuid,
            parent=None,
            name="folder",
            description="",
            client_metadata=None,
            owner="owner@example.com",
            created_at=datetime.now(),
            last_edited_at=datetime.now(),
            user_role=StorageUserRole.ADMIN,
            synced_dataset_hash=None,
            path_to_root=[],
        ),
    )

    folder.add_users(["user@example.com"], StorageUserRole.USER)
    list(folder.list_users())
    folder.remove_users(["user@example.com"])

    api_client.post.assert_called_once()
    assert api_client.post.call_args.args[0] == f"/storage/folders/{folder_uuid}/users"
    api_client.get.assert_called_once()
    assert api_client.get.call_args.args[0] == f"/storage/folders/{folder_uuid}/users"
    api_client.delete.assert_called_once()
    assert api_client.delete.call_args.args[0] == f"/storage/folders/{folder_uuid}/users"
