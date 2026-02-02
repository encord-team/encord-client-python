from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import auto
from typing import Annotated, Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO, Field


class IssueAnchorType(CamelStrEnum):
    DATA_UNIT = auto()
    FRAME = auto()
    FRAME_COORDINATE = auto()
    FRAME_RANGE = auto()
    ANNOTATION = auto()


class _FileIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.DATA_UNIT] = IssueAnchorType.DATA_UNIT
    data_uuid: UUID


class _FrameIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME] = IssueAnchorType.FRAME
    data_uuid: UUID
    frame_index: int


class _CoordinateIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME_COORDINATE] = IssueAnchorType.FRAME_COORDINATE
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


class GetIssuesParam(BaseDTO):
    data_unit_id: UUID
    page_token: Optional[str] = None


class IssueComment(BaseDTO):
    content: str
    author_email: str
    created_at: datetime


class IssueTag(BaseDTO):
    name: str


class IssueResolution(BaseDTO):
    is_resolved: bool
    created_at: datetime
    actor_email: Optional[str]


class _BaseIssue(BaseDTO):
    type: IssueAnchorType
    data_uuid: UUID
    comments: List[IssueComment]
    tags: List[IssueTag]
    resolution_history: List[IssueResolution]


class FileIssue(_BaseIssue):
    type: Literal[IssueAnchorType.DATA_UNIT] = IssueAnchorType.DATA_UNIT


class FrameIssue(_BaseIssue):
    type: Literal[IssueAnchorType.FRAME] = IssueAnchorType.FRAME
    frame_index: int


class _IssueCoordinate(BaseDTO):
    x: float
    y: float


class CoordinateIssue(_BaseIssue):
    type: Literal[IssueAnchorType.FRAME_COORDINATE] = IssueAnchorType.FRAME_COORDINATE
    frame_index: int
    coordinate: _IssueCoordinate


class _IssueFrameRange(BaseDTO):
    """Represents a range of frames [start, end] inclusive"""

    start: int
    end: int


class FrameRangeIssue(_BaseIssue):
    """Issue anchored to a range of frames"""

    type: Literal[IssueAnchorType.FRAME_RANGE] = IssueAnchorType.FRAME_RANGE
    frame_ranges: List[_IssueFrameRange]


class AnnotationIssue(_BaseIssue):
    """Issue anchored to a specific annotation (label rejection or annotation feedback)"""

    type: Literal[IssueAnchorType.ANNOTATION] = IssueAnchorType.ANNOTATION
    annotation_id: str


Issue = Annotated[
    Union[FileIssue, FrameIssue, CoordinateIssue, FrameRangeIssue, AnnotationIssue],
    Field(discriminator="type"),
]


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

    def get_issues(self, *, project_uuid: UUID, data_uuid: UUID) -> Iterable[Issue]:
        # Issue is a Pydantic discriminated union; type checker doesn't recognize it as Type[T]
        # but it works correctly at runtime
        return self._api_client.get_paged_iterator(
            path=f"/projects/{project_uuid}/issues",
            params=GetIssuesParam(data_unit_id=data_uuid),
            result_type=Issue,  # type: ignore[arg-type]
        )


class TaskIssues:
    def __init__(self, api_client: ApiClient, project_uuid: UUID, data_uuid: UUID):
        self._issue_client = _IssueClient(api_client=api_client)
        self._project_uuid = project_uuid
        self._data_uuid = data_uuid

    def list(self) -> Iterable[Issue]:
        """Lists all issues (comment threads) for this task.

        Returns an iterator of issues anchored to different parts of the data unit:
        - FileIssue: Issues anchored to the entire data unit
        - FrameIssue: Issues anchored to a specific frame
        - CoordinateIssue: Issues anchored to specific coordinates on a frame
        - FrameRangeIssue: Issues anchored to a range of frames
        - AnnotationIssue: Issues anchored to a specific annotation

        Each issue includes comments, tags, and resolution history.

        Returns:
            Iterable[Issue]: An iterator of Issue objects (discriminated union of all issue types).

        Example:
            >>> for issue in task.issues.list():
            ...     if isinstance(issue, FileIssue):
            ...         print(f"File issue: {issue.comments[0].content}")
            ...     elif isinstance(issue, FrameIssue):
            ...         print(f"Frame {issue.frame_index}: {issue.comments[0].content}")
        """
        return self._issue_client.get_issues(project_uuid=self._project_uuid, data_uuid=self._data_uuid)

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
