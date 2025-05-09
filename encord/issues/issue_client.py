from __future__ import annotations

from dataclasses import dataclass
from enum import auto
from typing import List, Literal, Union, final
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class _IssueAnchorType(CamelStrEnum):
    DATA_UNIT = auto()
    FRAME = auto()
    FRAME_COORDINATE = auto()


@final
class _ProjectDataUnitIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.DATA_UNIT] = _IssueAnchorType.DATA_UNIT
    project_hash: UUID
    data_hash: UUID


@final
class _ProjectDataUnitFrameIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.FRAME] = _IssueAnchorType.FRAME
    project_hash: UUID
    data_hash: UUID


@final
class _ProjectDataUnitFrameCoordinateIssueAnchor(BaseDTO):
    type: Literal[_IssueAnchorType.FRAME_COORDINATE] = _IssueAnchorType.FRAME_COORDINATE
    frame_index: int
    x: float
    y: float
    project_hash: UUID
    data_hash: UUID


_IssueAnchor = Union[
    _ProjectDataUnitIssueAnchor, _ProjectDataUnitFrameIssueAnchor, _ProjectDataUnitFrameCoordinateIssueAnchor
]


@final
class _NewIssueInProjectDataUnit(BaseDTO):
    anchor: _IssueAnchor
    comment: str
    issue_tags: List[str]


class _CreateIssuesPayload(BaseDTO):
    issues: List[_NewIssueInProjectDataUnit]


@dataclass
class _IssueClient:
    api_client: ApiClient

    def add_file_issue(self, *, project_hash: UUID, data_hash: UUID, comment: str, issue_tags: List[str]):
        self._add_issue(
            anchor=_ProjectDataUnitIssueAnchor(
                project_hash=project_hash,
                data_hash=data_hash,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_frame_issue(
        self, *, project_hash: UUID, data_hash: UUID, frame_index: int, comment: str, issue_tags: List[str]
    ):
        self._add_issue(
            anchor=_ProjectDataUnitFrameIssueAnchor(
                project_hash=project_hash, data_hash=data_hash, frame_index=frame_index
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
                    _NewIssueInProjectDataUnit(
                        anchor=anchor,
                        comment=comment,
                        issue_tags=issue_tags,
                    )
                ]
            ),
            result_type=None,
        )


class TaskIssueClient:
    def __init__(self, api_client: ApiClient, project_hash: UUID, data_hash: UUID):
        self._project_hash = project_hash
        self._data_hash = data_hash
        self._client = _IssueClient(api_client)

    def add_file_issue(self, comment: str, issue_tags: List[str]):
        self._client.add_file_issue(
            project_hash=self._project_hash, data_hash=self._data_hash, comment=comment, issue_tags=issue_tags
        )

    def add_frame_issue(self, frame_index: int, comment: str, issue_tags: List[str]):
        self._client.add_frame_issue(
            project_hash=self._project_hash,
            data_hash=self._data_hash,
            frame_index=frame_index,
            comment=comment,
            issue_tags=issue_tags,
        )


class ProjectIssueClient:
    def __init__(self, api_client: ApiClient, project_hash: UUID):
        self._project_hash = project_hash
        self._client = _IssueClient(api_client)

    def add_file_issue(self, data_hash: UUID, comment: str, issue_tags: List[str]):
        self._client.add_file_issue(
            project_hash=self._project_hash, data_hash=data_hash, comment=comment, issue_tags=issue_tags
        )

    def add_frame_issue(self, data_hash: UUID, frame_index: int, comment: str, issue_tags: List[str]):
        self._client.add_frame_issue(
            project_hash=self._project_hash,
            data_hash=data_hash,
            frame_index=frame_index,
            comment=comment,
            issue_tags=issue_tags,
        )
