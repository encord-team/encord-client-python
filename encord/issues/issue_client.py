from __future__ import annotations

from datetime import datetime
from enum import auto
from typing import Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class IssueAnchorType(CamelStrEnum):
    DATA_UNIT = auto()
    FRAME = auto()
    FRAME_COORDINATE = auto()
    SCENE_COORDINATE = auto()
    FRAME_RANGE = auto()
    ANNOTATION = auto()


class IssueFrameRange(BaseDTO):
    """Represents a range of frames [start, end] inclusive"""

    start: int
    end: int


class _FileIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.DATA_UNIT] = IssueAnchorType.DATA_UNIT
    data_uuid: UUID
    space_id: Optional[str] = None


class _FrameIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME] = IssueAnchorType.FRAME
    data_uuid: UUID
    space_id: Optional[str] = None
    frame_index: int


class _CoordinateIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME_COORDINATE] = IssueAnchorType.FRAME_COORDINATE
    data_uuid: UUID
    space_id: Optional[str] = None
    frame_index: int
    x: float
    y: float


class _SceneCoordinateIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.SCENE_COORDINATE] = IssueAnchorType.SCENE_COORDINATE
    data_uuid: UUID
    frame_index: int
    x: float
    y: float
    z: float


class _AnnotationIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.ANNOTATION] = IssueAnchorType.ANNOTATION
    data_uuid: UUID
    annotation_id: str
    space_id: Optional[str] = None
    frame_ranges: Optional[List[IssueFrameRange]] = None


_IssueAnchor = Union[
    _FileIssueAnchor,
    _FrameIssueAnchor,
    _CoordinateIssueAnchor,
    _SceneCoordinateIssueAnchor,
    _AnnotationIssueAnchor,
]


class _NewIssue(BaseDTO):
    anchor: _IssueAnchor
    comment: str
    issue_tags: List[str]


class _CreateIssuesPayload(BaseDTO):
    issues: List[_NewIssue]


class GetIssuesParam(BaseDTO):
    data_unit_id: UUID
    page_token: Optional[str] = None


class _DeleteIssuesBody(BaseDTO):
    issue_uuids: List[UUID]


# Matches the back-end's per-request issue limit. Kept in sync manually; if the
# back-end limit changes, this should change too.
_MAX_DELETE_BATCH = 1000


class IssueComment(BaseDTO):
    content: str
    author_email: str
    created_at: datetime


class GetIssueTagsParams(BaseDTO):
    page_token: Optional[str] = None


class IssueTag(BaseDTO):
    name: str
    uuid: UUID


class IssueResolution(BaseDTO):
    is_resolved: bool
    created_at: datetime
    actor_email: Optional[str]


class _BaseIssue(BaseDTO):
    type: IssueAnchorType
    uuid: UUID
    data_uuid: UUID
    comments: List[IssueComment]
    tags: List[IssueTag]
    resolution_history: List[IssueResolution]


class FileIssue(_BaseIssue):
    type: Literal[IssueAnchorType.DATA_UNIT] = IssueAnchorType.DATA_UNIT
    space_id: Optional[str] = None


class FrameIssue(_BaseIssue):
    type: Literal[IssueAnchorType.FRAME] = IssueAnchorType.FRAME
    space_id: Optional[str] = None
    frame_index: int


class IssueCoordinate(BaseDTO):
    x: float
    y: float


class CoordinateIssue(_BaseIssue):
    type: Literal[IssueAnchorType.FRAME_COORDINATE] = IssueAnchorType.FRAME_COORDINATE
    space_id: Optional[str] = None
    frame_index: int
    coordinate: IssueCoordinate


class SceneIssueCoordinate(BaseDTO):
    x: float
    y: float
    z: float


class SceneCoordinateIssue(_BaseIssue):
    """Issue anchored to a 3D coordinate within a scene on a specific frame."""

    type: Literal[IssueAnchorType.SCENE_COORDINATE] = IssueAnchorType.SCENE_COORDINATE
    frame_index: int
    coordinate: SceneIssueCoordinate


