from __future__ import annotations

from enum import auto
from typing import Literal

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class IssueAnchorType(CamelStrEnum):
    DATA_UNIT = auto()
    FRAME = auto()
    FRAME_COORDINATE = auto()


class DataUnitIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.DATA_UNIT] = IssueAnchorType.DATA_UNIT


class FrameIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME] = IssueAnchorType.FRAME
    frame_index: int


class FrameCoordinateIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME_COORDINATE] = IssueAnchorType.FRAME_COORDINATE
    frame_index: int
    x: float
    y: float
