"""---
title: "Objects - Transcripts"
slug: "sdk-ref-objects-transcript"
hidden: false
metadata:
  title: "Objects - Transcripts"
  description: "Encord SDK Objects - Transcript segment data class."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from encord.objects.attributes import Attribute

# Marker substring used in the ontology attribute display name to identify
# transcript-bearing text attributes. There is no schema flag for this yet;
# the marker is the only signal the FE and SDK agree on.
TRANSCRIPT_NAME_MARKER = "#transcript"


@dataclass(frozen=True)
class TranscriptSegment:
    """One playback segment of a transcript on an ObjectInstance.

    A transcript-bearing attribute on an object may have multiple segments,
    each with its own frame range and text. A single segment with multiple
    sub-ranges in the underlying label is unrolled into one TranscriptSegment
    per sub-range, all sharing the same text.
    """

    range: Tuple[int, int]
    text: str
    feature_hash: str
    attribute_name: str


def is_transcript_attribute(attribute: Attribute) -> bool:
    return TRANSCRIPT_NAME_MARKER in attribute.name


def is_transcript_raw_entry(entry: Mapping[str, Any]) -> bool:
    name = entry.get("name")
    return isinstance(name, str) and TRANSCRIPT_NAME_MARKER in name
