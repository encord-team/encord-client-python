"""---
title: "Objects - Bundled Operations"
slug: "sdk-ref-objects-bundled-op"
hidden: false
metadata:
  title: "Objects - Bundled Operations"
  description: "Encord SDK Objects - Bundled Operations."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

"""
Operation payloads to work with LabelRowV2 bundling.
These are internal helpers and not supposed to be used by external users.
"""


@dataclass
class BundledGetRowsPayload:
    uids: List[str]
    get_signed_url: bool
    include_object_feature_hashes: Optional[Set[str]]
    include_classification_feature_hashes: Optional[Set[str]]
    include_reviews: bool

    def add(self, other: BundledGetRowsPayload) -> BundledGetRowsPayload:
        self.uids.extend(other.uids)
        return self


@dataclass
class BundledCreateRowsPayload:
    uids: List[str]
    get_signed_url: bool
    branch_name: Optional[str]

    def add(self, other: BundledCreateRowsPayload) -> BundledCreateRowsPayload:
        self.uids.extend(other.uids)
        return self


@dataclass
class BundledSaveRowsPayload:
    uids: List[str]
    payload: List[Dict]
    validate_before_saving: Optional[bool]

    def add(self, other: BundledSaveRowsPayload) -> BundledSaveRowsPayload:
        self.uids.extend(other.uids)
        self.payload.extend(other.payload)
        self.validate_before_saving = self.validate_before_saving or other.validate_before_saving
        return self


@dataclass
class BundledSetPriorityPayload:
    priorities: List[Tuple[str, float]]

    def add(self, other: BundledSetPriorityPayload) -> BundledSetPriorityPayload:
        self.priorities.extend(other.priorities)
        return self


@dataclass
class BundledWorkflowCompletePayload:
    label_hashes: List[str]

    def add(self, other: BundledWorkflowCompletePayload) -> BundledWorkflowCompletePayload:
        self.label_hashes.extend(other.label_hashes)
        return self


@dataclass
class BundledWorkflowReopenPayload:
    label_hashes: List[str]

    def add(self, other: BundledWorkflowReopenPayload) -> BundledWorkflowReopenPayload:
        self.label_hashes.extend(other.label_hashes)
        return self
