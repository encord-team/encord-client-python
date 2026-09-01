from __future__ import annotations

from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.frames import Ranges, ranges_list_to_ranges
from encord.objects.types import ClassificationAnswer, SpaceRange


def resolve_classification_ranges(
    classification_answer: ClassificationAnswer,
) -> tuple[Ranges, dict[str, Ranges]] | None:
    """Return the root ranges and child-space ranges represented by a classification answer.

    The top-level range is always the root placement. A root entry in `spaces` is unsupported and ignored.
    """

    if not classification_answer.get("featureHash"):
        return None

    root_ranges = ranges_list_to_ranges(classification_answer.get("range") or [])
    space_ranges = {
        space_id: _frame_ranges(space_range)
        for space_id, space_range in (classification_answer.get("spaces") or {}).items()
        if space_id != ROOT_SPACE_ID
    }
    return root_ranges, space_ranges


def _frame_ranges(space_range: SpaceRange) -> Ranges:
    if space_range["type"] != "frame":
        return []

    return ranges_list_to_ranges(space_range["range"])
