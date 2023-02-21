from __future__ import annotations

from enum import Enum

DEFAULT_CONFIDENCE = 1
DEFAULT_MANUAL_ANNOTATION = True
DATETIME_LONG_STRING_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


# class LabelStatus(str, Enum):
#     NOT_LABELLED = "NOT_LABELLED"
#     LABEL_IN_PROGRESS = "LABEL_IN_PROGRESS"
#     LABELLED = "LABELLED"
#     REVIEW_IN_PROGRESS = "REVIEW_IN_PROGRESS"
#     REVIEWED = "REVIEWED"
#     REVIEWED_TWICE = "REVIEWED_TWICE"
#
#     MISSING_LABEL_STATUS = "_MISSING_LABEL_STATUS_"
#     """
#     This value will be displayed if the Encord platform has a new label status and your SDK version does not understand
#     it yet. Please update your SDK to the latest version.
#     """
#
#     @classmethod
#     def _missing_(cls, value):
#         return cls.MISSING_LABEL_STATUS
