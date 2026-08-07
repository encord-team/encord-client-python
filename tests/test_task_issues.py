"""Unit tests for TaskIssues issue-creation methods."""

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from encord.issues.issue_client import (
    IssueAnchorType,
    IssueFrameRange,
    TaskIssues,
    _AnnotationIssueAnchor,
    _CreateIssuesPayload,
)

PROJECT_UUID = UUID("00000000-0000-0000-0000-000000000001")
DATA_UUID = UUID("00000000-0000-0000-0000-000000000002")


def test_add_annotation_issue_posts_annotation_anchor() -> None:
    api_client = MagicMock()
    task_issues = TaskIssues(api_client=api_client, project_uuid=PROJECT_UUID, data_uuid=DATA_UUID)

    task_issues.add_annotation_issue(
        annotation_id="iFax13Qj",
        comment="fails-occlusion-rule",
        issue_tags=["qa-automation"],
    )

    api_client.post.assert_called_once()
    _, kwargs = api_client.post.call_args
    assert kwargs["path"] == f"/projects/{PROJECT_UUID}/issues"

    payload = kwargs["payload"]
    assert isinstance(payload, _CreateIssuesPayload)
    assert len(payload.issues) == 1

    new_issue = payload.issues[0]
    assert new_issue.comment == "fails-occlusion-rule"
    assert new_issue.issue_tags == ["qa-automation"]

    anchor = new_issue.anchor
    assert isinstance(anchor, _AnnotationIssueAnchor)
    assert anchor.type == IssueAnchorType.ANNOTATION
    assert anchor.data_uuid == DATA_UUID
    assert anchor.annotation_id == "iFax13Qj"
    # No frame ranges / space given => whole-instance issue on a non-Data-Group unit.
    assert anchor.frame_ranges is None
    assert anchor.space_id is None


def test_add_annotation_issue_with_frame_ranges_posts_frame_ranges() -> None:
    api_client = MagicMock()
    task_issues = TaskIssues(api_client=api_client, project_uuid=PROJECT_UUID, data_uuid=DATA_UUID)

    task_issues.add_annotation_issue(
        annotation_id="iFax13Qj",
        comment="bad-contour",
        issue_tags=["qa-automation"],
        frame_ranges=[IssueFrameRange(start=30, end=32), IssueFrameRange(start=45, end=45)],
        space_id="child-space-1",
    )

    api_client.post.assert_called_once()
    _, kwargs = api_client.post.call_args
    anchor = kwargs["payload"].issues[0].anchor
    assert isinstance(anchor, _AnnotationIssueAnchor)
    assert anchor.annotation_id == "iFax13Qj"
    assert anchor.frame_ranges == [IssueFrameRange(start=30, end=32), IssueFrameRange(start=45, end=45)]
    assert anchor.space_id == "child-space-1"


def test_add_annotation_issue_rejects_empty_frame_ranges() -> None:
    api_client = MagicMock()
    task_issues = TaskIssues(api_client=api_client, project_uuid=PROJECT_UUID, data_uuid=DATA_UUID)

    with pytest.raises(ValueError, match="must be non-empty"):
        task_issues.add_annotation_issue(
            annotation_id="iFax13Qj",
            comment="bad-contour",
            issue_tags=["qa-automation"],
            frame_ranges=[],
        )

    # Nothing should be sent when the guard trips.
    api_client.post.assert_not_called()


def test_add_annotation_issue_rejects_invalid_frame_range() -> None:
    api_client = MagicMock()
    task_issues = TaskIssues(api_client=api_client, project_uuid=PROJECT_UUID, data_uuid=DATA_UUID)

    for bad_range in (IssueFrameRange(start=45, end=30), IssueFrameRange(start=-1, end=5)):
        with pytest.raises(ValueError, match="Invalid frame range"):
            task_issues.add_annotation_issue(
                annotation_id="iFax13Qj",
                comment="bad-contour",
                issue_tags=["qa-automation"],
                frame_ranges=[bad_range],
            )

    api_client.post.assert_not_called()
