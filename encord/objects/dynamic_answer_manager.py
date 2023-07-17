from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

from encord.objects.answers import Answer, get_default_answer_from_attribute
from encord.objects.attributes import Attribute
from encord.objects.frames import (
    Frames,
    Range,
    Ranges,
    frames_class_to_frames_list,
    frames_to_ranges,
)
from encord.objects.options import Option


class DynamicAnswerManager:
    """
    This class is an internal helper class. The user should not interact with it directly.

    Manages the answers that are set for different frames.
    This can be part of the ObjectInstance class.
    """

    def __init__(self, object_instance: ObjectInstance):
        self._object_instance = object_instance
        self._frames_to_answers: Dict[int, Set[Answer]] = defaultdict(set)
        self._answers_to_frames: Dict[Answer, Set[int]] = defaultdict(set)

        self._dynamic_uninitialised_answer_options: Set[Answer] = self._get_dynamic_answers()
        # ^ these are like the static answers. Everything that is possibly an answer. However,
        # don't forget also nested-ness. In this case nested-ness should be ignored.
        # ^ I might not need this object but only need the _get_dynamic_answers object.

    def is_valid_dynamic_attribute(self, attribute: Attribute) -> bool:
        feature_node_hash = attribute.feature_node_hash

        for answer in self._dynamic_uninitialised_answer_options:
            if answer.ontology_attribute.feature_node_hash == feature_node_hash:
                return True
        return False

    def delete_answer(
        self,
        attribute: Attribute,
        frames: Optional[Frames] = None,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
    ) -> None:
        if frames is None:
            frames = [Range(i, i) for i in self._frames_to_answers.keys()]
        frame_list = frames_class_to_frames_list(frames)

        for frame in frame_list:
            to_remove_answer = None
            for answer_object in self._frames_to_answers[frame]:
                if filter_answer is not None:
                    if answer_object.is_answered() and answer_object.get() != filter_answer:
                        continue

                # ideally this would not be a log(n) operation, however these will not be extremely large.
                if answer_object.ontology_attribute == attribute:
                    to_remove_answer = answer_object
                    break

            if to_remove_answer is not None:
                self._frames_to_answers[frame].remove(to_remove_answer)
                self._answers_to_frames[to_remove_answer].remove(frame)
                if self._answers_to_frames[to_remove_answer] == set():
                    del self._answers_to_frames[to_remove_answer]

    def set_answer(
        self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Optional[Frames] = None
    ) -> None:
        if frames is None:
            for available_frame_view in self._object_instance.get_annotations():
                self._set_answer(answer, attribute, available_frame_view.frame)
            return
        self._set_answer(answer, attribute, frames)

    def _set_answer(self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Frames) -> None:
        """Set the answer for a single frame"""

        frame_list = frames_class_to_frames_list(frames)
        for frame in frame_list:
            self._object_instance.check_within_range(frame)

        self.delete_answer(attribute, frames)

        default_answer = get_default_answer_from_attribute(attribute)
        default_answer.set(answer)

        frame_list = frames_class_to_frames_list(frames)
        for frame in frame_list:
            self._frames_to_answers[frame].add(default_answer)
            self._answers_to_frames[default_answer].add(frame)

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frames: Optional[Frames] = None,
    ) -> AnswersForFrames:
        """For a given attribute, return all the answers and frames given the filters."""
        ret = []
        filter_frames_set = None if filter_frames is None else set(frames_class_to_frames_list(filter_frames))
        for answer in self._answers_to_frames:
            if answer.ontology_attribute != attribute:
                continue
            if not answer.is_answered():
                continue
            if not (filter_answer is None or filter_answer == answer.get()):
                continue
            actual_frames = self._answers_to_frames[answer]
            if not (filter_frames_set is None or len(actual_frames & filter_frames_set) > 0):
                continue

            ranges = frames_to_ranges(self._answers_to_frames[answer])
            ret.append(AnswerForFrames(answer=answer.get(), ranges=ranges))
        return ret

    def frames(self) -> Iterable[int]:
        """Returns all frames that have answers set."""
        return self._frames_to_answers.keys()

    def get_all_answers(self) -> List[Tuple[Answer, Ranges]]:
        """Returns all answers that are set."""
        ret = []
        for answer, frames in self._answers_to_frames.items():
            ret.append((answer, frames_to_ranges(frames)))
        return ret

    def copy(self) -> DynamicAnswerManager:
        ret = DynamicAnswerManager(self._object_instance)
        ret._frames_to_answers = deepcopy(self._frames_to_answers)
        ret._answers_to_frames = deepcopy(self._answers_to_frames)
        return ret

    def _get_dynamic_answers(self) -> Set[Answer]:
        ret: Set[Answer] = set()
        for attribute in self._object_instance.ontology_item.attributes:
            if attribute.dynamic:
                answer = get_default_answer_from_attribute(attribute)
                ret.add(answer)
        return ret

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DynamicAnswerManager):
            return False
        return (
            self._frames_to_answers == other._frames_to_answers and self._answers_to_frames == other._answers_to_frames
        )

    def __hash__(self) -> int:
        return hash(id(self))


@dataclass
class AnswerForFrames:
    answer: Union[str, Option, Iterable[Option]]
    ranges: Ranges
    """
    The ranges are essentially a run length encoding of the frames where the unique answer is set.
    They are sorted in ascending order.
    """


AnswersForFrames = List[AnswerForFrames]


from encord.objects import ObjectInstance
