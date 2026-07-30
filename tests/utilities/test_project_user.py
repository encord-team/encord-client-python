from unittest.mock import MagicMock
from uuid import UUID

import pytest

from encord.client import EncordClientProject
from encord.orm.project import ProjectUserResponse
from encord.utilities.project_user import ProjectUser, ProjectUserRole


def test_project_user_role_viewer() -> None:
    assert ProjectUserRole.VIEWER.value == 5
    assert ProjectUserRole(5) == ProjectUserRole.VIEWER


def test_project_user_role_unknown_fallback() -> None:
    assert ProjectUserRole(99) == ProjectUserRole.UNKNOWN
    assert ProjectUserRole(99).value == -99


def test_project_user_deserializes_viewer_role() -> None:
    project_user = ProjectUser.from_dict(
        {
            "user_email": "viewer@example.com",
            "user_role": 5,
            "project_hash": "project-hash",
        }
    )

    assert project_user.user_role == ProjectUserRole.VIEWER
    assert project_user.to_dict() == {
        "userEmail": "viewer@example.com",
        "userRole": 5,
        "projectHash": "project-hash",
    }


def test_project_user_response_deserializes_unknown_role() -> None:
    project_user = ProjectUserResponse.from_dict(
        {
            "user_email": "unknown@example.com",
            "user_role": 99,
        }
    )

    assert project_user.user_role == ProjectUserRole.UNKNOWN
    assert project_user.to_dict() == {
        "userEmail": "unknown@example.com",
        "userRole": -99,
    }


def test_add_users_rejects_unknown_project_user_role() -> None:
    client = EncordClientProject(MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ValueError, match="ProjectUserRole.UNKNOWN cannot be used"):
        client.add_users(["user@example.com"], ProjectUserRole.UNKNOWN)


def test_add_groups_rejects_unknown_project_user_role() -> None:
    client = EncordClientProject(MagicMock(), MagicMock(), MagicMock())
    project_hash = UUID("12345678-1234-5678-1234-567812345678")
    group_hash = UUID("87654321-4321-8765-4321-876543218765")

    with pytest.raises(ValueError, match="ProjectUserRole.UNKNOWN cannot be used"):
        client.add_groups(project_hash, [group_hash], ProjectUserRole.UNKNOWN)
