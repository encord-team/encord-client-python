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
    data_uuid: UUID


class _FrameIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.FRAME] = _IssueAnchorType.FRAME
    data_uuid: UUID
    frame_index: int


class _CoordinateIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.FRAME_COORDINATE] = _IssueAnchorType.FRAME_COORDINATE
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


class _IssueClient:
    def __init__(self, api_client: ApiClient) -> None:
        self._api_client = api_client

    def add_issue(self, project_uuid: UUID, anchor: _IssueAnchor, comment: str, issue_tags: List[str]) -> None:
        self._api_client.post(
            path=f"/projects/{project_uuid}/issues",
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


class TaskIssues:
    def __init__(self, api_client: ApiClient, project_uuid: UUID, data_uuid: UUID):
        self._issue_client = _IssueClient(api_client=api_client)
        self._project_uuid = project_uuid
        self._data_uuid = data_uuid

    def add_file_issue(self, comment: str, issue_tags: List[str]) -> None:
        """Adds a file issue.

        Args:
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_FileIssueAnchor(
                data_uuid=self._data_uuid,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_frame_issue(self, frame_index: int, comment: str, issue_tags: List[str]) -> None:
        """Adds a frame issue.

        Args:
            frame_index (int): The index of the frame to add the issue to.
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_FrameIssueAnchor(data_uuid=self._data_uuid, frame_index=frame_index),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_coordinate_issue(self, frame_index: int, x: float, y: float, comment: str, issue_tags: List[str]) -> None:
        """Adds a issue pinned to a coordinate.

        Args:
            frame_index (int): The index of the frame to add the issue to.
            x (float): The x coordinate of the issue.
            y (float): The y coordinate of the issue.
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_CoordinateIssueAnchor(
                data_uuid=self._data_uuid,
                frame_index=frame_index,
                x=x,
                y=y,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )
