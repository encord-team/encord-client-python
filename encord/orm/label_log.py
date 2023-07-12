from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


@dataclass(frozen=True)
class LabelLog:
    log_hash: str
    user_hash: str
    user_email: str
    annotation_hash: str  # Legacy value. Replaced by identifier.
    identifier: str
    data_hash: str
    feature_hash: str
    action: Action
    label_name: str
    time_taken: int
    created_at: datetime
    frame: int


class Action(IntEnum):
    ADD = 0
    EDIT = 1
    DELETE = 2
    START = 3
    END = 4
    MARK_AS_NOT_LABELLED = 5
    MARK_AS_IN_PROGRESS = 6
    MARK_AS_LABELLED = 7
    MARK_AS_REVIEW_REQUIRED = 8
    MARK_AS_REVIEWED = 9
    MARK_AS_REVIEWED_TWICE = 10
    SUBMIT_TASK = 11
    APPROVE_LABEL = 12
    REJECT_LABEL = 13
    CLICK_SAVE = 14
    CLICK_UNDO = 15
    CLICK_REDO = 16
    CLICK_BULK = 17
    CLICK_ZOOM = 19
    CLICK_BRIGHTNESS = 20
    CLICK_HOTKEYS = 21
    CLICK_SETTINGS = 22
    ADD_ATTRIBUTE = 23
    EDIT_ATTRIBUTE = 24
    DELETE_ATTRIBUTE = 25
    APPROVE_NESTED_ATTRIBUTE = 26
    REJECT_NESTED_ATTRIBUTE = 27
    SUBMIT_LABEL = 28
    SUBMIT_NESTED_ATTRIBUTE = 29
    BUFFERING_OVERLAY_SHOWN = 30
    BITRATE_WARNING_SHOWN = 31
    SEEKING_OVERLAY_SHOWN = 32
