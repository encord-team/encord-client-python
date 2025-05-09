from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union, final
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.issues.issue_anchors import DataUnitIssueAnchor, FrameCoordinateIssueAnchor, FrameIssueAnchor
from encord.orm.base_dto import BaseDTO


class _NewIssue(BaseDTO):
    anchor: Union[DataUnitIssueAnchor, FrameIssueAnchor, FrameCoordinateIssueAnchor]
    comment: str
    issue_tags: List[str]


@final
class _ProjectDataUnitIssueAnchor(DataUnitIssueAnchor):
    project_hash: UUID
    data_hash: UUID

    @classmethod
    def from_anchor_without_project_and_data_hashes(
        cls, anchor: DataUnitIssueAnchor, *, project_hash: UUID, data_hash: UUID
    ) -> _ProjectDataUnitIssueAnchor:
        return cls(
            type=anchor.type,
            project_hash=project_hash,
            data_hash=data_hash,
        )


@final
class _ProjectDataUnitFrameIssueAnchor(FrameIssueAnchor):
    project_hash: UUID
    data_hash: UUID

    @classmethod
    def from_anchor_without_project_and_data_hashes(
        cls, anchor: FrameIssueAnchor, *, project_hash: UUID, data_hash: UUID
    ) -> _ProjectDataUnitFrameIssueAnchor:
        return cls(
            type=anchor.type,
            project_hash=project_hash,
            data_hash=data_hash,
            frame_index=anchor.frame_index,
        )


@final
class _ProjectDataUnitFrameCoordinateIssueAnchor(FrameCoordinateIssueAnchor):
    project_hash: UUID
    data_hash: UUID

    @classmethod
    def from_anchor_without_project_and_data_hashes(
        cls, anchor: FrameCoordinateIssueAnchor, *, project_hash: UUID, data_hash: UUID
    ) -> _ProjectDataUnitFrameCoordinateIssueAnchor:
        return cls(
            type=anchor.type,
            project_hash=project_hash,
            data_hash=data_hash,
            frame_index=anchor.frame_index,
            x=anchor.x,
            y=anchor.y,
        )


@final
class _NewIssueInProjectDataUnit(BaseDTO):
    anchor: Union[
        _ProjectDataUnitIssueAnchor, _ProjectDataUnitFrameIssueAnchor, _ProjectDataUnitFrameCoordinateIssueAnchor
    ]
    comment: str
    issue_tags: List[str]


class _CreateIssuesPayload(BaseDTO):
    issues: List[_NewIssueInProjectDataUnit]


def _get_anchor_with_project_and_data_hashes(
    anchor: Union[DataUnitIssueAnchor, FrameIssueAnchor, FrameCoordinateIssueAnchor],
    *,
    project_hash: UUID,
    data_hash: UUID,
) -> Union[_ProjectDataUnitIssueAnchor, _ProjectDataUnitFrameIssueAnchor, _ProjectDataUnitFrameCoordinateIssueAnchor]:
    if isinstance(anchor, DataUnitIssueAnchor):
        return _ProjectDataUnitIssueAnchor.from_anchor_without_project_and_data_hashes(
            anchor, project_hash=project_hash, data_hash=data_hash
        )
    elif isinstance(anchor, FrameIssueAnchor):
        return _ProjectDataUnitFrameIssueAnchor.from_anchor_without_project_and_data_hashes(
            anchor, project_hash=project_hash, data_hash=data_hash
        )
    elif isinstance(anchor, FrameCoordinateIssueAnchor):
        return _ProjectDataUnitFrameCoordinateIssueAnchor.from_anchor_without_project_and_data_hashes(
            anchor, project_hash=project_hash, data_hash=data_hash
        )
    else:
        raise ValueError(f"Unknown anchor type: {type(anchor)}")


@dataclass
class _IssueClient:
    api_client: ApiClient

    def add_file_issue(self, *, project_hash: UUID, data_hash: UUID, comment: str, issue_tags: List[str]):
        self._add_issue(
            project_hash=project_hash,
            data_hash=data_hash,
            issue=_NewIssue(
                anchor=DataUnitIssueAnchor(),
                comment=comment,
                issue_tags=issue_tags,
            ),
        )

    def add_frame_issue(
        self, *, project_hash: UUID, data_hash: UUID, frame_index: int, comment: str, issue_tags: List[str]
    ):
        self._add_issue(
            project_hash=project_hash,
            data_hash=data_hash,
            issue=_NewIssue(
                anchor=FrameIssueAnchor(frame_index=frame_index),
                comment=comment,
                issue_tags=issue_tags,
            ),
        )

    def _add_issue(self, project_hash: UUID, data_hash: UUID, issue: _NewIssue) -> None:
        self.api_client.post(
            path=f"/comment-threads",
            params=None,
            payload=_CreateIssuesPayload(
                issues=[
                    _NewIssueInProjectDataUnit(
                        anchor=_get_anchor_with_project_and_data_hashes(
                            issue.anchor, project_hash=project_hash, data_hash=data_hash
                        ),
                        comment=issue.comment,
                        issue_tags=issue.issue_tags,
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
