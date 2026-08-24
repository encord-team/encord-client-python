from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from encord.common.utils import HEX_COLOR_PATTERN, snake_to_camel


def hex_color_field() -> Any:
    return Field(description="Colour used to render the radius indicator.", pattern=HEX_COLOR_PATTERN)


class SceneSettingsModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=snake_to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    def to_dict(self, by_alias: bool = True, exclude_none: bool = True) -> Dict[str, Any]:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none, mode="json")
