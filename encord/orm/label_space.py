from typing import Literal

from pydantic import BaseModel

from encord.constants.enums import DataType


class SpaceInfo(BaseModel):
    space_type: Literal["data-group-child"]
    data_type: DataType