class FrameRangeIssue(_BaseIssue):
    """Issue anchored to a range of frames"""

    type: Literal[IssueAnchorType.FRAME_RANGE] = IssueAnchorType.FRAME_RANGE
    space_id: Optional[str] = None
    frame_ranges: List[IssueFrameRange]


class AnnotationIssue(_BaseIssue):
    """Issue anchored to a specific annotation (label rejection or annotation feedback)"""

    type: Literal[IssueAnchorType.ANNOTATION] = IssueAnchorType.ANNOTATION
    annotation_id: str
    space_id: Optional[str] = None
    # Frame ranges the issue targets; None when the issue targets the whole annotation instance.
    frame_ranges: Optional[List[IssueFrameRange]] = None


Issue = Union[FileIssue, FrameIssue, CoordinateIssue, SceneCoordinateIssue, FrameRangeIssue, AnnotationIssue]


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
        return self._api_client.get_paged_iterator(
            path=f"/projects/{project_uuid}/issues",
            params=GetIssuesParam(data_unit_id=data_uuid),
            result_type=Issue,  # type: ignore[arg-type]
            # Issue is a Pydantic discriminated union; type checker doesn't recognize it as Type[T] but it works correctly at runtime
        )

    def delete_issues(self, project_uuid: UUID, issue_uuids: List[UUID]) -> None:
        if not issue_uuids:
            return

        for chunk_start in range(0, len(issue_uuids), _MAX_DELETE_BATCH):
            chunk = issue_uuids[chunk_start : chunk_start + _MAX_DELETE_BATCH]
            self._api_client.post(
                path=f"/projects/{project_uuid}/issues/delete",
                params=None,
                payload=_DeleteIssuesBody(issue_uuids=chunk),
                result_type=None,
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
        - CoordinateIssue: Issues anchored to specific 2D coordinates on a frame
        - SceneCoordinateIssue: Issues anchored to 3D scene coordinates on a frame
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

    def add_file_issue(self, comment: str, issue_tags: List[str], space_id: Optional[str] = None) -> None:
        """Adds a file issue.

        Args:
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
            space_id (Optional[str]): For data units that use spaces (Data Groups and scenes),
                identifies which space the issue is attached to. Leave as ``None`` for data
                units without spaces.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_FileIssueAnchor(
                data_uuid=self._data_uuid,
                space_id=space_id,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_frame_issue(
        self, frame_index: int, comment: str, issue_tags: List[str], space_id: Optional[str] = None
    ) -> None:
        """Adds a frame issue.

        Args:
            frame_index (int): The index of the frame to add the issue to.
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
            space_id (Optional[str]): For data units that use spaces (Data Groups and scenes),
                identifies which space the issue is attached to. Leave as ``None`` for data
                units without spaces.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_FrameIssueAnchor(data_uuid=self._data_uuid, frame_index=frame_index, space_id=space_id),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_coordinate_issue(
        self,
        frame_index: int,
        x: float,
        y: float,
        comment: str,
        issue_tags: List[str],
        space_id: Optional[str] = None,
    ) -> None:
        """Adds a issue pinned to a coordinate.

        Args:
            frame_index (int): The index of the frame to add the issue to.
            x (float): The x coordinate of the issue.
            y (float): The y coordinate of the issue.
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
            space_id (Optional[str]): For data units that use spaces (Data Groups and scenes),
                identifies which space the issue is attached to. Leave as ``None`` for data
                units without spaces.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_CoordinateIssueAnchor(
                data_uuid=self._data_uuid,
                frame_index=frame_index,
                x=x,
                y=y,
                space_id=space_id,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_scene_coordinate_issue(
        self, frame_index: int, x: float, y: float, z: float, comment: str, issue_tags: List[str]
    ) -> None:
        """Adds an issue pinned to a 3D coordinate in a scene on a specific frame.

        Args:
            frame_index (int): The index of the frame to add the issue to.
            x (float): The x coordinate (in scene space).
            y (float): The y coordinate (in scene space).
            z (float): The z coordinate (in scene space).
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.
        """
        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_SceneCoordinateIssueAnchor(
                data_uuid=self._data_uuid,
                frame_index=frame_index,
                x=x,
                y=y,
                z=z,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def add_annotation_issue(
        self,
        annotation_id: str,
        comment: str,
        issue_tags: List[str],
        frame_ranges: Optional[List[IssueFrameRange]] = None,
        space_id: Optional[str] = None,
    ) -> None:
        """Adds an issue anchored to a specific annotation (object or classification instance).

        Args:
            annotation_id (str): The annotation the issue is attached to. This is the
                object instance ``object_hash`` (or classification instance
                ``classification_hash``) of the annotation within this task's data unit.
            comment (str): The comment for the issue.
            issue_tags (List[str]): The issue tags for the issue.

            frame_ranges (Optional[List[IssueFrameRange]]): The frame ranges to pin the issue
                to, each an inclusive ``[start, end]`` range. Leave as ``None`` to
                flag the whole annotation instance across every frame it appears on (e.g. a

                wrong attribute value). Provide one or more ranges to target the instance on
                those frames (e.g. a bad contour over a span of frames). A single frame is a
                range where ``start == end``.
            space_id (Optional[str]): For data units that use spaces (Data Groups and scenes),
                identifies which space the annotation belongs to. Leave as ``None`` for data
                units without spaces.

        Example:
            >>> for obj in label_row.get_object_instances():
            ...     # Flag the whole instance (e.g. wrong attribute value):
            ...     if not passes_attribute_qa(obj):
            ...         task.issues.add_annotation_issue(
            ...             annotation_id=obj.object_hash,
            ...             comment="Wrong attribute value",
            ...             issue_tags=["qa-automation"],
            ...         )
            ...     # Flag the instance over a span of frames (e.g. bad contour on frames 30-45):
            ...     task.issues.add_annotation_issue(
            ...         annotation_id=obj.object_hash,
            ...         comment="Bad contour",
            ...         issue_tags=["qa-automation"],
            ...         frame_ranges=[IssueFrameRange(start=30, end=45)],
            ...     )

        Raises:
            ValueError: If ``frame_ranges`` is an empty list (omit it, or pass ``None``, to
                target the whole annotation instance) or contains an invalid range where
                ``start`` is negative or ``start > end``.
        """
        if frame_ranges is not None:
            if len(frame_ranges) == 0:
                raise ValueError(
                    "`frame_ranges` must be non-empty when provided; omit it to target the whole annotation instance."
                )
            for frame_range in frame_ranges:
                if frame_range.start < 0 or frame_range.start > frame_range.end:
                    raise ValueError(
                        f"Invalid frame range [{frame_range.start}, {frame_range.end}]: expected 0 <= start <= end."
                    )

        self._issue_client.add_issue(
            project_uuid=self._project_uuid,
            anchor=_AnnotationIssueAnchor(
                data_uuid=self._data_uuid,
                annotation_id=annotation_id,
                space_id=space_id,
                frame_ranges=frame_ranges,
            ),
            comment=comment,
            issue_tags=issue_tags,
        )

    def delete(self, issues: List[Union[Issue, UUID]]) -> None:
        """Deletes one or more issues from this task in a single request.

        Accepts either `Issue` objects (as returned by `list()`) or raw UUIDs,
        mixed freely. Empty input is a no-op.

        Permissions: project admins can delete any issue. Issue authors can
        delete their own general issues, but annotation issues (label
        rejections) can only be deleted by project admins.

        The back-end validates the entire batch before deleting anything: if
        any issue cannot be deleted (because the caller is not the author and
        not a project admin, or the issue doesn't belong to this task's
        project), the request raises and NO issues in the batch are deleted.

        Args:
            issues: A list of `Issue` objects or `UUID`s to delete.

        Example:
            >>> # Delete a single issue:
            >>> task.issues.delete([issue])
            >>>
            >>> # Or delete several at once:
            >>> obsolete = [i for i in task.issues.list() if i.comments[0].content.startswith("[obsolete]")]
            >>> task.issues.delete(obsolete)
        """
        if not issues:
            return
        issue_uuids: List[UUID] = [item if isinstance(item, UUID) else item.uuid for item in issues]
        self._issue_client.delete_issues(project_uuid=self._project_uuid, issue_uuids=issue_uuids)
