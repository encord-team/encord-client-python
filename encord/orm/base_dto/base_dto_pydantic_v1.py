from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic.generics import GenericModel

from encord.exceptions import EncordException
from encord.objects.utils import _snake_to_camel
from encord.orm.base_dto.base_dto_interface import BaseDTOInterface, T


class BaseDTO(BaseDTOInterface, BaseModel):
    class Config:
        allow_extra = True
        alias_generator = _snake_to_camel
        allow_population_by_field_name = True

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.parse_obj(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self) -> Dict[str, Any]:
        return self.dict(by_alias=True)  # type: ignore[attr-defined]


DataT = TypeVar("DataT")


class GenericBaseDTO(BaseDTOInterface, GenericModel):
    class Config:
        allow_extra = True
        alias_generator = _snake_to_camel
        allow_population_by_field_name = True

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.parse_obj(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self) -> Dict[str, Any]:
        return self.dict(by_alias=True)  # type: ignore[attr-defined]
