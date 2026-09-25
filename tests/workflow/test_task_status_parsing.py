"""Tests that workflow task status enums tolerate skipped and future/unknown values.

The Encord platform can return task statuses (e.g. ``SKIPPED``) or entirely new
statuses that a given SDK version does not know about. Parsing such a response
must not raise; unrecognized values fall back to ``UNKNOWN``.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from encord.workflow.stages.agent import AgentTask, AgentTaskStatus
from encord.workflow.stages.annotation import AnnotationTask, AnnotationTaskStatus
from encord.workflow.stages.consensus_review import ConsensusReviewTask, ConsensusReviewTaskStatus
from encord.workflow.stages.review import (
    LabelReview,
    LabelReviewStatus,
    ReviewTask,
    ReviewTaskStatus,
)


def _base_task_fields() -> dict:
    return {
        "uuid": str(uuid4()),
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "dataHash": str(uuid4()),
        "dataTitle": "data unit",
        "assignee": None,
    }


@pytest.mark.parametrize(
    "status_enum",
    [ReviewTaskStatus, ConsensusReviewTaskStatus, AnnotationTaskStatus, AgentTaskStatus],
)
def test_status_enum_skipped_and_unknown_fallback(status_enum) -> None:
    assert status_enum("SKIPPED") is status_enum.SKIPPED
    assert status_enum("SOME_BRAND_NEW_STATUS") is status_enum.UNKNOWN


def test_label_review_status_unknown_fallback() -> None:
    assert LabelReviewStatus("SOME_BRAND_NEW_STATUS") is LabelReviewStatus.UNKNOWN


def test_review_task_parses_skipped_status() -> None:
    task = ReviewTask.from_dict({**_base_task_fields(), "status": "SKIPPED"})
    assert task.status is ReviewTaskStatus.SKIPPED


def test_review_task_parses_unknown_status() -> None:
    task = ReviewTask.from_dict({**_base_task_fields(), "status": "FUTURE_STATUS"})
    assert task.status is ReviewTaskStatus.UNKNOWN


def test_consensus_review_task_parses_unknown_status() -> None:
    task = ConsensusReviewTask.from_dict({**_base_task_fields(), "status": "FUTURE_STATUS", "options": []})
    assert task.status is ConsensusReviewTaskStatus.UNKNOWN


def test_annotation_task_parses_unknown_status() -> None:
    fields = {**_base_task_fields(), "status": "FUTURE_STATUS", "labelBranchName": "main", "lastActionedBy": None}
    task = AnnotationTask.from_dict(fields)
    assert task.status is AnnotationTaskStatus.UNKNOWN


def test_agent_task_parses_unknown_status() -> None:
    fields = {**_base_task_fields(), "status": "FUTURE_STATUS", "labelBranchName": "main", "lastActionedBy": None}
    task = AgentTask.from_dict(fields)
    assert task.status is AgentTaskStatus.UNKNOWN


def test_label_review_parses_unknown_status() -> None:
    review = LabelReview.from_dict(
        {
            "reviewUuid": str(uuid4()),
            "status": "FUTURE_STATUS",
            "labelType": "Object",
            "labelId": str(uuid4()),
        }
    )
    assert review.status is LabelReviewStatus.UNKNOWN
