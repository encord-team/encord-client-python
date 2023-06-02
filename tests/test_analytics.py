import pytest

from encord import EncordUserClient


@pytest.mark.xfail
def test_project_collaborator_timers(user_client: EncordUserClient):
    project = user_client.get_project(project_hash="abc")

    assert project is not None
