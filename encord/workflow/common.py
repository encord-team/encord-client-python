from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import auto
from typing import Iterable, List, Literal, Optional, Sequence, Tuple, Type, TypeVar, Union, final
from uuid import UUID

from encord.http.bundle import Bundle, bundled_operation
from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO, PrivateAttr


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None


@dataclass(frozen=True)
class WorkflowStageBase:
    _workflow_client: WorkflowClient = field(compare=False, hash=False)
    uuid: UUID
    title: str

    def __repr__(self):
        return f"{self.__class__.__name__}(stage_type={self.stage_type}, uuid='{self.uuid}', title='{self.title}')"


class WorkflowTask(BaseDTO):
    _stage_uuid: Optional[UUID] = PrivateAttr(None)
    _workflow_client: Optional[WorkflowClient] = PrivateAttr(None)

    uuid: UUID
    created_at: datetime
    updated_at: datetime

    def _get_client_data(self) -> Tuple[WorkflowClient, UUID]:
        assert self._stage_uuid
        assert self._workflow_client
        return self._workflow_client, self._stage_uuid


class WorkflowAction(BaseDTO):
    task_uuid: UUID


class IssueAnchorType(CamelStrEnum):
    DATA_UNIT = auto()
    FRAME = auto()
    FRAME_COORDINATE = auto()


class DataUnitIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.DATA_UNIT] = IssueAnchorType.DATA_UNIT

    def with_project_and_data_hash(self, *, project_hash: UUID, data_hash: UUID) -> _ProjectDataUnitIssueAnchor:
        return _ProjectDataUnitIssueAnchor(
            type=self.type,
            project_hash=project_hash,
            data_hash=data_hash,
        )


class FrameIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME] = IssueAnchorType.FRAME
    frame_index: int

    def with_project_and_data_hash(self, *, project_hash: UUID, data_hash: UUID) -> _ProjectDataUnitFrameIssueAnchor:
        return _ProjectDataUnitFrameIssueAnchor(
            type=self.type,
            project_hash=project_hash,
            data_hash=data_hash,
            frame_index=self.frame_index,
        )


class FrameCoordinateIssueAnchor(BaseDTO):
    type: Literal[IssueAnchorType.FRAME_COORDINATE] = IssueAnchorType.FRAME_COORDINATE
    frame_index: int
    x: float
    y: float

    def with_project_and_data_hash(
        self, *, project_hash: UUID, data_hash: UUID
    ) -> _ProjectDataUnitFrameCoordinateIssueAnchor:
        return _ProjectDataUnitFrameCoordinateIssueAnchor(
            type=self.type,
            project_hash=project_hash,
            data_hash=data_hash,
            frame_index=self.frame_index,
            x=self.x,
            y=self.y,
        )


class NewIssue(BaseDTO):
    anchor: Union[DataUnitIssueAnchor, FrameIssueAnchor, FrameCoordinateIssueAnchor]
    comment: str
    issue_tags: List[str]


@final
class _ProjectDataUnitIssueAnchor(DataUnitIssueAnchor):
    project_hash: UUID
    data_hash: UUID


@final
class _ProjectDataUnitFrameIssueAnchor(FrameIssueAnchor):
    project_hash: UUID
    data_hash: UUID


@final
class _ProjectDataUnitFrameCoordinateIssueAnchor(FrameCoordinateIssueAnchor):
    project_hash: UUID
    data_hash: UUID


@final
class _NewIssueInProjectDataUnit(BaseDTO):
    anchor: Union[
        _ProjectDataUnitIssueAnchor, _ProjectDataUnitFrameIssueAnchor, _ProjectDataUnitFrameCoordinateIssueAnchor
    ]
    comment: str
    issue_tags: List[str]


class _CreateIssuesPayload(BaseDTO):
    issues: List[_NewIssueInProjectDataUnit]


TaskT = TypeVar("TaskT", bound=WorkflowTask)
ReviewT = TypeVar("ReviewT", bound=BaseDTO)


@dataclass
class BundledWorkflowActionPayload:
    stage_uuid: UUID
    actions: List[WorkflowAction]

    def add(self, other: BundledWorkflowActionPayload) -> BundledWorkflowActionPayload:
        assert self.stage_uuid == other.stage_uuid, "It's only possible to bundle actions for one stage at a time"
        self.actions.extend(other.actions)
        return self


class WorkflowReviewAction(BaseDTO):
    review_uuid: UUID


@dataclass
class BundledReviewActionPayload:
    stage_uuid: UUID
    task_uuid: UUID
    actions: List[WorkflowReviewAction]

    def add(self, other: BundledReviewActionPayload) -> BundledReviewActionPayload:
        assert self.stage_uuid == other.stage_uuid, "It's only possible to bundle actions for one stage at a time"
        assert self.task_uuid == other.task_uuid, "It's only possible to bundle review actions one task at a time"
        self.actions.extend(other.actions)
        return self


@dataclass
class WorkflowClient:
    api_client: ApiClient
    project_hash: UUID

    def get_tasks(self, stage_uuid: UUID, params: TasksQueryParams, type_: Type[TaskT]) -> Iterable[TaskT]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks",
            params=params,
            result_type=type_,
        )

    def action(self, stage_uuid: UUID, action: WorkflowAction, *, bundle: Optional[Bundle] = None) -> None:
        if not bundle:
            self._action(stage_uuid, [action])
        else:
            bundled_operation(
                bundle=bundle,
                operation=self._action,
                payload=BundledWorkflowActionPayload(stage_uuid=stage_uuid, actions=[action]),
            )

    def _action(self, stage_uuid: UUID, actions: Sequence[WorkflowAction]) -> None:
        self.api_client.post(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/actions",
            params=None,
            payload=actions,
            result_type=None,
        )

    def add_issues(self, issues: List[NewIssue], data_hash: UUID) -> None:
        self.api_client.post(
            path=f"/comment-threads",
            params=None,
            payload=_CreateIssuesPayload(
                issues=[
                    _NewIssueInProjectDataUnit(
                        anchor=issue.anchor.with_project_and_data_hash(
                            project_hash=self.project_hash, data_hash=data_hash
                        ),
                        comment=issue.comment,
                        issue_tags=issue.issue_tags,
                    )
                    for issue in issues
                ]
            ),
            result_type=None,
        )

    def get_label_reviews(self, stage_uuid: UUID, task_uuid: UUID, type_: Type[ReviewT]) -> Iterable[ReviewT]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks/{task_uuid}/reviews",
            params=TasksQueryParams(),
            result_type=type_,
        )

    def label_review_action(
        self,
        stage_uuid: UUID,
        task_uuid: UUID,
        action: WorkflowReviewAction,
        *,
        bundle: Optional[Bundle] = None,
    ) -> None:
        if not bundle:
            self._label_review_action(stage_uuid, task_uuid, [action])
        else:
            bundled_operation(
                bundle=bundle,
                operation=self._label_review_action,
                payload=BundledReviewActionPayload(stage_uuid=stage_uuid, task_uuid=task_uuid, actions=[action]),
            )

    def _label_review_action(self, stage_uuid: UUID, task_uuid: UUID, actions: Sequence[WorkflowReviewAction]) -> None:
        self.api_client.post(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks/{task_uuid}/reviews/actions",
            params=TasksQueryParams(),
            payload=actions,
            result_type=None,
        )
