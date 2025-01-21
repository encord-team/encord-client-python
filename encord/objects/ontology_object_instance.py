"""---
title: "Objects - Ontology Object Instance"
slug: "sdk-ref-objects-ont-object-instance"
hidden: false
metadata:
  title: "Objects - Ontology Object Instance"
  description: "Encord SDK Objects - Ontology Object Instances."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from encord.common.range_manager import RangeManager
from encord.common.time_parser import parse_datetime
from encord.constants.enums import DataType
from encord.exceptions import LabelRowError
from encord.objects import ChecklistAttribute, RadioAttribute, Shape, TextAttribute
from encord.objects.answers import (
    Answer,
    _get_static_answer_map,
    get_default_answer_from_attribute,
)
from encord.objects.attributes import Attribute, _get_attribute_by_hash
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    NON_GEOMETRIC_COORDINATES,
    AudioCoordinates,
    Coordinates,
    HtmlCoordinates,
    TextCoordinates,
)
from encord.objects.frames import (
    Frames,
    Range,
    Ranges,
    frames_class_to_frames_list,
    frames_to_ranges,
    ranges_list_to_ranges,
)
from encord.objects.html_node import HtmlRange, HtmlRanges
from encord.objects.internal_helpers import (
    _infer_attribute_from_answer,
    _search_child_attributes,
)
from encord.objects.ontology_object import Object
from encord.objects.options import Option
from encord.objects.utils import check_email, short_uuid_str

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class ObjectInstance:
    """An object instance is an object that has coordinates and can be placed on one or multiple frames in a label row."""

    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None):
        self._ontology_object = ontology_object
        self._object_hash = object_hash or short_uuid_str()
        self._parent: Optional[LabelRowV2] = None

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_object.attributes)
        # feature_node_hash of attribute to the answer.

        self._dynamic_answer_manager = DynamicAnswerManager(self)

        # Only used for non-frame entities
        self._non_geometric = ontology_object.shape in (Shape.AUDIO, Shape.TEXT)

        self._frames_to_instance_data: Dict[int, ObjectInstance.FrameData] = {}

    def is_assigned_to_label_row(self) -> Optional[LabelRowV2]:
        """Checks if the object instance is assigned to a label row.

        Returns:
            The LabelRowV2 instance if assigned, otherwise None.
        """
        return self._parent

    @property
    def object_hash(self) -> str:
        """A unique identifier for the object instance.

        Returns:
            The unique object hash.
        """
        return self._object_hash

    @property
    def ontology_item(self) -> Object:
        """The ontology object associated with this instance.

        Returns:
            The ontology object.
        """
        return self._ontology_object

    @property
    def feature_hash(self) -> str:
        """Feature node hash from the project ontology.

        Returns:
            The feature node hash.
        """
        return self._ontology_object.feature_node_hash

    @property
    def object_name(self) -> str:
        """Object name from the project ontology.

        Returns:
            The object name.
        """
        return self._ontology_object.name

    @property
    def _last_frame(self) -> Union[int, float]:
        if self._parent is None or self._parent.data_type is DataType.DICOM:
            return float("inf")
        else:
            return self._parent.number_of_frames

    @property
    def range_list(self) -> Ranges | None:
        if self._non_geometric:
            non_geometric_annotation = self._get_non_geometric_annotation()
            if non_geometric_annotation is None:
                return None

            coordinates = non_geometric_annotation.coordinates

            if isinstance(coordinates, (AudioCoordinates, TextCoordinates)):
                return coordinates.range
            else:
                return None

        else:
            raise LabelRowError(
                "No ranges available for this object instance."
                "Please ensure the object instance was created with "
                "the range_only property to True (via a range aware shape)"
                "You can do ObjectInstance(audio_ontology_object) to achieve this."
            )

    @property
    def range_html(self) -> Optional[HtmlRanges]:
        if not self._non_geometric:
            return None

        non_geometric_annotation = self._get_non_geometric_annotation()
        if non_geometric_annotation is None:
            return None

        coordinates = non_geometric_annotation.coordinates

        if isinstance(coordinates, HtmlCoordinates):
            return coordinates.range
        else:
            return None

    def is_range_only(self) -> bool:
        return self._non_geometric

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
        is_dynamic: Optional[bool] = None,
    ) -> Union[str, Option, Iterable[Option], AnswersForFrames, None]:
        """Get the answer set for a given ontology Attribute. Returns `None` if the attribute is not yet answered.

        For the ChecklistAttribute, it returns None if and only if
        the attribute is nested and the parent is unselected. Otherwise, if not yet answered it will return an empty
        list.

        Args:
            attribute: The ontology attribute to get the answer for.
            filter_answer: A filter for a specific answer value. Only applies to dynamic attributes.
            filter_frame: A filter for a specific frame. Only applies to dynamic attributes.
            is_dynamic: Optionally specify whether a dynamic answer is expected or not. This will throw if it is
                set incorrectly according to the attribute. Set this to narrow down the return type.

        Returns:
            If the attribute is static, then the answer value is returned, assuming an answer value has already been
            set. If the attribute is dynamic, the AnswersForFrames object is returned.
        """
        if attribute is None:
            attribute = self._ontology_object.attributes[0]
        elif not self._is_attribute_valid_child_of_object_instance(attribute):
            raise LabelRowError("The attribute is not a valid child of the classification.")
        elif not attribute.dynamic and not self._is_selectable_child_attribute(attribute):
            return None

        if is_dynamic is not None and is_dynamic is not attribute.dynamic:
            raise LabelRowError(
                f"The attribute is {'dynamic' if attribute.dynamic else 'static'}, but is_dynamic is set to "
                f"{is_dynamic}."
            )

        if attribute.dynamic:
            return self._dynamic_answer_manager.get_answer(attribute, filter_answer, filter_frame)

        static_answer = self._static_answer_map[attribute.feature_node_hash]

        if not static_answer.is_answered():
            if isinstance(attribute, ChecklistAttribute):
                return []
            return None

        return static_answer.get()

    def set_answer(
        self,
        answer: Union[str, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
    ) -> None:
        """Set the answer for a given ontology Attribute. This is the equivalent of e.g. selecting a checkbox in the
        UI after drawing the ObjectInstance. There is only one answer per ObjectInstance per Attribute, unless
        the attribute is dynamic (check the args list for more instructions on how to set dynamic answers).

        Args:
            answer: The answer to set.
            attribute: The ontology attribute to set the answer for. If not set, this will be attempted to be
                inferred.  For answers to :class:`encord.objects.common.RadioAttribute` or
                :class:`encord.objects.common.ChecklistAttribute`, this can be inferred automatically. For
                :class:`encord.objects.common.TextAttribute`, this will only be inferred there is only one possible
                TextAttribute to set for the entire object instance. Otherwise, a
                :class:`encord.exceptionsLabelRowError` will be thrown.
            frames: Only relevant for dynamic attributes. The frames to set the answer for. If `None`, the
                answer is set for all frames that this object currently has set coordinates for (also overwriting
                current answers). This will not automatically propagate the answer to new frames that are added in the
                future.
                If this is anything but `None` for non-dynamic attributes, this will
                throw a ValueError.
            overwrite: If `True`, the answer will be overwritten if it already exists. If `False`, this will throw
                a LabelRowError if the answer already exists. This argument is ignored for dynamic attributes.
            manual_annotation: If `True`, the answer will be marked as manually annotated. This arg defaults to
                DEFAULT_MANUAL_ANNOTATION.
        """
        if attribute is None:
            attribute = _infer_attribute_from_answer(self._ontology_object.attributes, answer)
        if not self._is_attribute_valid_child_of_object_instance(attribute):
            raise LabelRowError("The attribute is not a valid child of the object.")
        elif not attribute.dynamic and not self._is_selectable_child_attribute(attribute):
            raise LabelRowError(
                "Setting a nested attribute is only possible if all parent attributes have been selected."
            )
        elif frames is not None and attribute.dynamic is False:
            raise LabelRowError("Setting frames is only possible for dynamic attributes.")

        if attribute.dynamic:
            self._dynamic_answer_manager.set_answer(answer, attribute, frames)
            return

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        if static_answer.is_answered() and overwrite is False:
            raise LabelRowError(
                "The answer to this attribute was already set. Set `overwrite` to `True` if you want to"
                "overwrite an existing answer to an attribute."
            )
        static_answer.set(answer, manual_annotation=manual_annotation)

    def set_answer_from_list(self, answers_list: List[Dict[str, Any]]) -> None:
        """This is a low level helper function and should usually not be used directly.

        Sets the answer for the classification from a dictionary.

        Args:
            answers_list: The list of dictionaries to set the answer from.
        """
        grouped_answers = defaultdict(list)

        for answer_dict in answers_list:
            attribute = _get_attribute_by_hash(answer_dict["featureHash"], self._ontology_object.attributes)
            if attribute is None:
                raise LabelRowError(
                    "One of the attributes does not exist in the ontology. Cannot create a valid LabelRow."
                )
            if not self._is_attribute_valid_child_of_object_instance(attribute):
                raise LabelRowError(
                    "One of the attributes set for a classification is not a valid child of the classification. "
                    "Cannot create a valid LabelRow."
                )

            grouped_answers[attribute.feature_node_hash].append(answer_dict)

        #
        # UI structures answers for checkboxes differently from SDK.
        # It has separate answer dict with the same feature hash rather than just one dict with multiple answers,
        # as SDK expects.
        # So until we aligned the models, we need to introduce additional adaptation layer, that groups separate
        # dictionaries with one answer into one with multiple answer.
        # This is a hotfix rather than a proper solution.
        # TODO: agree on a one correct way to represent the checklist response, and change the SDK accordingly.
        #

        for feature_hash, answers_list in grouped_answers.items():
            attribute = _get_attribute_by_hash(feature_hash, self._ontology_object.attributes)
            assert attribute  # we already checked that attribute is not null above. So just silencing this for now
            self._set_answer_from_grouped_list(attribute, answers_list)

    @staticmethod
    def _merge_answers_to_non_overlapping_ranges(ranges: List[Tuple[Range, Set[str]]]) -> List[Tuple[Range, Set[str]]]:
        ranges.sort(key=lambda x: x[0].start)

        edges: List[Tuple[int, bool, Set[str]]] = []
        for r, option_ids in ranges:
            edges.extend(((r.start, True, set(option_ids)), (r.end, False, set(option_ids))))
        edges.sort(key=lambda x: x[0])

        result_ranges: Dict[Tuple[int, int], Tuple[Range, Set[str]]] = {}

        prev = 0
        prev_state: Set[str] = set()
        prev_close = False

        for frame_num, is_start, options in edges:
            if is_start:
                new_state = prev_state.union(options)
                start = prev
                end = frame_num - int((len(prev_state) > 0))
                prev_close = False
            else:
                start = prev + int(prev_close)
                end = frame_num
                prev_close = True
                new_state = prev_state.difference(options)

            if len(prev_state) > 0:
                if (start, end) in result_ranges:
                    result_ranges[(start, end)][1].update(prev_state.copy())
                else:
                    result_ranges[(start, end)] = (
                        Range(start, end),
                        prev_state.copy(),
                    )

            prev_state = new_state
            prev = frame_num

        return list(result_ranges.values())

    def _set_answer_from_grouped_list(self, attribute: Attribute, answers_list: List[Dict[str, Any]]) -> None:
        if isinstance(attribute, ChecklistAttribute):
            if not attribute.dynamic:
                options = []
                for answer_dict in answers_list:
                    for answer in answer_dict["answers"]:
                        feature_hash = answer["featureHash"]
                        option = attribute.get_child_by_hash(feature_hash, type_=Option)
                        options.append(option)

                self._set_answer_unsafe(options, attribute, None)
            else:
                all_feature_hashes: Set[str] = set()
                ranges = []
                for answer_dict in answers_list:
                    feature_hashes: Set[str] = {answer["featureHash"] for answer in answer_dict["answers"]}
                    all_feature_hashes.update(feature_hashes)
                    for frame_range in ranges_list_to_ranges(answer_dict["range"]):
                        ranges.append((frame_range, feature_hashes))

                options_cache = {
                    feature_hash: attribute.get_child_by_hash(feature_hash, type_=Option)
                    for feature_hash in all_feature_hashes
                }

                for frame_range, feature_hashes in self._merge_answers_to_non_overlapping_ranges(ranges):
                    options = [options_cache[feature_hash] for feature_hash in feature_hashes]
                    self._set_answer_unsafe(options, attribute, [frame_range])
        else:
            for answer in answers_list:
                self._set_answer_from_dict(answer, attribute)

    def delete_answer(
        self,
        attribute: Attribute,
        filter_answer: Optional[Union[str, Option, Iterable[Option]]] = None,
        filter_frame: Optional[int] = None,
    ) -> None:
        """Reset the answer of an attribute as if it was never set.

        Args:
            attribute: The attribute to delete the answer for.
            filter_answer: A filter for a specific answer value. Delete only answers with the provided value.
                Only applies to dynamic attributes.
            filter_frame: A filter for a specific frame. Only applies to dynamic attributes.
        """
        if attribute.dynamic:
            self._dynamic_answer_manager.delete_answer(attribute, filter_frame, filter_answer)
            return

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        static_answer.unset()

    def check_within_range(self, frame: int) -> None:
        """Check if the given frame is within the acceptable range.

        Args:
            frame: The frame number to check.

        Raises:
            LabelRowError: If the frame is out of the acceptable range.
        """
        if frame < 0 or frame >= self._last_frame:
            raise LabelRowError(
                f"The supplied frame of `{frame}` is not within the acceptable bounds of `0` to `{self._last_frame}`."
            )

    def set_for_frames(
        self,
        coordinates: Coordinates,
        frames: Frames = 0,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        """Place the object onto the specified frame(s).

        If the object already exists on the frame and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            coordinates: The coordinates of the object in the frame.
                This will throw an error if the type of the coordinates does not match the type of the attribute in the object instance.
            frames: The frames to add the object instance to. Defaults to the first frame for convenience.
            overwrite: If `True`, overwrite existing data for the given frames.
                This will not reset all the non-specified values.
                If `False` and data already exists for the given frames, raises an error.
            created_at: Optionally specify the creation time of the object instance on this frame.
                Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the object instance on this frame.
                Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the object instance on this frame.
                Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the object instance on this frame.
                Defaults to the current SDK user.
            confidence: Optionally specify the confidence of the object instance on this frame. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the object instance on this frame was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
            is_deleted: Should only be set by internal functions.
        """
        if self._non_geometric:
            if not isinstance(coordinates, tuple(NON_GEOMETRIC_COORDINATES)):
                raise LabelRowError("Expecting non-geometric coordinate type")

            elif frames != 0:
                raise LabelRowError(
                    f"For objects with a non-geometric shape (e.g. {Shape.TEXT} and {Shape.AUDIO}), "
                    f"There is only one frame. Please ensure `set_for_frames` is called with `frames=0`."
                )

        frames_list = frames_class_to_frames_list(frames)

        for frame in frames_list:
            existing_frame_data = self._frames_to_instance_data.get(frame)

            if overwrite is False and existing_frame_data is not None:
                raise LabelRowError(
                    "Cannot overwrite existing data for a frame. Set `overwrite` to `True` to overwrite."
                )

            check_coordinate_type(coordinates, self._ontology_object, self._parent)

            if isinstance(coordinates, (TextCoordinates, AudioCoordinates)):
                for non_geometric_range in coordinates.range:
                    self.check_within_range(non_geometric_range.end)
            else:
                self.check_within_range(frame)

            if existing_frame_data is None:
                existing_frame_data = ObjectInstance.FrameData(
                    coordinates=coordinates, object_frame_instance_info=ObjectInstance.FrameInfo()
                )
                self._frames_to_instance_data[frame] = existing_frame_data

            existing_frame_data.object_frame_instance_info.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                reviews=reviews,
                is_deleted=is_deleted,
            )
            existing_frame_data.coordinates = coordinates

            if self._parent:
                self._parent.add_to_single_frame_to_hashes_map(self, frame)

    def _get_non_geometric_annotation(self) -> Optional[Annotation]:
        # Non-geometric annotations (e.g. Audio and Text) only have one frame.
        if 0 not in self._frames_to_instance_data:
            return None
        else:
            return self.get_annotation(0)

    def get_annotation(self, frame: Union[int, str] = 0) -> Annotation:
        """Get the annotation for the object instance on the specified frame.

        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.

        Returns:
            Annotation: The annotation for the specified frame.

        Raises:
            LabelRowError: If the frame is not present in the label row.
        """
        if self._non_geometric and frame != 0:
            raise LabelRowError(
                'This annotation data for this object instance is stored on only one "frame". '
                "Use `get_annotation(0)` to get the frame data of the first frame."
            )
        if isinstance(frame, str):
            # TODO: this check should be consistent for both string and integer frames,
            #       but currently it is not possible due to the parsing logic
            if not self._parent:
                raise LabelRowError("Cannot get annotation for an object instance that is not assigned to a label row.")

            frame_num = self._parent.get_frame_number(frame)
            if frame_num is None:
                raise LabelRowError(f"Image hash {frame} is not present in the label row.")
        else:
            frame_num = frame

        return self.Annotation(self, frame_num)

    def copy(self) -> ObjectInstance:
        """Create an exact copy of this ObjectInstance.

        The new copy will have a new object hash and will not be associated with any `LabelRowV2`.
        This is useful for adding the semantically same ObjectInstance to multiple `LabelRowV2`s.

        Returns:
            ObjectInstance: A new ObjectInstance that is a copy of the current instance.
        """
        ret = ObjectInstance(self._ontology_object)
        ret._frames_to_instance_data = deepcopy(self._frames_to_instance_data)
        ret._static_answer_map = deepcopy(self._static_answer_map)
        ret._dynamic_answer_manager = self._dynamic_answer_manager.copy()
        return ret

    def get_annotations(self) -> List[Annotation]:
        """Get all annotations for the object instance on all frames it has been placed on.

        Returns:
            List[Annotation]: A list of `ObjectInstance.Annotation` in order of available frames.
        """
        return [self.get_annotation(frame_num) for frame_num in sorted(self._frames_to_instance_data.keys())]

    def get_annotation_frames(self) -> set[int]:
        """Get all annotations for the object instance on all frames it has been placed on.

        Returns:
            List[Annotation]: A list of `ObjectInstance.Annotation` in order of available frames.
        """
        return {self.get_annotation(frame_num).frame for frame_num in sorted(self._frames_to_instance_data.keys())}

    def remove_from_frames(self, frames: Frames) -> None:
        """Remove the object instance from the specified frames.

        Args:
            frames: The frames from which to remove the object instance.
        """
        if self._non_geometric and frames != 0:
            raise LabelRowError(
                f"For objects with a non-geometric shape (e.g. {Shape.TEXT} and {Shape.AUDIO}), "
                f"There is only one frame. Please ensure `remove_from_frames` is called with `frames=0`."
            )

        frames_list = frames_class_to_frames_list(frames)
        for frame in frames_list:
            self._frames_to_instance_data.pop(frame)

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames_list, self.object_hash)

    def is_valid(self) -> None:
        """Check if the ObjectInstance is valid.

        Raises:
            LabelRowError: If the ObjectInstance is not on any frames.
        """
        if len(self._frames_to_instance_data) == 0:
            raise LabelRowError("ObjectInstance is not on any frames. Please add it to at least one frame.")

        self.are_dynamic_answers_valid()

    def are_dynamic_answers_valid(self) -> None:
        """Validate if there are any dynamic answers on frames that have no coordinates.

        Raises:
            LabelRowError: If there are dynamic answers on frames without coordinates.
        """
        dynamic_frames = set(self._dynamic_answer_manager.frames())
        local_frames = self.get_annotation_frames()

        if not len(dynamic_frames - local_frames) == 0:
            raise LabelRowError(
                "There are some dynamic answers on frames that have no coordinates. "
                "Please ensure that all the dynamic answers are only on frames where coordinates "
                "have been set previously."
            )

    class Annotation:
        """Represents an annotation for a specific frame of an ObjectInstance.

        Allows setting or getting data for the ObjectInstance on the given frame number.
        """

        def __init__(self, object_instance: ObjectInstance, frame: int):
            self._object_instance = object_instance
            self._frame = frame

        @property
        def frame(self) -> int:
            return self._frame

        @property
        def coordinates(self) -> Coordinates:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().coordinates

        @coordinates.setter
        def coordinates(self, coordinates: Coordinates) -> None:
            self._check_if_frame_view_is_valid()
            self._object_instance.set_for_frames(coordinates, self._frame, overwrite=True)

        @property
        def created_at(self) -> datetime:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.created_at

        @created_at.setter
        def created_at(self, created_at: datetime) -> None:
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.created_at = created_at

        @property
        def created_by(self) -> Optional[str]:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.created_by

        @created_by.setter
        def created_by(self, created_by: Optional[str]) -> None:
            """Set the created_by field with a user email or None if it should default to the current user of the SDK."""
            self._check_if_frame_view_is_valid()
            if created_by is not None:
                check_email(created_by)
            self._get_object_frame_instance_data().object_frame_instance_info.created_by = created_by

        @property
        def last_edited_at(self) -> datetime:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.last_edited_at

        @last_edited_at.setter
        def last_edited_at(self, last_edited_at: datetime) -> None:
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.last_edited_at = last_edited_at

        @property
        def last_edited_by(self) -> Optional[str]:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.last_edited_by

        @last_edited_by.setter
        def last_edited_by(self, last_edited_by: Optional[str]) -> None:
            """Set the last_edited_by field with a user email or None if it should default to the current user of the SDK."""
            self._check_if_frame_view_is_valid()
            if last_edited_by is not None:
                check_email(last_edited_by)
            self._get_object_frame_instance_data().object_frame_instance_info.last_edited_by = last_edited_by

        @property
        def confidence(self) -> float:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.confidence

        @confidence.setter
        def confidence(self, confidence: float) -> None:
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.confidence = confidence

        @property
        def manual_annotation(self) -> bool:
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.manual_annotation

        @manual_annotation.setter
        def manual_annotation(self, manual_annotation: bool) -> None:
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.manual_annotation = manual_annotation

        @property
        def reviews(self) -> Optional[List[Dict[str, Any]]]:
            """Get the reviews for this object on this frame.

            Returns:
                Optional[List[Dict[str, Any]]]: A list of review dictionaries, if any.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.reviews

        @property
        def is_deleted(self) -> Optional[bool]:
            """Check if the object instance is marked as deleted on this frame.

            Returns:
                Optional[bool]: `True` if deleted, `False` otherwise, or `None` if not set.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.is_deleted

        def _get_object_frame_instance_data(self) -> ObjectInstance.FrameData:
            return self._object_instance._frames_to_instance_data[self._frame]

        def _check_if_frame_view_is_valid(self) -> None:
            if self._frame not in self._object_instance._frames_to_instance_data:
                raise LabelRowError(
                    "Trying to use an ObjectInstance.Annotation for an ObjectInstance that is not on the frame"
                )

    @dataclass
    class FrameInfo:
        """Contains metadata information about a frame."""

        created_at: datetime = field(default_factory=datetime.now)
        created_by: Optional[str] = None
        """None defaults to the user of the SDK once uploaded to the server."""
        last_edited_at: datetime = field(default_factory=datetime.now)
        last_edited_by: Optional[str] = None
        """None defaults to the user of the SDK once uploaded to the server."""
        confidence: float = DEFAULT_CONFIDENCE
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
        reviews: Optional[List[dict]] = None
        is_deleted: Optional[bool] = None

        @staticmethod
        def from_dict(d: dict) -> ObjectInstance.FrameInfo:
            """Create a FrameInfo instance from a dictionary.

            Args:
                d: A dictionary containing frame information.

            Returns:
                ObjectInstance.FrameInfo: An instance of FrameInfo.
            """
            if "lastEditedAt" in d and d["lastEditedAt"] is not None:
                last_edited_at = parse_datetime(d["lastEditedAt"])
            else:
                last_edited_at = datetime.now()

            return ObjectInstance.FrameInfo(
                created_at=parse_datetime(d["createdAt"]),
                created_by=d["createdBy"],
                last_edited_at=last_edited_at,
                last_edited_by=d.get("lastEditedBy"),
                confidence=d["confidence"],
                manual_annotation=d.get("manualAnnotation", True),
                reviews=d.get("reviews"),
                is_deleted=d.get("isDeleted"),
            )

        def update_from_optional_fields(
            self,
            created_at: Optional[datetime] = None,
            created_by: Optional[str] = None,
            last_edited_at: Optional[datetime] = None,
            last_edited_by: Optional[str] = None,
            confidence: Optional[float] = None,
            manual_annotation: Optional[bool] = None,
            reviews: Optional[List[Dict[str, Any]]] = None,
            is_deleted: Optional[bool] = None,
        ) -> None:
            """Update the FrameInfo fields with the specified values.

            Args:
                created_at: Optional creation time.
                created_by: Optional creator identifier.
                last_edited_at: Optional last edited time.
                last_edited_by: Optional last editor identifier.
                confidence: Optional confidence value.
                manual_annotation: Optional manual annotation flag.
                reviews: Optional list of reviews.
                is_deleted: Optional deleted flag.
            """
            self.created_at = created_at or self.created_at
            if created_by is not None:
                self.created_by = created_by
            self.last_edited_at = last_edited_at or self.last_edited_at
            if last_edited_by is not None:
                self.last_edited_by = last_edited_by
            if confidence is not None:
                self.confidence = confidence
            if manual_annotation is not None:
                self.manual_annotation = manual_annotation
            if reviews is not None:
                self.reviews = reviews
            if is_deleted is not None:
                self.is_deleted = is_deleted

    @dataclass
    class FrameData:
        """Data class for storing frame-specific data.

        Attributes:
            coordinates (Coordinates): The coordinates associated with the frame.
            object_frame_instance_info (ObjectInstance.FrameInfo): The frame's metadata information.
        """

        coordinates: Coordinates
        object_frame_instance_info: ObjectInstance.FrameInfo
        # Probably the above can be flattened out into this class.

    def _set_answer_unsafe(
        self,
        answer: Union[str, Option, Iterable[Option]],
        attribute: Attribute,
        ranges: Optional[Ranges],
    ) -> None:
        if attribute.dynamic:
            self._dynamic_answer_manager.set_answer(answer, attribute, frames=ranges)
        else:
            static_answer = self._static_answer_map[attribute.feature_node_hash]
            static_answer.set(answer)

    def _set_answer_from_dict(self, answer_dict: Dict[str, Any], attribute: Attribute) -> None:
        if attribute.dynamic:
            ranges = ranges_list_to_ranges(answer_dict["range"])
        else:
            ranges = None

        if isinstance(attribute, TextAttribute):
            self._set_answer_unsafe(answer_dict["answers"], attribute, ranges)
        elif isinstance(attribute, RadioAttribute):
            if len(answer_dict["answers"]) == 1:
                feature_hash = answer_dict["answers"][0]["featureHash"]
                option = attribute.get_child_by_hash(feature_hash, type_=Option)
                self._set_answer_unsafe(option, attribute, ranges)
        elif isinstance(attribute, ChecklistAttribute):
            options = []
            for answer in answer_dict["answers"]:
                feature_hash = answer["featureHash"]
                option = attribute.get_child_by_hash(feature_hash, type_=Option)
                options.append(option)
            self._set_answer_unsafe(options, attribute, ranges)
        else:
            raise NotImplementedError(f"The attribute type {type(attribute)} is not supported.")

    def _is_attribute_valid_child_of_object_instance(self, attribute: Attribute) -> bool:
        is_static_child = attribute.feature_node_hash in self._static_answer_map
        is_dynamic_child = self._dynamic_answer_manager.is_valid_dynamic_attribute(attribute)
        return is_dynamic_child or is_static_child

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        ontology_object = self._ontology_object
        for search_attribute in ontology_object.attributes:
            if search_attribute.dynamic:
                continue

            if _search_child_attributes(attribute, search_attribute, self._static_answer_map):
                return True
        return False

    def _get_all_static_answers(self) -> List[Answer]:
        return list(self._static_answer_map.values())

    def _get_all_dynamic_answers(self) -> List[Tuple[Answer, Ranges]]:
        return self._dynamic_answer_manager.get_all_answers()

    def __repr__(self) -> str:
        return (
            f"ObjectInstance(object_hash={self._object_hash}, object_name={self._ontology_object.name}, "
            f"feature_hash={self._ontology_object.feature_node_hash})"
        )

    def __hash__(self) -> int:
        return hash(id(self))

    def __lt__(self, other: ObjectInstance) -> bool:
        return self._object_hash < other._object_hash


def check_coordinate_type(coordinates: Coordinates, ontology_object: Object, parent: Optional[LabelRowV2]) -> None:
    """Check if the coordinate type matches the expected type for the ontology object.

    Args:
        coordinates (Coordinates): The coordinates to check.
        ontology_object (Object): The ontology object to check against.
        parent (LabelRowV2): The parent label row (if any) of the ontology object.

    Raises:
        LabelRowError: If the coordinate type does not match the expected type.
    """
    expected_coordinate_types = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[ontology_object.shape]
    if all(
        not isinstance(coordinates, expected_coordinate_type) for expected_coordinate_type in expected_coordinate_types
    ):
        raise LabelRowError(
            f"Expected coordinates of one of the following types: `{expected_coordinate_types}`, but got type `{type(coordinates)}`."
        )

    # An ontology object with `Text` shape can have both coordinates `HtmlCoordinates` and `TextCoordinates`
    # Therefore, we need to further check the file type, to ensure that `HtmlCoordinates` are only used for
    # HTML files, and `TextCoordinates` are only used for plain text files.
    if isinstance(coordinates, TextCoordinates):
        if parent is not None and parent == "text/html":
            raise LabelRowError(f"Expected coordinates of type {HtmlCoordinates}`, but got type `{type(coordinates)}`.")
    elif isinstance(coordinates, HtmlCoordinates):
        if parent is not None and parent.file_type != "text/html":
            raise LabelRowError(
                "For non-html labels, ensure the `range` property " "is set when instantiating the TextCoordinates."
            )


class DynamicAnswerManager:
    """Manages dynamic answers for different frames of an ObjectInstance.

    This class is an internal helper class and should not be interacted with directly by the user.
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
        """Check if the attribute is a valid dynamic attribute.

        Args:
            attribute (Attribute): The attribute to check.

        Returns:
            bool: True if the attribute is valid, False otherwise.
        """
        return any(
            answer.ontology_attribute.feature_node_hash == attribute.feature_node_hash
            for answer in self._dynamic_uninitialised_answer_options
        )

    def delete_answer(
        self,
        attribute: Attribute,
        frames: Optional[Frames] = None,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
    ) -> None:
        """Delete the answer for a given attribute and frames.

        Args:
            attribute (Attribute): The attribute to delete the answer for.
            frames (Optional[Frames]): The frames to delete the answer for.
            filter_answer (Union[str, Option, Iterable[Option], None]): The specific answer to delete.
        """
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
                if self._frames_to_answers[frame] == set():
                    del self._frames_to_answers[frame]
                self._answers_to_frames[to_remove_answer].remove(frame)
                if self._answers_to_frames[to_remove_answer] == set():
                    del self._answers_to_frames[to_remove_answer]

    def set_answer(
        self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Optional[Frames] = None
    ) -> None:
        """Set the answer for a given attribute and frames.

        Args:
            answer (Union[str, Option, Iterable[Option]]): The answer to set.
            attribute (Attribute): The attribute to set the answer for.
            frames (Optional[Frames]): The frames to set the answer for.
        """
        if frames is None:
            for available_frame_view in self._object_instance.get_annotations():
                self._set_answer(answer, attribute, available_frame_view.frame)
            return
        self._set_answer(answer, attribute, frames)

    def _set_answer(self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Frames) -> None:
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
        """Get answers for a given attribute, filtered by the specified criteria.

        Args:
            attribute (Attribute): The attribute to get the answers for.
            filter_answer (Union[str, Option, Iterable[Option], None]): The specific answer to filter by.
            filter_frames (Optional[Frames]): The specific frames to filter by.

        Returns:
            AnswersForFrames: A list of answers and their associated frames.
        """
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
        """Get all frames that have answers set.

        Returns:
            Iterable[int]: An iterable of frames.
        """
        return self._frames_to_answers.keys()

    def get_all_answers(self) -> List[Tuple[Answer, Ranges]]:
        """Get all answers that are set.

        Returns:
            List[Tuple[Answer, Ranges]]: A list of tuples containing the answer and its associated ranges.
        """
        return [(answer, frames_to_ranges(frames)) for answer, frames in self._answers_to_frames.items()]

    def copy(self) -> DynamicAnswerManager:
        """Create a deep copy of the DynamicAnswerManager instance.

        Returns:
            DynamicAnswerManager: A new instance of DynamicAnswerManager with copied data.
        """
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
    """Data class for storing an answer and its associated frame ranges.

    Attributes:
        answer (Union[str, Option, Iterable[Option]]): The answer set for the frames.
        ranges (Ranges): The ranges representing the frames where the answer is set.

    The ranges are essentially a run-length encoding of the frames where the unique answer is set.
    They are sorted in ascending order.
    """

    answer: Union[str, Option, Iterable[Option]]
    ranges: Ranges


AnswersForFrames = List[AnswerForFrames]
"""
A list of AnswerForFrames objects, representing answers and their associated frame ranges.
"""
