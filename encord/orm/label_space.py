from typing import Literal

from pydantic import BaseModel

from encord.constants.enums import DataType
from encord.objects.space import SpaceType


class SpaceInfo(BaseModel):
    space_type: SpaceType
    data_type: DataType
