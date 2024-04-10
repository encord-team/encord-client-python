from uuid import UUID

from encord.orm.base_dto import BaseDTO


class WrappedUUID(BaseDTO):
    __root__: UUID
