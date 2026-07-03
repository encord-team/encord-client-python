import uuid
from datetime import datetime, timezone

import pytest

from encord.group import Group
from encord.orm.group import Group as OrmGroup


def _make_group() -> Group:
    orm_group = OrmGroup(
        group_hash=uuid.uuid4(),
        name="My Group",
        description="desc",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    # The client is unused: update_group validates its arguments before making any request.
    return Group(None, orm_group)  # type: ignore[arg-type]


def test_update_group_requires_at_least_one_field() -> None:
    with pytest.raises(ValueError):
        _make_group().update_group()
