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
    NoReturn,
    Optional,
    Sequence,
    Union,
)

from dateutil.parser import parse

from encord.constants.enums import DataType
from encord.exceptions import LabelRowError
from encord.objects.classification import Classification
from encord.objects.common import (
    Attribute,
    ChecklistAttribute,
    Option,
    RadioAttribute,
    TextAttribute,
    _get_attribute_by_hash,
    _get_option_by_hash,
)
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.frames import Frames, frames_class_to_frames_list
from encord.objects.internal_helpers import (
    Answer,
    ValueType,
    _get_static_answer_map,
    _infer_attribute_from_answer,
    _search_child_attributes,
)
from encord.objects.utils import check_email, short_uuid_str

if TYPE_CHECKING:
    from encord.objects import LabelRowV2


class ClassificationInstance:
    def __init__(self, ontology_classification: Classification, *, classification_hash: Optional[str] = None):
        self._ontology_classification = ontology_classification
        self._parent: Optional[LabelRowV2] = None
        self._classification_hash = classification_hash or short_uuid_str()

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_classification.attributes)
        # feature_node_hash of attribute to the answer.

        self._frames_to_data: Dict[int, ClassificationInstance.FrameData] = defaultdict(self.FrameData)

    @property
    def classification_hash(self) -> str:
        """A unique identifier for the classification instance."""
        return self._classification_hash

    @classification_hash.setter
    def classification_hash(self, v: Any) -> NoReturn:
        raise LabelRowError("Cannot set the object hash on an instantiated label object.")

    @property
    def ontology_item(self) -> Classification:
        return self._ontology_classification

    @property
    def classification_name(self) -> str:
        """Classification name from the project ontology"""
        return self._ontology_classification.attributes[0].name

    @property
    def feature_hash(self) -> str:
        """Feature node hash from the project ontology"""
        return self._ontology_classification.feature_node_hash

    @property
    def _last_frame(self) -> Union[int, float]:
        if self._parent is None or self._parent.data_type is DataType.DICOM:
            return float("inf")
        else:
            return self._parent.number_of_frames

    def is_assigned_to_label_row(self) -> bool:
        return self._parent is not None

    def set_for_frames(
        self,
        frames: Frames = 0,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        confidence: float = DEFAULT_CONFIDENCE,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        reviews: Optional[List[dict]] = None,
    ) -> None:
        """
        Places the classification onto the specified frame. If the classification already exists on the frame and
        overwrite is set to `True`, the currently specified values will be overwritten.

        Args:
            frames:
                The frame to add the classification instance to. Defaulting to the first frame for convenience.
            overwrite:
                If `True`, overwrite existing data for the given frames. This will not reset all the
                non-specified values. If `False` and data already exists for the given frames,
                raises an error.
            created_at:
                Optionally specify the creation time of the classification instance on this frame. Defaults to `datetime.now()`.
            created_by:
                Optionally specify the creator of the classification instance on this frame. Defaults to the current SDK user.
            last_edited_at:
                Optionally specify the last edit time of the classification instance on this frame. Defaults to `datetime.now()`.
            last_edited_by:
                Optionally specify the last editor of the classification instance on this frame. Defaults to the current SDK
                user.
            confidence:
                Optionally specify the confidence of the classification instance on this frame. Defaults to `1.0`.
            manual_annotation:
                Optionally specify whether the classification instance on this frame was manually annotated. Defaults to `True`.
            reviews:
                Should only be set by internal functions.
        """
        if created_at is None:
            created_at = datetime.now()

        if last_edited_at is None:
            last_edited_at = datetime.now()

        frames_list = frames_class_to_frames_list(frames)

        self._check_classification_already_present(frames_list)

        for frame in frames_list:
            self._check_within_range(frame)
            self._set_frame_and_frame_data(
                frame,
                overwrite=overwrite,
                created_at=created_at,
                created_by=created_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                reviews=reviews,
            )

        if self.is_assigned_to_label_row():
            assert self._parent is not None
            self._parent._add_frames_to_classification(self.ontology_item, frames_list)
            self._parent._add_to_frame_to_hashes_map(self, frames_list)

    def get_annotation(self, frame: Union[int, str] = 0) -> Annotation:
        """
        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.
        """
        if isinstance(frame, str):
            # TODO: this check should be consistent for both string and integer frames,
            #       but currently it is not possible due to the parsing logic
            if not self._parent:
                raise LabelRowError(
                    "Cannot get annotation for a classification instance that is not assigned to a label row."
                )

            frame_num = self._parent.get_frame_number(frame)
            if frame_num is None:
                raise LabelRowError(f"Image hash {frame} is not present in the label row.")
        else:
            frame_num = frame

        return self.Annotation(self, frame_num)

    def remove_from_frames(self, frames: Frames) -> None:
        frame_list = frames_class_to_frames_list(frames)
        for frame in frame_list:
            self._frames_to_data.pop(frame)

        if self.is_assigned_to_label_row():
            assert self._parent is not None
            self._parent._remove_frames_from_classification(self.ontology_item, frame_list)
            self._parent._remove_from_frame_to_hashes_map(frame_list, self.classification_hash)

    def get_annotations(self) -> List[Annotation]:
        """
        Returns:
            A list of `ClassificationInstance.Annotation` in order of available frames.
        """
        ret = []
        for frame_num in sorted(self._frames_to_data.keys()):
            ret.append(self.get_annotation(frame_num))
        return ret

    def is_valid(self) -> None:
        if not len(self._frames_to_data) > 0:
            raise LabelRowError("ClassificationInstance is not on any frames. Please add it to at least one frame.")

    def set_answer(
        self,
        answer: Union[str, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Set the answer for a given ontology Attribute. This is the equivalent of e.g. selecting a checkbox in the
        UI after adding a ClassificationInstance. There is only one answer per ClassificationInstance per Attribute.

        Args:
            answer: The answer to set.
            attribute: The ontology attribute to set the answer for. If not set, this will be attempted to be
                inferred.  For answers to :class:`encord.objects.common.RadioAttribute` or
                :class:`encord.objects.common.ChecklistAttribute`, this can be inferred automatically. For
                :class:`encord.objects.common.TextAttribute`, this will only be inferred there is only one possible
                TextAttribute to set for the entire object instance. Otherwise, a
                :class:`encord.exceptionsLabelRowError` will be thrown.
            overwrite: If `True`, the answer will be overwritten if it already exists. If `False`, this will throw
                a LabelRowError if the answer already exists.
        """
        if attribute is None:
            attribute = _infer_attribute_from_answer(self._ontology_classification.attributes, answer)
        elif not self._is_attribute_valid_child_of_classification(attribute):
            raise LabelRowError("The attribute is not a valid child of the classification.")
        elif not self._is_selectable_child_attribute(attribute):
            raise LabelRowError(
                "Setting a nested attribute is only possible if all parent attributes have been selected."
            )

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        if static_answer.is_answered() and overwrite is False:
            raise LabelRowError(
                "The answer to this attribute was already set. Set `overwrite` to `True` if you want to"
                "overwrite an existing answer to and attribute."
            )

        static_answer.set(answer)

    def set_answer_from_list(self, answers_list: List[Dict[str, Any]]) -> None:
        """
        This is a low level helper function and should not be used directly.

        Sets the answer for the classification from a dictionary.

        Args:
            answers_list: The list to set the answer from.
        """

        for answer_dict in answers_list:
            attribute = _get_attribute_by_hash(answer_dict["featureHash"], self._ontology_classification.attributes)
            if attribute is None:
                raise LabelRowError(
                    "One of the attributes does not exist in the ontology. Cannot create a valid LabelRow."
                )

            if not self._is_attribute_valid_child_of_classification(attribute):
                raise LabelRowError(
                    "One of the attributes set for a classification is not a valid child of the classification. "
                    "Cannot create a valid LabelRow."
                )

            if isinstance(attribute, TextAttribute):
                self._set_answer_unsafe(answer_dict["answers"], attribute)
            elif isinstance(attribute, RadioAttribute):
                if len(answer_dict["answers"]) == 1:
                    # When classification is removed in UI, it keeps the entry about the classification,
                    # but removes the answers.
                    # Thus an empty answers array is equivalent to "no such attribute", and such attribute should be ignored
                    feature_hash = answer_dict["answers"][0]["featureHash"]
                    option = _get_option_by_hash(feature_hash, attribute.options)
                    self._set_answer_unsafe(option, attribute)
            elif isinstance(attribute, ChecklistAttribute):
                options = []
                for answer in answer_dict["answers"]:
                    feature_hash = answer["featureHash"]
                    option = _get_option_by_hash(feature_hash, attribute.options)
                    options.append(option)
                self._set_answer_unsafe(options, attribute)
            else:
                raise NotImplementedError(f"The attribute type {type(attribute)} is not supported.")

    def get_answer(self, attribute: Optional[Attribute] = None) -> Union[str, Option, Iterable[Option], None]:
        """
        Get the answer set for a given ontology Attribute. Returns `None` if the attribute is not yet answered.

        For the ChecklistAttribute, it returns None if and only if
        the attribute is nested and the parent is unselected. Otherwise, if not yet answered it will return an empty
        list.

        Args:
            attribute: The ontology attribute to get the answer for.
        """
        if attribute is None:
            attribute = self._ontology_classification.attributes[0]
        elif not self._is_attribute_valid_child_of_classification(attribute):
            raise LabelRowError("The attribute is not a valid child of the classification.")
        elif not self._is_selectable_child_attribute(attribute):
            return None

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        if not static_answer.is_answered():
            return None

        return static_answer.get()

    def delete_answer(self, attribute: Optional[Attribute] = None) -> None:
        """
        This resets the answer of an attribute as if it was never set.

        Args:
            attribute: The ontology attribute to delete the answer for. If not provided, the first level attribute is
                used.
        """
        if attribute is None:
            attribute = self._ontology_classification.attributes[0]
        elif not self._is_attribute_valid_child_of_classification(attribute):
            raise LabelRowError("The attribute is not a valid child of the classification.")

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        static_answer.unset()

    def copy(self) -> ClassificationInstance:
        """
        Creates an exact copy of this ClassificationInstance but with a new classification hash and without being
        associated to any LabelRowV2. This is useful if you want to add the semantically same
        ClassificationInstance to multiple `LabelRowV2`s.
        """
        ret = ClassificationInstance(self._ontology_classification)
        ret._static_answer_map = deepcopy(self._static_answer_map)
        ret._frames_to_data = deepcopy(self._frames_to_data)
        return ret

    def get_all_static_answers(self) -> List[Answer]:
        """A low level helper function."""
        return list(self._static_answer_map.values())

    class Annotation:
        """
        This class can be used to set or get data for a specific annotation (i.e. the ClassificationInstance for a given
        frame number).
        """

        def __init__(self, classification_instance: ClassificationInstance, frame: int):
            self._classification_instance = classification_instance
            self._frame = frame

        @property
        def frame(self) -> int:
            return self._frame

        @property
        def created_at(self) -> datetime:
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().created_at

        @created_at.setter
        def created_at(self, created_at: datetime) -> None:
            self._check_if_frame_view_valid()
            self._get_object_frame_instance_data().created_at = created_at

        @property
        def created_by(self) -> Optional[str]:
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().created_by

        @created_by.setter
        def created_by(self, created_by: Optional[str]) -> None:
            """
            Set the created_by field with a user email or None if it should default to the current user of the SDK.
            """
            self._check_if_frame_view_valid()
            if created_by is not None:
                check_email(created_by)
            self._get_object_frame_instance_data().created_by = created_by

        @property
        def last_edited_at(self) -> datetime:
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().last_edited_at

        @last_edited_at.setter
        def last_edited_at(self, last_edited_at: datetime) -> None:
            self._check_if_frame_view_valid()
            self._get_object_frame_instance_data().last_edited_at = last_edited_at

        @property
        def last_edited_by(self) -> Optional[str]:
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().last_edited_by

        @last_edited_by.setter
        def last_edited_by(self, last_edited_by: Optional[str]) -> None:
            """
            Set the last_edited_by field with a user email or None if it should default to the current user of the SDK.
            """
            self._check_if_frame_view_valid()
            if last_edited_by is not None:
                check_email(last_edited_by)
            self._get_object_frame_instance_data().last_edited_by = last_edited_by

        @property
        def confidence(self) -> float:
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().confidence

        @confidence.setter
        def confidence(self, confidence: float) -> None:
            self._check_if_frame_view_valid()
            self._get_object_frame_instance_data().confidence = confidence

        @property
        def manual_annotation(self) -> bool:
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().manual_annotation

        @manual_annotation.setter
        def manual_annotation(self, manual_annotation: bool) -> None:
            self._check_if_frame_view_valid()
            self._get_object_frame_instance_data().manual_annotation = manual_annotation

        @property
        def reviews(self) -> Optional[List[dict]]:
            """
            A read only property about the reviews that happened for this object on this frame.
            """
            self._check_if_frame_view_valid()
            return self._get_object_frame_instance_data().reviews

        def _check_if_frame_view_valid(self) -> None:
            if self._frame not in self._classification_instance._frames_to_data:
                raise LabelRowError(
                    "Trying to use an ObjectInstance.Annotation for an ObjectInstance that is not on the frame."
                )

        def _get_object_frame_instance_data(self) -> ClassificationInstance.FrameData:
            return self._classification_instance._frames_to_data[self._frame]

    @dataclass
    class FrameData:
        created_at: datetime = field(default_factory=datetime.now)
        created_by: Optional[str] = None
        confidence: float = DEFAULT_CONFIDENCE
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
        last_edited_at: datetime = field(default_factory=datetime.now)
        last_edited_by: Optional[str] = None
        reviews: Optional[List[dict]] = None

        @staticmethod
        def from_dict(d: dict) -> ClassificationInstance.FrameData:
            if "lastEditedAt" in d:
                last_edited_at = parse(d["lastEditedAt"])
            else:
                last_edited_at = datetime.now()

            return ClassificationInstance.FrameData(
                created_at=parse(d["createdAt"]),
                created_by=d["createdBy"],
                confidence=d["confidence"],
                manual_annotation=d["manualAnnotation"],
                last_edited_at=last_edited_at,
                last_edited_by=d.get("lastEditedBy"),
                reviews=d.get("reviews"),
            )

        def update_from_optional_fields(
            self,
            created_at: Optional[datetime] = None,
            created_by: Optional[str] = None,
            confidence: Optional[float] = None,
            manual_annotation: Optional[bool] = None,
            last_edited_at: Optional[datetime] = None,
            last_edited_by: Optional[str] = None,
            reviews: Optional[List[dict]] = None,
        ) -> None:
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

    def _set_frame_and_frame_data(
        self,
        frame,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        reviews: Optional[List[dict]] = None,
    ):
        existing_frame_data = self._frames_to_data.get(frame)
        if overwrite is False and existing_frame_data is not None:
            raise LabelRowError(
                f"Cannot overwrite existing data for frame `{frame}`. Set `overwrite` to `True` to overwrite."
            )

        if existing_frame_data is None:
            existing_frame_data = self.FrameData()
            self._frames_to_data[frame] = existing_frame_data

        existing_frame_data.update_from_optional_fields(
            created_at, created_by, confidence, manual_annotation, last_edited_at, last_edited_by, reviews
        )

        if self.is_assigned_to_label_row():
            assert self._parent is not None
            self._parent.add_to_single_frame_to_hashes_map(self, frame)

    def _set_answer_unsafe(self, answer: ValueType, attribute: Attribute) -> None:
        self._static_answer_map[attribute.feature_node_hash].set(answer)

    def _is_attribute_valid_child_of_classification(self, attribute: Attribute) -> bool:
        return attribute.feature_node_hash in self._static_answer_map

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        # I have the ontology classification, so I can build the tree from that. Basically do a DFS.
        ontology_classification = self._ontology_classification
        top_attribute = ontology_classification.attributes[0]
        return _search_child_attributes(attribute, top_attribute, self._static_answer_map)

    def _check_within_range(self, frame: int) -> None:
        if frame < 0 or frame >= self._last_frame:
            raise LabelRowError(
                f"The supplied frame of `{frame}` is not within the acceptable bounds of `0` to `{self._last_frame}`."
            )

    def _check_classification_already_present(self, frames: Iterable[int]) -> None:
        if self._parent is None:
            return
        already_present_frame = self._parent._is_classification_already_present(self.ontology_item, frames)
        if already_present_frame is not None:
            raise LabelRowError(
                f"The LabelRowV2, that this classification is part of, already has a classification of the same type "
                f"on frame `{already_present_frame}`. The same type of classification can only be present once per "
                f"frame per LabelRowV2."
            )

    def __repr__(self):
        return (
            f"ClassificationInstance(classification_hash={self.classification_hash}, "
            f"classification_name={self._ontology_classification.attributes[0].name}, "
            f"feature_hash={self._ontology_classification.feature_node_hash})"
        )

    def __lt__(self, other) -> bool:
        return self.classification_hash < other.classification_hash
