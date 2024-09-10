import json
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Generic, Literal, Type, TypeVar

from pydantic import BaseModel, Field, PrivateAttr, ValidationError, root_validator, validator
from pydantic.generics import GenericModel
from pydantic.json import pydantic_encoder
from typing_extensions import Self

from encord.common.time_parser import parse_datetime
from encord.common.utils import snake_to_camel
from encord.exceptions import EncordException
from encord.orm.base_dto.base_dto_interface import BaseDTOInterface, T


class BaseDTO(BaseDTOInterface, BaseModel):
    class Config:
        ignore_extra = True
        alias_generator = snake_to_camel
        allow_population_by_field_name = True

    @validator("*", pre=True)
    def parse_datetime(cls, value, field):
        if isinstance(value, str) and issubclass(field.type_, datetime):
            return parse_datetime(value)
        return value

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.parse_obj(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        # Pydantic v1 is missing the 'model_dump()' method, the below is suboptimal but works
        return json.loads(self.json(by_alias=by_alias, exclude_none=exclude_none))  # type: ignore[attr-defined]


DataT = TypeVar("DataT")


class GenericBaseDTO(BaseDTOInterface, GenericModel):
    class Config:
        ignore_extra = True
        alias_generator = snake_to_camel
        allow_population_by_field_name = True

    @validator("*", pre=True)
    def parse_datetime(cls, value, field):
        if isinstance(value, str) and issubclass(field.type_, datetime):
            return parse_datetime(value)
        return value

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.parse_obj(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        # Pydantic v1 is missing the 'model_dump()' method, the below is suboptimal but works
        return json.loads(self.json(by_alias=by_alias, exclude_none=exclude_none))  # type: ignore[attr-defined]


def dto_validator(mode: Literal["before", "after"] = "before") -> Callable:
    def decorator(func: Callable) -> Callable:
        return root_validator(pre=(mode == "before"))(func)  # type: ignore

    return decorator


RootType = TypeVar("RootType")


class RootModelDTO(GenericModel, Generic[RootType]):
    __root__: RootType

    def __init__(cls, *args, **kwargs):
        if "__root__" in kwargs:
            super().__init__(*args, **kwargs)
        else:
            root = args[0] if len(args) > 0 else kwargs.pop("root", None)
            super().__init__(__root__=root)

    @property
    def root(self) -> Type:
        return self.__root__  # type: ignore[return-value]

    @classmethod
    def model_validate(cls, *args, **kwargs) -> Self:
        return cls.validate(*args, **kwargs)

    def model_dump(self, *args, **kwargs) -> dict:
        mode = kwargs.pop("mode")
        value = self.dict(*args, **kwargs)
        raw_value = value.get("__root__")
        if mode == "json":
            return json.loads(json.dumps(raw_value, default=pydantic_encoder))
        else:
            return raw_value  # type: ignore[return-value]
