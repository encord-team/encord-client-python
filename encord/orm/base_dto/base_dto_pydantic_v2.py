from typing import Any, Dict, Type, TypeVar

# TODO: invent some dependency version dependent type checking to get rid of this ignore
from pydantic import (  # type: ignore[attr-defined]
    BaseModel,
    ConfigDict,  # type: ignore[attr-defined]
    ValidationError,
)

from encord.common.utils import snake_to_camel
from encord.exceptions import EncordException
from encord.orm.base_dto.base_dto_interface import BaseDTOInterface, T


class BaseDTO(BaseDTOInterface, BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=snake_to_camel)

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.model_validate(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none)  # type: ignore[attr-defined]


DataT = TypeVar("DataT")


class GenericBaseDTO(BaseDTOInterface, BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=snake_to_camel)

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.model_validate(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none)  # type: ignore[attr-defined]
