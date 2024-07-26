"""
---
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

from encord.common.time_parser import parse_datetime
from encord.constants.enums import DataType
from encord.exceptions import LabelRowError
from encord.objects import ChecklistAttribute, RadioAttribute, TextAttribute
from encord.objects.answers import (
    Answer,
    _get_static_answer_map,
    get_default_answer_from_attribute,
)
from encord.objects.attributes import Attribute, _get_attribute_by_hash
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    Coordinates,
)
from encord.objects.frames import (
    Frames,
    Range,
    Ranges,
    frames_class_to_frames_list,
    frames_to_ranges,
    ranges_list_to_ranges,
)
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
    """
    An object instance is an object that has coordinates and can be placed on one or multiple frames in a label row.
    """

    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None):
        """
        Initialize an ObjectInstance.

        Args:
            ontology_object: The ontology object associated with this instance.
            object_hash: Optional hash to uniquely identify the object instance. If not provided, a new UUID is generated.
        """
        self._ontology_object = ontology_object
        self._frames_to_instance_data: Dict[int, ObjectInstance.FrameData] = {}
        self._object_hash = object_hash or short_uuid_str()
        self._parent: Optional[LabelRowV2] = None
        """This member should only be manipulated by a LabelRowV2"""

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_object.attributes)
        # feature_node_hash of attribute to the answer.

        self._dynamic_answer_manager = DynamicAnswerManager(self)

    def is_assigned_to_label_row(self) -> Optional[LabelRowV2]:
        """
        Check if the object instance is assigned to a label row.

        Returns:
            The parent LabelRowV2 if assigned, otherwise None.
        """
        return self._parent

    @property
    def object_hash(self) -> str:
        """A unique identifier for the object instance."""
        return self._object_hash

    @property
    def ontology_item(self) -> Object:
        """The ontology object associated with this instance."""
        return self._ontology_object

    @property
    def feature_hash(self) -> str:
        """Feature node hash from the project ontology."""
        return self._ontology_object.feature_node_hash

    @property
    def object_name(self) -> str:
        """Object name from the project ontology."""
        return self._ontology_object.name

    @property
    def _last_frame(self) -> Union[int, float]:
        if self._parent is None or self._parent.data_type is DataType.DICOM:
            return float("inf")
        else:
            return self._parent.number_of_frames

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
        is_dynamic: Optional[bool] = None,
    ) -> Union[str, Option, Iterable[Option], AnswersForFrames, None]:
        """
        Get the answer set for a given ontology Attribute. Returns `None` if the attribute is not yet answered.

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
        """
        Set the answer for a given ontology Attribute. This is the equivalent of e.g. selecting a checkbox in the
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
        """
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

    def delete_answer(
        self,
        attribute: Attribute,
        filter_answer: Optional[Union[str, Option, Iterable[Option]]] = None,
        filter_frame: Optional[int] = None,
    ) -> None:
        """
        This resets the answer of an attribute as if it was never set.

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
        """
        Checks if the provided frame is within the acceptable bounds.

        Args:
            frame: The frame number to check.

        Raises:
            LabelRowError: If the frame is not within the acceptable bounds.
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
        """
        Places the object onto the specified frame. If the object already exists on the frame and overwrite is set to
        `True`, the currently specified values will be overwritten.

        Args:
            coordinates:
                The coordinates of the object in the frame. This will throw an error if the type of the coordinates
                does not match the type of the attribute in the object instance.
            frames:
                The frames to add the object instance to. Defaulting to the first frame for convenience.
            overwrite:
                If `True`, overwrite existing data for the given frames. This will not reset all the
                non-specified values. If `False` and data already exists for the given frames,
                raises an error.
            created_at:
                Optionally specify the creation time of the object instance on this frame. Defaults to `datetime.now()`.
            created_by:
                Optionally specify the creator of the object instance on this frame. Defaults to the current SDK user.
            last_edited_at:
                Optionally specify the last edit time of the object instance on this frame. Defaults to `datetime.now()`.
            last_edited_by:
                Optionally specify the last editor of the object instance on this frame. Defaults to the current SDK
                user.
            confidence:
                Optionally specify the confidence of the object instance on this frame. Defaults to `1.0`.
            manual_annotation:
                Optionally specify whether the object instance on this frame was manually annotated. Defaults to `True`.
            reviews:
                Should only be set by internal functions.
            is_deleted:
                Should only be set by internal functions.
        """
        frames_list = frames_class_to_frames_list(frames)

        for frame in frames_list:
            existing_frame_data = self._frames_to_instance_data.get(frame)

            if overwrite is False and existing_frame_data is not None:
                raise LabelRowError(
                    "Cannot overwrite existing data for a frame. Set `overwrite` to `True` to overwrite."
                )

            check_coordinate_type(coordinates, self._ontology_object)
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

    def get_annotation(self, frame: Union[int, str] = 0) -> Annotation:
        """
        Get the annotation for the object instance on the specified frame.

        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.

        Returns:
            An `Annotation` instance representing the annotation for the specified frame.

        Raises:
            LabelRowError: If the frame or image hash is not valid or not present in the label row.
        """
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
        """
        Creates an exact copy of this ObjectInstance but with a new object hash and without being associated to any
        LabelRowV2. This is useful if you want to add the semantically same ObjectInstance to multiple
        `LabelRowV2`s.

        Returns:
            A new `ObjectInstance` that is a copy of the current instance.
        """
        ret = ObjectInstance(self._ontology_object)
        ret._frames_to_instance_data = deepcopy(self._frames_to_instance_data)
        ret._static_answer_map = deepcopy(self._static_answer_map)
        ret._dynamic_answer_manager = self._dynamic_answer_manager.copy()
        return ret

    def get_annotations(self) -> List[Annotation]:
        """
        Get all annotations for the object instance on all frames it has been placed to.

        Returns:
            A list of `Annotation` instances in order of available frames.
        """
        return [self.get_annotation(frame_num) for frame_num in sorted(self._frames_to_instance_data.keys())]

    def remove_from_frames(self, frames: Frames):
        """
        Remove the object instance from the specified frames.

        Args:
            frames: The frames from which to remove the object instance.
        """
        frames_list = frames_class_to_frames_list(frames)
        for frame in frames_list:
            self._frames_to_instance_data.pop(frame)

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames_list, self.object_hash)

    def is_valid(self) -> None:
        """
        Check if the object instance is valid.

        Raises:
            LabelRowError: If the object instance is not on any frames or if dynamic answers are invalid.
        """
        if len(self._frames_to_instance_data) == 0:
            raise LabelRowError("ObjectInstance is not on any frames. Please add it to at least one frame.")

        self.are_dynamic_answers_valid()

    def are_dynamic_answers_valid(self) -> None:
        """
        Check if there are any dynamic answers on frames that have no coordinates.

        Raises:
            LabelRowError: If there are dynamic answers on frames without coordinates.
        """
        dynamic_frames = set(self._dynamic_answer_manager.frames())
        local_frames = {annotation.frame for annotation in self.get_annotations()}

        if not len(dynamic_frames - local_frames) == 0:
            raise LabelRowError(
                "There are some dynamic answers on frames that have no coordinates. "
                "Please ensure that all the dynamic answers are only on frames where coordinates "
                "have been set previously."
            )

    class Annotation:
        """
        Represents an annotation for a specific frame of an `ObjectInstance`.

        Attributes:
            frame: The frame number for this annotation.
        """

        def __init__(self, object_instance: ObjectInstance, frame: int):
            self._object_instance = object_instance
            self._frame = frame

        @property
        def frame(self) -> int:
            """
            The frame number for this annotation.

            Returns:
                The frame number.
            """
            return self._frame

        @property
        def coordinates(self) -> Coordinates:
            """
            The coordinates of the object instance for this frame.

            Returns:
                The coordinates.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().coordinates

        @coordinates.setter
        def coordinates(self, coordinates: Coordinates) -> None:
            """
            Set the coordinates for the object instance on this frame.

            Args:
                coordinates: The new coordinates to set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            self._object_instance.set_for_frames(coordinates, self._frame, overwrite=True)

        @property
        def created_at(self) -> datetime:
            """
            The creation time of the object instance on this frame.

            Returns:
                The creation time.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.created_at

        @created_at.setter
        def created_at(self, created_at: datetime) -> None:
            """
            Set the creation time of the object instance on this frame.

            Args:
                created_at: The new creation time to set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.created_at = created_at

        @property
        def created_by(self) -> Optional[str]:
            """
            The creator of the object instance on this frame.

            Returns:
                The creator's email or None if not set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.created_by

        @created_by.setter
        def created_by(self, created_by: Optional[str]) -> None:
            """
            Set the creator of the object instance on this frame.

            Args:
                created_by: The email of the creator or None if it should default to the current SDK user.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            if created_by is not None:
                check_email(created_by)
            self._get_object_frame_instance_data().object_frame_instance_info.created_by = created_by

        @property
        def last_edited_at(self) -> datetime:
            """
            The last edit time of the object instance on this frame.

            Returns:
                The last edit time.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.last_edited_at

        @last_edited_at.setter
        def last_edited_at(self, last_edited_at: datetime) -> None:
            """
            Set the last edit time of the object instance on this frame.

            Args:
                last_edited_at: The new last edit time to set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.last_edited_at = last_edited_at

        @property
        def last_edited_by(self) -> Optional[str]:
            """
            The last editor of the object instance on this frame.

            Returns:
                The last editor's email or None if not set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.last_edited_by

        @last_edited_by.setter
        def last_edited_by(self, last_edited_by: Optional[str]) -> None:
            """
            Set the last editor of the object instance on this frame.

            Args:
                last_edited_by: The email of the last editor or None if it should default to the current SDK user.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            if last_edited_by is not None:
                check_email(last_edited_by)
            self._get_object_frame_instance_data().object_frame_instance_info.last_edited_by = last_edited_by

        @property
        def confidence(self) -> float:
            """
            The confidence level of the object instance on this frame.

            Returns:
                The confidence level.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.confidence

        @confidence.setter
        def confidence(self, confidence: float) -> None:
            """
            Set the confidence level of the object instance on this frame.

            Args:
                confidence: The new confidence level to set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.confidence = confidence

        @property
        def manual_annotation(self) -> bool:
            """
            Indicates whether the object instance on this frame was manually annotated.

            Returns:
                True if manually annotated, False otherwise.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.manual_annotation

        @manual_annotation.setter
        def manual_annotation(self, manual_annotation: bool) -> None:
            """
            Set whether the object instance on this frame was manually annotated.

            Args:
                manual_annotation: True if manually annotated, False otherwise.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            self._get_object_frame_instance_data().object_frame_instance_info.manual_annotation = manual_annotation

        @property
        def reviews(self) -> Optional[List[Dict[str, Any]]]:
            """
            Get the reviews for the object instance on this frame.

            Returns:
                A list of reviews or None if no reviews are set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.reviews

        @property
        def is_deleted(self) -> Optional[bool]:
            """
            Indicates whether the object instance on this frame is marked as deleted.

            Returns:
                True if deleted, False otherwise, or None if not set.

            Raises:
                LabelRowError: If the frame view is invalid.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.is_deleted

    @dataclass
    class FrameInfo:
        """
        Stores information about the frame including timestamps, user data, confidence, and annotations.

        Attributes:
            created_at: The datetime when the frame information was created.
            created_by: The user who created the frame information. Defaults to None, which implies the user of the SDK once uploaded to the server.
            last_edited_at: The datetime when the frame information was last edited.
            last_edited_by: The user who last edited the frame information. Defaults to None, which implies the user of the SDK once uploaded to the server.
            confidence: The confidence level of the annotation. Defaults to `DEFAULT_CONFIDENCE`.
            manual_annotation: Indicates if the annotation was done manually. Defaults to `DEFAULT_MANUAL_ANNOTATION`.
            reviews: Optional list of reviews for the frame information.
            is_deleted: Optional flag indicating if the frame information is marked as deleted.
        """

        created_at: datetime = field(default_factory=datetime.now)
        created_by: Optional[str] = None
        last_edited_at: datetime = field(default_factory=datetime.now)
        last_edited_by: Optional[str] = None
        confidence: float = DEFAULT_CONFIDENCE
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
        reviews: Optional[List[dict]] = None
        is_deleted: Optional[bool] = None

        @staticmethod
        def from_dict(d: dict) -> 'FrameInfo':
            """
            Create a `FrameInfo` instance from a dictionary.

            Args:
                d: A dictionary containing the frame information.

            Returns:
                A `FrameInfo` instance populated with the values from the dictionary.
            """
            if "lastEditedAt" in d:
                last_edited_at = parse_datetime(d["lastEditedAt"])
            else:
                last_edited_at = datetime.now()

            return ObjectInstance.FrameInfo(
                created_at=parse_datetime(d["createdAt"]),
                created_by=d["createdBy"],
                last_edited_at=last_edited_at,
                last_edited_by=d.get("lastEditedBy"),
                confidence=d["confidence"],
                manual_annotation=d["manualAnnotation"],
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
            """
            Update the frame information with specified optional fields.

            Args:
                created_at: Optional new creation time.
                created_by: Optional new creator's email.
                last_edited_at: Optional new last edit time.
                last_edited_by: Optional new last editor's email.
                confidence: Optional new confidence level.
                manual_annotation: Optional new manual annotation flag.
                reviews: Optional new list of reviews.
                is_deleted: Optional new deleted status.
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
        """
        Stores the data related to a frame including coordinates and frame information.

        Attributes:
            coordinates: The coordinates associated with the frame.
            object_frame_instance_info: Metadata and additional information about the frame.
        """
        coordinates: Coordinates
        object_frame_instance_info: ObjectInstance.FrameInfo

    def check_coordinate_type(coordinates: Coordinates, ontology_object: Object) -> None:
        """
        Check if the coordinates match the expected type for the given ontology object.

        Args:
            coordinates: The coordinates to check.
            ontology_object: The ontology object defining the expected coordinate type.

        Raises:
            LabelRowError: If the coordinates type does not match the expected type.
        """
        expected_coordinate_type = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[ontology_object.shape]
        if not isinstance(coordinates, expected_coordinate_type):
            raise LabelRowError(
                f"Expected a coordinate of type `{expected_coordinate_type}`, but got type `{type(coordinates)}`."
            )

    class DynamicAnswerManager:
        """
        Manages dynamic answers for different frames in an object instance.

        Attributes:
            _object_instance: The object instance this manager is associated with.
            _frames_to_answers: Mapping of frame numbers to sets of answers.
            _answers_to_frames: Mapping of answers to sets of frame numbers.
            _dynamic_uninitialised_answer_options: Set of possible dynamic answers that are uninitialized.
        """

        def __init__(self, object_instance: ObjectInstance):
            self._object_instance = object_instance
            self._frames_to_answers: Dict[int, Set[Answer]] = defaultdict(set)
            self._answers_to_frames: Dict[Answer, Set[int]] = defaultdict(set)

            self._dynamic_uninitialised_answer_options: Set[Answer] = self._get_dynamic_answers()

        def is_valid_dynamic_attribute(self, attribute: Attribute) -> bool:
            """
            Check if the given attribute is a valid dynamic attribute.

            Args:
                attribute: The attribute to check.

            Returns:
                True if the attribute is a valid dynamic attribute, False otherwise.
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
            """
            Delete answers for the given attribute from specified frames.

            Args:
                attribute: The attribute whose answers should be deleted.
                frames: Optional frames from which to remove answers. If None, all frames are considered.
                filter_answer: Optional specific answer to filter by for deletion.
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

                    if answer_object.ontology_attribute == attribute:
                        to_remove_answer = answer_object
                        break

                if to_remove_answer is not None:
                    self._frames_to_answers[frame].remove(to_remove_answer)
                    if not self._frames_to_answers[frame]:
                        del self._frames_to_answers[frame]
                    self._answers_to_frames[to_remove_answer].remove(frame)
                    if not self._answers_to_frames[to_remove_answer]:
                        del self._answers_to_frames[to_remove_answer]

    def set_answer(
        self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, frames: Optional[Frames] = None
    ) -> None:
        """
        Set the provided answer for the specified attribute and frames.

        Args:
            answer: The answer to set, which can be a string, an `Option`, or a list of `Option`s.
            attribute: The attribute for which the answer is being set.
            frames: Optional frames where the answer should be set. If None, the answer is set for all available frames.
        """
        if frames is None:
            for available_frame_view in self._object_instance.get_annotations():
                self._set_answer(answer, attribute, available_frame_view.frame)
            return
        self._set_answer(answer, attribute, frames)

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
        filter_frames: Optional[Frames] = None,
    ) -> AnswersForFrames:
        """
        Retrieve answers for a given attribute, optionally filtered by answer and frame.

        Args:
            attribute: The attribute for which to retrieve answers.
            filter_answer: Optional filter for specific answers. If None, all answers are considered.
            filter_frames: Optional frames to filter by. If None, answers from all frames are considered.

        Returns:
            A list of `AnswerForFrames` objects, each containing an answer and the frames where it is set.
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
        """
        Return all frames that have answers set.

        Returns:
            An iterable of frame numbers that have answers set.
        """
        return self._frames_to_answers.keys()

    def get_all_answers(self) -> List[Tuple[Answer, Ranges]]:
        """
        Retrieve all answers that are set, along with the ranges of frames they cover.

        Returns:
            A list of tuples where each tuple contains an `Answer` and the corresponding `Ranges` of frames.
        """
        return [(answer, frames_to_ranges(frames)) for answer, frames in self._answers_to_frames.items()]

    def copy(self) -> DynamicAnswerManager:
        """
        Create a copy of the current `DynamicAnswerManager` instance.

        Returns:
            A new `DynamicAnswerManager` instance with the same frame-to-answer mappings.
        """
        ret = DynamicAnswerManager(self._object_instance)
        ret._frames_to_answers = deepcopy(self._frames_to_answers)
        ret._answers_to_frames = deepcopy(self._answers_to_frames)
        return ret

    @dataclass
    class AnswerForFrames:
        """
        Represents an answer and the ranges of frames where the answer is set.

        Attributes:
            answer: The answer which can be a string, an `Option`, or a list of `Option`s.
            ranges: The ranges of frames where the answer is set. The ranges are sorted in ascending order and represent
                    a run-length encoding of the frames.
        """
        answer: Union[str, Option, Iterable[Option]]
        ranges: Ranges

    AnswersForFrames = List[AnswerForFrames]
