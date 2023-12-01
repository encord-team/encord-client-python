from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Optional

from encord.common.deprecated import deprecated
from encord.orm.base_dto import BaseDTO


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


class LabelLog(BaseDTO):
    log_hash: str
    user_hash: str
    user_email: str
    data_hash: str
    action: Action
    created_at: datetime
    identifier: Optional[str]
    feature_hash: Optional[str]
    label_name: Optional[str]
    time_taken: Optional[int]
    frame: Optional[int]

    @property
    @deprecated(version="0.1.100", alternative="LabelLog.identifier")
    def annotation_hash(self) -> Optional[str]:
        """
        DEPRECATED: this field is only provided for backwards compatibility, and will be removed in the future versions.
        Please use :attr:`identifier <LabelLog.identifier>` instead.
        """
        return self.identifier


class LabelLogParams(BaseDTO):
    user_hash: Optional[str]
    data_hash: Optional[str]
    start_timestamp: Optional[int]
    end_timestamp: Optional[int]
    user_email: Optional[str]
    # Flag for backwards compatibility
    include_user_email_and_interface_key: bool = True
