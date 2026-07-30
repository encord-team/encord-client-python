import uuid
from unittest.mock import MagicMock

from encord.client import EncordClientDataset, EncordClientProject
from encord.orm.dataset import RemoveDatasetUsersPayload
from encord.orm.project import RemoveProjectUsersPayload


def test_project_remove_users_posts_bulk_delete() -> None:
    client = object.__new__(EncordClientProject)
    client._api_client = MagicMock()
    project_hash = uuid.uuid4()

    client.remove_users(project_hash, ["user@example.com"])

    client._api_client.post.assert_called_once_with(
        f"projects/{project_hash}/users/bulk-delete",
        params=None,
        payload=RemoveProjectUsersPayload(user_emails=["user@example.com"]),
        result_type=None,
    )


def test_dataset_remove_users_posts_bulk_delete() -> None:
    client = object.__new__(EncordClientDataset)
    client._api_client = MagicMock()
    dataset_hash = uuid.uuid4()

    client.remove_users(dataset_hash, ["user@example.com"])

    client._api_client.post.assert_called_once_with(
        f"datasets/{dataset_hash}/users/bulk-delete",
        params=None,
        payload=RemoveDatasetUsersPayload(user_emails=["user@example.com"]),
        result_type=None,
    )


def test_remove_users_payloads_serialise_to_camel_case() -> None:
    assert RemoveProjectUsersPayload(user_emails=["a@b.com"]).to_dict() == {"userEmails": ["a@b.com"]}
    assert RemoveDatasetUsersPayload(user_emails=["a@b.com"]).to_dict() == {"userEmails": ["a@b.com"]}
