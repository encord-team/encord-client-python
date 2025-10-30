from enum import Enum
from typing import Optional

from encord.orm.base_dto import BaseDTO


class ActiveProjectMode(Enum):
    DATA = "data"
    LABEL = "label"
    METRIC = "metric"
    ADVANCED = "advanced"


class ActiveProjectImportPayload(BaseDTO):
    project_mode: ActiveProjectMode
    video_sampling_rate: Optional[float] = None
