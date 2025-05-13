from __future__ import annotations

from dataclasses import dataclass
from enum import auto
from typing import List, Literal, Union
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class _IssueAnchorType(CamelStrEnum):
    DATA_UNIT = auto()
    FRAME = auto()
    FRAME_COORDINATE = auto()


class _FileIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.DATA_UNIT] = _IssueAnchorType.DATA_UNIT
    project_uuid: UUID
    data_uuid: UUID


class _FrameIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.FRAME] = _IssueAnchorType.FRAME
    project_uuid: UUID
    data_uuid: UUID
    frame_index: int


class _CoordinateIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.FRAME_COORDINATE] = _IssueAnchorType.FRAME_COORDINATE
    project_uuid: UUID
    data_uuid: UUID
    frame_index: int
    x: float
    y: float


_IssueAnchor = Union[_FileIssueAnchor, _FrameIssueAnchor, _CoordinateIssueAnchor]


class _NewIssue(BaseDTO):
    anchor: _IssueAnchor
    comment: str
    issue_tags: List[str]


class _CreateIssuesPayload(BaseDTO):
    issues: List[_NewIssue]


@dataclass
class TaskIssueClient:
    api_client: ApiClient
    project_uuid: UUID
    data_uuid: UUID

    def add_file_issue(self, comment: str, issue_tags: List[str]) -> None:
        self._add_issue(
            anchor=_FileIssueAnchor(
                project_uuid=self.project_uuid,
                data_uuid=self.data_uuid,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_frame_issue(self, frame_index: int, comment: str, issue_tags: List[str]) -> None:
        self._add_issue(
            anchor=_FrameIssueAnchor(project_uuid=self.project_uuid, data_uuid=self.data_uuid, frame_index=frame_index),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_coordinate_issue(self, frame_index: int, x: float, y: float, comment: str, issue_tags: List[str]) -> None:
        self._add_issue(
            anchor=_CoordinateIssueAnchor(
                project_uuid=self.project_uuid,
                data_uuid=self.data_uuid,
                frame_index=frame_index,
                x=x,
                y=y,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def _add_issue(self, anchor: _IssueAnchor, comment: str, issue_tags: List[str]) -> None:
        self.api_client.post(
            path=f"/comment-threads",
            params=None,
            payload=_CreateIssuesPayload(
                issues=[
                    _NewIssue(
                        anchor=anchor,
                        comment=comment,
                        issue_tags=issue_tags,
                    )
                ]
            ),
            result_type=None,
        )
