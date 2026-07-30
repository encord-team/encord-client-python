import uuid
from unittest.mock import MagicMock

from encord.client import EncordClientDataset
from encord.http.v2.payloads import Page
from encord.orm.dataset import DatasetUser, DatasetUserRole, _PublicDatasetUser


def test_list_users_maps_wire_users_to_dataset_users() -> None:
    client = object.__new__(EncordClientDataset)
    client._api_client = MagicMock()
    dataset_hash = uuid.uuid4()
    client._api_client.get.return_value = Page[_PublicDatasetUser](
        results=[
            _PublicDatasetUser(
                dataset_uuid=dataset_hash,
                user_email="user@example.com",
                user_role=DatasetUserRole.USER,
            )
        ]
    )

    users = list(client.list_users(dataset_hash))

    client._api_client.get.assert_called_once_with(
        f"datasets/{dataset_hash}/users", params=None, result_type=Page[_PublicDatasetUser]
    )
    assert users == [
        DatasetUser(
            user_email="user@example.com",
            user_role=DatasetUserRole.USER,
            dataset_hash=str(dataset_hash),
        )
    ]


def test_public_dataset_user_parses_wire_format() -> None:
    dataset_uuid = uuid.uuid4()
    user = _PublicDatasetUser.from_dict(
        {"datasetUuid": str(dataset_uuid), "userEmail": "user@example.com", "userRole": 0}
    )
    assert user.dataset_uuid == dataset_uuid
    assert user.user_email == "user@example.com"
    assert user.user_role == DatasetUserRole.ADMIN
