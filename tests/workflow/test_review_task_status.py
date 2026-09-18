import uuid
from datetime import datetime, timezone

import pytest

from encord.workflow.stages.consensus_review import ConsensusReviewTask, ConsensusReviewTaskStatus
from encord.workflow.stages.review import ReviewTask, ReviewTaskStatus


def _raw_task(status: str) -> dict:
    return {
        "uuid": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "data_hash": str(uuid.uuid4()),
        "data_title": "some data unit",
        "assignee": None,
        "status": status,
    }


@pytest.mark.parametrize("status", [s.value for s in ReviewTaskStatus])
def test_review_task_parses_every_status(status: str) -> None:
    task = ReviewTask.from_dict(_raw_task(status))
    assert task.status == ReviewTaskStatus(status)


@pytest.mark.parametrize("status", [s.value for s in ConsensusReviewTaskStatus])
def test_consensus_review_task_parses_every_status(status: str) -> None:
    task = ConsensusReviewTask.from_dict({**_raw_task(status), "options": []})
    assert task.status == ConsensusReviewTaskStatus(status)


def test_review_task_status_matches_annotation_and_agent_task_status() -> None:
    from encord.workflow.stages.agent import AgentTaskStatus
    from encord.workflow.stages.annotation import AnnotationTaskStatus

    review_values = {s.value for s in ReviewTaskStatus}
    annotation_values = {s.value for s in AnnotationTaskStatus}
    agent_values = {s.value for s in AgentTaskStatus}

    assert review_values == annotation_values == agent_values
