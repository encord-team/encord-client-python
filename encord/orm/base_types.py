from enum import Enum

from encord.common.utils import snake_to_camel


class CamelStrEnum(str, Enum):
    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values) -> str:  # type: ignore
        return snake_to_camel(name)


class BeEnum(str, Enum):
    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values) -> str:  # type: ignore
        return name.upper()
