"""Polling a queued platform job for its result."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

JobT = TypeVar("JobT")


@dataclass(frozen=True)
class PollingSchedule:
    """How often a job is read while it is pending. The wait doubles from ``initial_seconds`` up to ``max_seconds``.

    Each job kind sets its own: a job that finishes in seconds polls more often than one that runs for minutes.
    """

    initial_seconds: float = 1.0
    max_seconds: float = 5.0


def poll_job(
    get_job: Callable[[], JobT],
    is_pending: Callable[[JobT], bool],
    deadline: float,
    schedule: PollingSchedule = PollingSchedule(),
) -> Optional[JobT]:
    """Poll the job until it is no longer pending, or the deadline passes; None if it is still pending then.

    The job is checked at least once, even when the deadline has already passed.

    Args:
        get_job: Reads the job's current state from the platform.
        is_pending: Whether a state means the job is still queued or running.
        deadline: A ``time.monotonic()`` value after which polling stops.
        schedule: The wait between reads.
    """
    interval = schedule.initial_seconds
    while True:
        job = get_job()
        if not is_pending(job):
            return job
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        time.sleep(min(interval, remaining))
        interval = min(interval * 2, schedule.max_seconds)
