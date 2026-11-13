from datetime import datetime
from typing import Any, Callable, Dict, Literal, Type, TypeVar, get_origin

from pydantic import (
    BaseModel,
    ConfigDict,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic import (
    Field as Field,
)
from pydantic import (
    PrivateAttr as PrivateAttr,
)

from encord.common.time_parser import parse_datetime
from encord.common.utils import snake_to_camel
from encord.exceptions import EncordException
from encord.orm.base_dto.base_dto_interface import BaseDTOInterface as BaseDTOInterface
from encord.orm.base_dto.base_dto_interface import T


class BaseDTO(BaseDTOInterface, BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        alias_generator=snake_to_camel,
        protected_namespaces=(),  # otherwise clash with model_ prefixes
    )

    @field_validator("*", mode="before")
    def parse_datetime(cls, value, info):
        annotation = cls.model_fields[info.field_name].annotation
        origin = get_origin(annotation)
        # Only fields annotated as plain `datetime` use the custom parser. Wrapped types such as
        # Optional[datetime] or List[datetime] fall back to pydantic's own datetime parsing.
        if (
            origin is None
            and isinstance(annotation, type)
            and issubclass(annotation, datetime)
            and isinstance(value, str)
        ):
            return parse_datetime(value)
        return value

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.model_validate(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none, mode="json")


class BaseDTOWithExtra(BaseDTO):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=snake_to_camel,
        protected_namespaces=(),  # otherwise clash with model_ prefixes
    )

    def get_extra(self, field_name: str):
        return self.model_extra.get(field_name) if self.model_extra else None


DataT = TypeVar("DataT")


class GenericBaseDTO(BaseDTOInterface, BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        alias_generator=snake_to_camel,
        protected_namespaces=(),  # otherwise clash with model_ prefixes
    )

    @field_validator("*", mode="before")
    def parse_datetime(cls, value, info):
        annotation = cls.model_fields[info.field_name].annotation
        origin = get_origin(annotation)
        # Only fields annotated as plain `datetime` use the custom parser. Wrapped types such as
        # Optional[datetime] or List[datetime] fall back to pydantic's own datetime parsing.
        if (
            origin is None
            and isinstance(annotation, type)
            and issubclass(annotation, datetime)
            and isinstance(value, str)
        ):
            return parse_datetime(value)
        return value

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        try:
            return cls.model_validate(d)  # type: ignore[attr-defined]
        except ValidationError as e:
            raise EncordException(message=str(e)) from e

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none, mode="json")


def dto_validator(mode: Literal["before", "after"] = "before") -> Callable:
    def decorator(func: Callable) -> Callable:
        return model_validator(mode=mode)(func)  # type: ignore

    return decorator


RootModelDTO = RootModel
