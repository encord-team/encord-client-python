from typing import Union
from uuid import UUID


def convert_to_uuid(uuid: Union[UUID, str]) -> UUID:
    if not isinstance(uuid, UUID):
        uuid = UUID(uuid)
    return uuid
