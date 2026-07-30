import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from encord.http.v2.payloads import Page
from encord.orm.organisation_user import AddOrganisationUserPayload, OrganisationUser
from encord.user_client import EncordUserClient


@patch.object(EncordUserClient, "__init__", lambda self, config, querier: None)
def test_add_organisation_user_posts_expected_payload() -> None:
    user_client = EncordUserClient(MagicMock(), MagicMock())  # type: ignore[arg-type]
    user_client._api_client = MagicMock()

    user_client.add_organisation_user(
        "user@example.com",
        role_mnemonic_name="MEMBER",
        member_type="internal",
    )

    user_client._api_client.post.assert_called_once_with(
        "organisation/users",
        params=None,
        payload=AddOrganisationUserPayload(
            email="user@example.com",
            role_mnemonic_name="MEMBER",
            member_type="internal",
        ),
        result_type=None,
    )


def test_add_organisation_user_payload_serialisation() -> None:
    payload = AddOrganisationUserPayload(email="user@example.com", role_mnemonic_name="MEMBER", member_type="external")
    assert payload.to_dict() == {
        "email": "user@example.com",
        "roleMnemonicName": "MEMBER",
        "memberType": "external",
    }


@patch.object(EncordUserClient, "__init__", lambda self, config, querier: None)
def test_remove_organisation_user_deletes_url_encoded_email() -> None:
    user_client = EncordUserClient(MagicMock(), MagicMock())  # type: ignore[arg-type]
    user_client._api_client = MagicMock()

    user_client.remove_organisation_user("user+alias@example.com")

    user_client._api_client.delete.assert_called_once_with(
        "organisation/users/user%2Balias%40example.com",
        params=None,
        result_type=None,
    )


@patch.object(EncordUserClient, "__init__", lambda self, config, querier: None)
def test_list_organisation_users_returns_page_results() -> None:
    user_client = EncordUserClient(MagicMock(), MagicMock())  # type: ignore[arg-type]
    user_client._api_client = MagicMock()
    org_user = OrganisationUser(
        email="user@example.com",
        role_mnemonic_name="MEMBER",
        role_uuid=uuid.uuid4(),
        member_type="internal",
        created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        last_edited_at=datetime(2026, 7, 2, tzinfo=timezone.utc),
    )
    user_client._api_client.get.return_value = Page[OrganisationUser](results=[org_user])

    users = user_client.list_organisation_users()

    user_client._api_client.get.assert_called_once_with(
        "organisation/users",
        params=None,
        result_type=Page[OrganisationUser],
    )
    assert users == [org_user]


def test_organisation_user_parses_wire_format() -> None:
    role_uuid = uuid.uuid4()
    user = OrganisationUser.from_dict(
        {
            "email": "user@example.com",
            "roleMnemonicName": "SOME_FUTURE_ROLE",
            "roleUuid": str(role_uuid),
            "memberType": "workforce",
            "createdAt": "2026-07-01T00:00:00+00:00",
            "lastEditedAt": "2026-07-02T00:00:00+00:00",
        }
    )
    assert user.email == "user@example.com"
    assert user.role_mnemonic_name == "SOME_FUTURE_ROLE"
    assert user.role_uuid == role_uuid
    assert user.member_type == "workforce"
