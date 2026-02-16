import pytest

from encord.orm.project import ProjectStatus


@pytest.mark.parametrize(
    ("status_str", "expected_parsed_status"),
    [
        ("inProgress", ProjectStatus.IN_PROGRESS),
        ("inReview", ProjectStatus.IN_REVIEW),
        ("someNewStatus1", ProjectStatus.UNKNOWN),
        ("someNewStatus2", ProjectStatus.UNKNOWN),
    ],
)
def test_project_status_unknown_fallback(
    status_str: str,
    expected_parsed_status: ProjectStatus,
) -> None:
    """Test that unknown project status values are handled gracefully.

    When the backend API introduces new status values that this SDK version
    doesn't recognize, they should be mapped to ProjectStatus.UNKNOWN instead
    of raising a ValueError.
    """
    # Test direct enum construction with unknown value
    unknown_status = ProjectStatus(status_str)
    assert unknown_status == expected_parsed_status
