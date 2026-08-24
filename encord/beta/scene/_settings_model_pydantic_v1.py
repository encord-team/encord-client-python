import json
from typing import Any, Dict

from pydantic import BaseModel, Field

from encord.common.utils import HEX_COLOR_PATTERN, snake_to_camel


def hex_color_field() -> Any:
    field_kwargs: Dict[str, Any] = {"regex": HEX_COLOR_PATTERN}
    return Field(description="Colour used to render the radius indicator.", **field_kwargs)


class SceneSettingsModel(BaseModel):
    class Config:
        alias_generator = snake_to_camel
        allow_population_by_field_name = True
        extra = "forbid"

    def to_dict(self, by_alias: bool = True, exclude_none: bool = True) -> Dict[str, Any]:
        return json.loads(self.json(by_alias=by_alias, exclude_none=exclude_none))
