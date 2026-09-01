"""Resolving the root and child-space ranges in a `classification_answers` entry.

This is the single reading of the wire contract, shared by `LabelRowV2` when it parses a label row and by
`classification_expansion` when it reconstructs the per-frame classifications the backend used to serve.
"""

from typing import Any, Dict, List, Optional

from encord.objects.classification_ranges import resolve_classification_ranges
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.frames import Range


def _answer(
    range_: Optional[List[List[int]]] = None,
    spaces: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "classificationHash": "clf",
        "featureHash": "feature",
        "classifications": [],
        "range": range_,
        "spaces": spaces or {},
    }


def test_top_level_range_is_returned_as_the_root_range() -> None:
    resolved_ranges = resolve_classification_ranges(_answer(range_=[[0, 5]]))

    assert resolved_ranges == ([Range(0, 5)], {})


def test_root_space_entry_is_ignored() -> None:
    answer = _answer(range_=[[0, 0]], spaces={ROOT_SPACE_ID: {"type": "frame", "range": [[7, 9]]}})

    resolved_ranges = resolve_classification_ranges(answer)

    assert resolved_ranges == ([Range(0, 0)], {})


def test_ranges_are_returned_for_every_child_space() -> None:
    answer = _answer(
        range_=[[0, 0]],
        spaces={
            "video-1": {"type": "frame", "range": [[4, 4]]},
            "video-2": {"type": "frame", "range": [[2, 3]]},
        },
    )

    resolved_ranges = resolve_classification_ranges(answer)

    assert resolved_ranges == (
        [Range(0, 0)],
        {
            "video-1": [Range(4, 4)],
            "video-2": [Range(2, 3)],
        },
    )


def test_a_space_naming_no_frames_has_no_ranges() -> None:
    resolved_ranges = resolve_classification_ranges(_answer(spaces={"a-space": {"type": "frame", "range": []}}))

    assert resolved_ranges == ([], {"a-space": []})


def test_a_space_does_not_inherit_the_root_range() -> None:
    answer = _answer(range_=[[100, 200]], spaces={"audio": {"type": "frame", "range": []}})

    resolved_ranges = resolve_classification_ranges(answer)

    assert resolved_ranges == ([Range(100, 200)], {"audio": []})


def test_an_answer_naming_nowhere_has_empty_root_ranges() -> None:
    resolved_ranges = resolve_classification_ranges(_answer())

    assert resolved_ranges == ([], {})


def test_a_missing_range_is_treated_as_naming_nowhere() -> None:
    answer = _answer()
    del answer["range"]

    resolved_ranges = resolve_classification_ranges(answer)

    assert resolved_ranges == ([], {})
