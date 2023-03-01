from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)
from uuid import uuid4

from dateutil.parser import parse

from encord.client import EncordClientProject
from encord.constants.enums import DataType
from encord.exceptions import LabelRowError, OntologyError
from encord.objects.common import (
    Attribute,
    AttributeClasses,
    AttributeTypes,
    ChecklistAttribute,
    FlatOption,
    NestableOption,
    Option,
    OptionClasses,
    OptionTypes,
    RadioAttribute,
    Shape,
    TextAttribute,
    _add_attribute,
    _get_attribute_by_hash,
    _get_attributes_by_title,
    _get_option_by_hash,
    _handle_wrong_number_of_found_items,
    attribute_from_dict,
    attributes_to_list_dict,
)
from encord.objects.constants import (
    DATETIME_LONG_STRING_FORMAT,
    DEFAULT_CONFIDENCE,
    DEFAULT_MANUAL_ANNOTATION,
)
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    BoundingBoxCoordinates,
    Coordinates,
    PointCoordinate,
    PolygonCoordinates,
    PolylineCoordinates,
    RotatableBoundingBoxCoordinates,
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
    Answer,
    _get_static_answer_map,
    _infer_attribute_from_answer,
    _search_child_attributes,
    get_answer_from_object,
    get_default_answer_from_attribute,
    set_answer_for_object,
)
from encord.objects.utils import (
    _lower_snake_case,
    check_email,
    check_type,
    does_type_match,
    filter_by_type,
    short_uuid_str,
)
from encord.orm.formatter import Formatter
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus


@dataclass
class Object:
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    uid: int
    name: str
    color: str
    shape: Shape
    feature_node_hash: str
    attributes: List[Attribute] = field(default_factory=list)

    def create_instance(self) -> ObjectInstance:
        """Create a :class:`encord.objects.ObjectInstance` to be used with a label row."""
        return ObjectInstance(self)

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        found_item = _get_attribute_by_hash(feature_node_hash, self.attributes)
        if found_item is None:
            raise OntologyError("Item not found.")
        check_type(found_item, type_)
        return found_item

    def get_child_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _handle_wrong_number_of_found_items(found_items, title, type_)
        return found_items[0]

    def get_children_by_title(
        self,
        title: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        found_items = _get_attributes_by_title(title, self.attributes)
        return filter_by_type(found_items, type_)  # noqa

    @classmethod
    def from_dict(cls, d: dict) -> Object:
        shape_opt = Shape.from_string(d["shape"])
        if shape_opt is None:
            raise TypeError(f"The shape '{d['shape']}' of the object '{d}' is not recognised")

        attributes_ret: List[Attribute] = list()
        if "attributes" in d:
            for attribute_dict in d["attributes"]:
                attributes_ret.append(attribute_from_dict(attribute_dict))

        object_ret = Object(
            uid=int(d["id"]),
            name=d["name"],
            color=d["color"],
            shape=shape_opt,
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
        )

        return object_ret

    def to_dict(self) -> dict:
        ret = dict()
        ret["id"] = str(self.uid)
        ret["name"] = self.name
        ret["color"] = self.color
        ret["shape"] = self.shape.value
        ret["featureNodeHash"] = self.feature_node_hash

        attributes_list = attributes_to_list_dict(self.attributes)
        if attributes_list:
            ret["attributes"] = attributes_list

        return ret

    T = TypeVar("T", bound=Attribute)

    def add_attribute(
        self,
        cls: Type[T],
        name: str,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
        required: bool = False,
        dynamic: bool = False,
    ) -> T:
        """
        Adds an attribute to the object.

        Args:
            cls: attribute type, one of `RadioAttribute`, `ChecklistAttribute`, `TextAttribute`
            name: the user-visible name of the attribute
            local_uid: integer identifier of the attribute. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            feature_node_hash: global identifier of the attribute. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            required: whether the label editor would mark this attribute as 'required'
            dynamic: whether the attribute can have a different answer for the same object across different frames.

        Returns:
            the created attribute that can be further specified with Options, where appropriate

        Raises:
            ValueError: if specified `local_uid` or `feature_node_hash` violate uniqueness constraints
        """
        return _add_attribute(self.attributes, cls, name, [self.uid], local_uid, feature_node_hash, required, dynamic)


@dataclass
class Classification:
    """
    This class is currently in BETA. Its API might change in future minor version releases.

    Represents a whole-image classification as part of Ontology structure. Wraps a single Attribute that describes
    the image in general rather then individual object.
    """

    uid: int
    feature_node_hash: str
    attributes: List[Attribute]

    def create_instance(self) -> ClassificationInstance:
        """Create a :class:`encord.objects.ClassificationInstance` to be used with a label row."""
        return ClassificationInstance(self)

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[AttributeTypes, OptionTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        found_item = _get_attribute_by_hash(feature_node_hash, self.attributes)
        if found_item is None:
            raise OntologyError("Item not found.")
        check_type(found_item, type_)
        return found_item

    def get_child_by_title(
        self,
        title: str,
        type_: Union[OptionTypes, AttributeTypes, None] = None,
    ) -> Union[AttributeClasses, OptionClasses]:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _handle_wrong_number_of_found_items(found_items, title, type_)
        return found_items[0]

    def get_children_by_title(
        self,
        title: str,
        type_: Union[OptionTypes, AttributeTypes, None] = None,
    ) -> List[Union[AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        found_items = _get_attributes_by_title(title, self.attributes)
        return filter_by_type(found_items, type_)  # noqa

    @classmethod
    def from_dict(cls, d: dict) -> Classification:
        attributes_ret: List[Attribute] = list()
        for attribute_dict in d["attributes"]:
            attributes_ret.append(attribute_from_dict(attribute_dict))

        return Classification(
            uid=int(d["id"]),
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
        )

    def to_dict(self) -> dict:
        ret = dict()
        ret["id"] = str(self.uid)
        ret["featureNodeHash"] = self.feature_node_hash

        attributes_list = attributes_to_list_dict(self.attributes)
        if attributes_list:
            ret["attributes"] = attributes_list

        return ret

    T = TypeVar("T", bound=Attribute)

    def add_attribute(
        self,
        cls: Type[T],
        name: str,
        local_uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
        required: bool = False,
    ) -> T:
        """
        Adds an attribute to the classification.

        Args:
            cls: attribute type, one of `RadioAttribute`, `ChecklistAttribute`, `TextAttribute`
            name: the user-visible name of the attribute
            local_uid: integer identifier of the attribute. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            feature_node_hash: global identifier of the attribute. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing ontology
            required: whether the label editor would mark this attribute as 'required'

        Returns:
            the created attribute that can be further specified with Options, where appropriate

        Raises:
            ValueError: if the classification already has an attribute assigned
        """
        if self.attributes:
            raise ValueError("Classification should have exactly one root attribute")
        return _add_attribute(self.attributes, cls, name, [self.uid], local_uid, feature_node_hash, required)

    def __hash__(self):
        return hash(self.feature_node_hash)


OntologyTypes = Union[Type[Object], Type[Classification]]
OntologyClasses = Union[Object, Classification]


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
        return self._classification_hash

    @classification_hash.setter
    def classification_hash(self, v: Any) -> NoReturn:
        raise LabelRowError("Cannot set the object hash on an instantiated label object.")

    @property
    def ontology_item(self) -> Classification:
        return deepcopy(self._ontology_classification)

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
        created_at: datetime = datetime.now(),
        created_by: str = None,
        confidence: int = DEFAULT_CONFIDENCE,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
        last_edited_at: datetime = datetime.now(),
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

    def get_annotation(self, frame: Union[int, str] = 0) -> Annotation:
        """
        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.
        """
        if isinstance(frame, str):
            frame = self._parent.get_frame_number(frame)
        return self.Annotation(self, frame)

    def remove_from_frames(self, frames: Frames) -> None:
        frame_list = frames_class_to_frames_list(frames)
        for frame in frame_list:
            self._frames_to_data.pop(frame)

        if self.is_assigned_to_label_row():
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
        answer: Union[str, Option, Iterable[Option]],
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

        set_answer_for_object(static_answer, answer)

    def set_answer_from_list(self, answers_list: List[Dict[str, Any]]) -> None:
        """
        This is a low level helper function and should not be used directly.

        Sets the answer for the classification from a dictionary.

        Args:
            answer_dict: The dictionary to set the answer from.
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

        return get_answer_from_object(static_answer)

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
        def reviews(self) -> List[dict]:
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
        created_at: datetime = datetime.now()
        created_by: str = None
        confidence: int = DEFAULT_CONFIDENCE
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
        last_edited_at: datetime = datetime.now()
        last_edited_by: Optional[str] = None
        reviews: Optional[List[dict]] = None

        @staticmethod
        def from_dict(d: dict) -> ClassificationInstance.FrameData:
            if "lastEditedAt" in d:
                last_edited_at = parse(d["lastEditedAt"])
            else:
                last_edited_at = None

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
            confidence: Optional[int] = None,
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
        confidence: Optional[int] = None,
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
            self._parent.add_to_single_frame_to_hashes_map(self, frame)

    def _set_answer_unsafe(self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute) -> None:
        static_answer = self._static_answer_map[attribute.feature_node_hash]
        set_answer_for_object(static_answer, answer)

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
            f"object_feature_hash={self._ontology_classification.feature_node_hash})"
        )

    def __lt__(self, other) -> bool:
        return self.classification_hash < other.classification_hash


class LabelRowV2:
    """
    This class represents a single label row. It is corresponding to exactly one data row within a project. It holds all
    the labels for that data row.

    You can access a many metadata fields with this class directly. If you want to read or write labels you will need to
    call :meth:`.initialise_labels()` first. To upload your added labels call :meth:`.save()`.
    """

    def __init__(
        self,
        label_row_metadata: LabelRowMetadata,
        project_client: EncordClientProject,
    ) -> None:
        self._ontology_structure: Optional[OntologyStructure] = None

        self._project_client = project_client
        self._querier = project_client._querier

        self._label_row_read_only_data: LabelRowV2.LabelRowReadOnlyData = self._parse_label_row_metadata(
            label_row_metadata
        )

        self._is_labelling_initialised = False

        self._frame_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        # ^ frames to object and classification hashes

        self._classifications_to_frames: defaultdict[Classification, Set[int]] = defaultdict(set)

        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()
        # ^ conveniently a dict is ordered in Python. Use this to our advantage to keep the labels in order
        # at least at the final objects_index/classifications_index level.

    @property
    def label_hash(self) -> Optional[str]:
        return self._label_row_read_only_data.label_hash

    @property
    def data_hash(self) -> str:
        return self._label_row_read_only_data.data_hash

    @property
    def dataset_hash(self) -> str:
        return self._label_row_read_only_data.dataset_hash

    @property
    def dataset_title(self) -> str:
        return self._label_row_read_only_data.dataset_title

    @property
    def data_title(self) -> str:
        return self._label_row_read_only_data.data_title

    @property
    def data_type(self) -> DataType:
        return self._label_row_read_only_data.data_type

    @property
    def label_status(self) -> LabelStatus:
        return self._label_row_read_only_data.label_status

    @property
    def annotation_task_status(self) -> AnnotationTaskStatus:
        return self._label_row_read_only_data.annotation_task_status

    @property
    def is_shadow_data(self) -> bool:
        return self._label_row_read_only_data.is_shadow_data

    @property
    def created_at(self) -> Optional[datetime]:
        """The creation date of the label row. None if the label row was not yet created."""
        return self._label_row_read_only_data.created_at

    @property
    def last_edited_at(self) -> Optional[datetime]:
        """The time the label row was updated last as a whole. None if the label row was not yet created."""
        return self._label_row_read_only_data.last_edited_at

    @property
    def number_of_frames(self) -> int:
        return self._label_row_read_only_data.number_of_frames

    @property
    def duration(self) -> Optional[float]:
        """Only a value for Video data types."""
        return self._label_row_read_only_data.duration

    @property
    def fps(self) -> Optional[float]:
        """Only a value for Video data types."""
        return self._label_row_read_only_data.fps

    @property
    def data_link(self) -> Optional[str]:
        """
        The data link in either your cloud storage or the encord storage to the underlying object. This will be `None`
        for DICOM series or image groups that have been created without performance optimisations, as there is no
        single underlying file for these data types.
        """
        return self._label_row_read_only_data.data_link

    @property
    def width(self) -> Optional[int]:
        """
        This is `None` for image groups without performance optimisation, as there is no single underlying width
        for this data type.
        """
        return self._label_row_read_only_data.width

    @property
    def height(self) -> Optional[int]:
        """
        This is `None` for image groups without performance optimisation, as there is no single underlying width
        for this data type.
        """
        return self._label_row_read_only_data.height

    @property
    def ontology_structure(self) -> OntologyStructure:
        """Get the corresponding ontology structure"""
        self._check_labelling_is_initalised()
        if self._ontology_structure is None:
            raise LabelRowError("The LabelRowV2 class is in an unexpected state.")

        return self._ontology_structure

    @property
    def is_labelling_initialised(self) -> bool:
        """
        Whether you can start labelling or not. If this is `False`, call the member `.initialise_labels()` to
        read or write specific ObjectInstances or ClassificationInstances.
        """
        return self._is_labelling_initialised

    def initialise_labels(
        self,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
        overwrite: bool = False,
    ) -> None:
        """
        Call this function to start reading or writing labels. This will fetch the labels that are currently stored
        in the Encord server. If you only want to inspect a subset of labels, you can filter them. Please note that if
        you filter the labels, and upload them later, you will effectively delete all the labels that had been filtered
        previously.

        If the label was not yet in progress, this will set the label status to `LabelStatus.LABEL_IN_PROGRESS`.

        You can call this function at any point to overwrite the current labels stored in this class with the most
        up to date labels stored in the Encord servers. This would only matter if you manipulate the labels while
        someone else is working on the labels as well. You would need to supply the `overwrite` parameter to `True`

        Args:
            include_object_feature_hashes: If None all the objects will be included. Otherwise, only objects labels
                will be included of which the feature_hash has been added. WARNING: it is only recommended to use
                this filter if you are reading (not writing) the labels. If you are requesting a subset of objects and
                later, save the label, you will effectively delete all the object instances that are stored in the
                Encord platform, which were not included in this filtered subset.
            include_classification_feature_hashes: If None all the classifications will be included. Otherwise, only
                classification labels will be included of which the feature_hash has been added. WARNING: it is only
                recommended to use this filter if you are reading (not writing) the labels. If you are requesting a
                subset of classifications and later, save the label, you will effectively delete all the
                classification instances that are stored in the Encord platform, which were not included in this
                filtered subset.
            include_reviews: Whether to request read only information about the reviews of the label row.
            overwrite: If the label row was already initialised, you need to set this flag to `True` to overwrite the
                current labels with the labels stored in the Encord server. If this is `False` and the label row was
                already initialised, this function will throw an error.
        """
        if self.is_labelling_initialised and not overwrite:
            raise LabelRowError(
                "You are trying to re-initialise a label row that has already been initialised. This would overwrite "
                "current labels. If this is your intend, set the `overwrite` flag to `True`."
            )

        if self._ontology_structure is None:
            self._refresh_ontology_structure()

        get_signed_url = False
        if self.label_hash is None:
            label_row_dict = self._project_client.create_label_row(self.data_hash)
        else:
            label_row_dict = self._project_client.get_label_row(
                uid=self.label_hash,
                get_signed_url=get_signed_url,
                include_object_feature_hashes=include_object_feature_hashes,
                include_classification_feature_hashes=include_classification_feature_hashes,
                include_reviews=include_reviews,
            )

        self.from_labels_dict(label_row_dict)

    def from_labels_dict(self, label_row_dict: dict, ontology_structure: Optional[OntologyStructure] = None) -> None:
        """
        If you have a label row dictionary in the same format that the Encord servers produce, you can initialise the
        LabelRow from that directly. In most cases you should prefer using the `initialise_labels` method.

        This function also initialises the label row.

        Calling this function will reset all the labels that are currently stored within this class.

        Args:
            label_row_dict: The dictionary of all labels as expected by the Encord format.
        """
        if ontology_structure is not None:
            self._ontology_structure = ontology_structure

        if self._ontology_structure is None:
            self._refresh_ontology_structure()

        self._is_labelling_initialised = True

        self._label_row_read_only_data = self._parse_label_row_dict(label_row_dict)
        self._frame_to_hashes = defaultdict(set)
        self._classifications_to_frames: defaultdict[Classification, Set[int]] = defaultdict(set)

        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()
        self._parse_labels_from_dict(label_row_dict)

    def get_image_hash(self, frame_number: int) -> Optional[str]:
        """
        Get the corresponding image hash of the frame number. Return `None` if the frame number is out of bounds.
        Raise an error if this function is used for non-image data types.
        """
        self._check_labelling_is_initalised()

        if self.data_type not in (DataType.IMAGE, DataType.IMG_GROUP):
            raise LabelRowError("This function is only supported for label rows of image or image group data types.")

        return self._label_row_read_only_data.frame_to_image_hash.get(frame_number)

    def get_frame_number(self, image_hash: str) -> Optional[int]:
        """
        Get the corresponding image hash of the frame number. Return `None` if the image hash was not found with an
        associated frame number.
        Raise an error if this function is used for non-image data types.
        """
        self._check_labelling_is_initalised()

        if self.data_type not in (DataType.IMAGE, DataType.IMG_GROUP):
            raise LabelRowError("This function is only supported for label rows of image or image group data types.")
        return self._label_row_read_only_data.image_hash_to_frame[image_hash]

    def save(self):
        """
        Upload the created labels with the Encord server. This will overwrite any labels that someone has created
        in the platform in the meantime.
        """
        self._check_labelling_is_initalised()

        dict_labels = self.to_encord_dict()
        self._project_client.save_label_row(uid=self.label_hash, label=dict_labels)

    def get_frame_view(self, frame: Union[int, str] = 0) -> FrameView:
        """
        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.
        """
        self._check_labelling_is_initalised()
        if isinstance(frame, str):
            frame = self.get_frame_number(frame)
        return self.FrameView(self, self._label_row_read_only_data, frame)

    def get_frame_views(self) -> List[FrameView]:
        """
        Returns:
            A list of frame views in order of available frames.
        """
        self._check_labelling_is_initalised()
        ret = []
        for frame in range(self.number_of_frames):
            ret.append(self.get_frame_view(frame))
        return ret

    def get_object_instances(
        self, filter_ontology_object: Optional[Object] = None, filter_frames: Optional[Frames] = None
    ) -> List[ObjectInstance]:
        """
        Args:
            filter_ontology_object:
                Optionally filter by a specific ontology object.
            filter_frames:
                Optionally filter by specific frames.

        Returns:
            All the `ObjectInstance`s that match the filter.
        """
        self._check_labelling_is_initalised()

        ret: List[ObjectInstance] = list()

        if filter_frames is not None:
            filtered_frames_list = frames_class_to_frames_list(filter_frames)
        else:
            filtered_frames_list = list()

        for object_ in self._objects_map.values():
            # filter by ontology object
            if not (
                filter_ontology_object is None
                or object_.ontology_item.feature_node_hash == filter_ontology_object.feature_node_hash
            ):
                continue

            # filter by frame
            if filter_frames is None:
                append = True
            else:
                append = False
            for frame in filtered_frames_list:
                hashes = self._frame_to_hashes.get(frame, set())
                if object_.object_hash in hashes:
                    append = True
                    break

            if append:
                ret.append(object_)

        return ret

    def add_object_instance(self, object_instance: ObjectInstance, force: bool = True) -> None:
        """
        Add an object instance to the label row. If the object instance already exists, it

        Args:
            object_instance: The object instance to add.
            force: overwrites current objects, otherwise this will replace the current object.
        """
        self._check_labelling_is_initalised()

        object_instance.is_valid()

        if object_instance.is_assigned_to_label_row():
            raise LabelRowError(
                "The supplied ObjectInstance is already part of a LabelRowV2. You can only add a ObjectInstance to one "
                "LabelRowV2. You can do a ObjectInstance.copy() to create an identical ObjectInstance which is not part of "
                "any LabelRowV2."
            )

        object_hash = object_instance.object_hash
        if object_hash in self._objects_map and not force:
            raise LabelRowError(
                "The supplied ObjectInstance was already previously added. (the object_hash is the same)."
            )
        elif object_hash in self._objects_map and force:
            self._objects_map.pop(object_hash)

        self._objects_map[object_hash] = object_instance
        object_instance._parent = self

        self._add_to_frame_to_hashes_map(object_instance)

    def add_classification_instance(self, classification_instance: ClassificationInstance, force: bool = False) -> None:
        """
        Add a classification instance to the label row.

        Args:
            classification_instance: The object instance to add.
            force: overwrites current objects, otherwise this will replace the current object.
        """
        self._check_labelling_is_initalised()

        classification_instance.is_valid()

        if classification_instance.is_assigned_to_label_row():
            raise LabelRowError(
                "The supplied ClassificationInstance is already part of a LabelRowV2. You can only add a ClassificationInstance"
                " to one LabelRowV2. You can do a ClassificationInstance.copy() to create an identical ObjectInstance which is "
                "not part of any LabelRowV2."
            )

        classification_hash = classification_instance.classification_hash
        already_present_frame = self._is_classification_already_present(
            classification_instance.ontology_item,
            _frame_views_to_frame_numbers(classification_instance.get_annotations()),
        )
        if classification_hash in self._classifications_map and not force:
            raise LabelRowError(
                "The supplied ClassificationInstance was already previously added. (the classification_hash is the same)."
            )

        if already_present_frame is not None and not force:
            raise LabelRowError(
                f"A ClassificationInstance of the same type was already added and has overlapping frames. One "
                f"overlapping frame that was found is `{already_present_frame}`. Make sure that you only add "
                f"classifications which are on frames where the same type of classification does not yet exist."
            )

        if classification_hash in self._classifications_map and force:
            self._classifications_map.pop(classification_hash)

        self._classifications_map[classification_hash] = classification_instance
        classification_instance._parent = self

        self._classifications_to_frames[classification_instance.ontology_item].update(
            set(_frame_views_to_frame_numbers(classification_instance.get_annotations()))
        )
        self._add_to_frame_to_hashes_map(classification_instance)

    def remove_classification(self, classification_instance: ClassificationInstance):
        """Remove a classification instance from a label row."""
        self._check_labelling_is_initalised()

        classification_hash = classification_instance.classification_hash
        self._classifications_map.pop(classification_hash)
        all_frames = self._classifications_to_frames[classification_instance.ontology_item]
        actual_frames = _frame_views_to_frame_numbers(classification_instance.get_annotations())
        for actual_frame in actual_frames:
            all_frames.remove(actual_frame)

    def add_to_single_frame_to_hashes_map(
        self, label_item: Union[ObjectInstance, ClassificationInstance], frame: int
    ) -> None:
        """This is an internal function, it is not meant to be called by the SDK user."""
        self._check_labelling_is_initalised()

        if isinstance(label_item, ObjectInstance):
            self._frame_to_hashes[frame].add(label_item.object_hash)
        elif isinstance(label_item, ClassificationInstance):
            self._frame_to_hashes[frame].add(label_item.classification_hash)
        else:
            raise NotImplementedError(f"Got an unexpected label item class `{type(label_item)}`")

    def get_classification_instances(
        self, filter_ontology_classification: Optional[Classification] = None, filter_frames: Optional[Frames] = None
    ) -> List[ClassificationInstance]:
        """
        Args:
            filter_ontology_classification:
                Optionally filter by a specific ontology classification.
            filter_frames:
                Optionally filter by specific frames.

        Returns:
            All the `ObjectInstance`s that match the filter.
        """
        self._check_labelling_is_initalised()

        ret: List[ClassificationInstance] = list()

        if filter_frames is not None:
            filtered_frames_list = frames_class_to_frames_list(filter_frames)
        else:
            filtered_frames_list = list()

        for classification in self._classifications_map.values():
            # filter by ontology object
            if not (
                filter_ontology_classification is None
                or classification.ontology_item.feature_node_hash == filter_ontology_classification.feature_node_hash
            ):
                continue

            # filter by frame
            if filter_frames is None:
                append = True
            else:
                append = False
            for frame in filtered_frames_list:
                hashes = self._frame_to_hashes.get(frame, set())
                if classification.classification_hash in hashes:
                    append = True
                    break

            if append:
                ret.append(classification)
        return ret

    def remove_object(self, object_instance: ObjectInstance):
        """Remove an object instance from a label row."""
        self._check_labelling_is_initalised()

        self._objects_map.pop(object_instance.object_hash)
        self._remove_from_frame_to_hashes_map(
            _frame_views_to_frame_numbers(object_instance.get_annotations()), object_instance.object_hash
        )
        object_instance._parent = None

    def to_encord_dict(self) -> dict:
        """
        This is an internal helper function. Likely this should not be used by a user. To upload labels use the
        :meth:`.save()` function.
        """
        self._check_labelling_is_initalised()

        ret = {}
        read_only_data = self._label_row_read_only_data

        ret["label_hash"] = read_only_data.label_hash
        ret["created_at"] = read_only_data.created_at
        ret["last_edited_at"] = read_only_data.last_edited_at
        ret["data_hash"] = read_only_data.data_hash
        ret["dataset_hash"] = read_only_data.dataset_hash
        ret["dataset_title"] = read_only_data.dataset_title
        ret["data_title"] = read_only_data.data_title
        ret["data_type"] = read_only_data.data_type.value
        ret["annotation_task_status"] = read_only_data.annotation_task_status
        ret["is_shadow_data"] = read_only_data.is_shadow_data
        ret["object_answers"] = self._to_object_answers()
        ret["classification_answers"] = self._to_classification_answers()
        ret["object_actions"] = self._to_object_actions()
        ret["label_status"] = read_only_data.label_status.value
        ret["data_units"] = self._to_encord_data_units()

        return ret

    class FrameView:
        """
        This class can be used to inspect what object/classification instances are on a given frame or
        what metadata, such as a image file size, is on a given frame.
        """

        def __init__(
            self, label_row: LabelRowV2, label_row_read_only_data: LabelRowV2.LabelRowReadOnlyData, frame: int
        ):

            self._label_row = label_row
            self._label_row_read_only_data = label_row_read_only_data
            self._frame = frame

        @property
        def image_hash(self) -> str:
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("Image hash can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().image_hash

        @property
        def image_title(self) -> str:
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("Image title can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().image_title

        @property
        def file_type(self) -> str:
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("File type can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().file_type

        @property
        def frame(self) -> int:
            return self._frame

        @property
        def width(self) -> int:
            if self._label_row.data_type in [DataType.IMG_GROUP]:
                return self._frame_level_data().width
            else:
                return self._label_row_read_only_data.width

        @property
        def height(self) -> int:
            if self._label_row.data_type in [DataType.IMG_GROUP]:
                return self._frame_level_data().height
            else:
                return self._label_row_read_only_data.height

        @property
        def data_link(self) -> Optional[str]:
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("Data link can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().data_link

        def add_object_instance(
            self,
            object_instance: ObjectInstance,
            coordinates: Coordinates,
            *,
            overwrite: bool = False,
            created_at: Optional[datetime] = None,
            created_by: Optional[str] = None,
            last_edited_at: Optional[datetime] = None,
            last_edited_by: Optional[str] = None,
            confidence: Optional[float] = None,
            manual_annotation: Optional[bool] = None,
        ) -> None:
            label_row = object_instance.is_assigned_to_label_row()
            if label_row and self._label_row != label_row:
                raise LabelRowError(
                    "This object instance is already assigned to a different label row. It can not be "
                    "added to multiple label rows at once."
                )

            object_instance.set_for_frames(
                coordinates,
                self._frame,
                overwrite=overwrite,
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
            )

            if not label_row:
                self._label_row.add_object_instance(object_instance)

        def add_classification_instance(
            self,
            classification_instance: ClassificationInstance,
            *,
            overwrite: bool = False,
            created_at: datetime = datetime.now(),
            created_by: str = None,
            confidence: int = DEFAULT_CONFIDENCE,
            manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
            last_edited_at: datetime = datetime.now(),
            last_edited_by: Optional[str] = None,
        ) -> None:
            label_row = classification_instance.is_assigned_to_label_row()
            if label_row and self._label_row != label_row:
                raise LabelRowError(
                    "This object instance is already assigned to a different label row. It can not be "
                    "added to multiple label rows at once."
                )

            classification_instance.set_for_frames(
                self._frame,
                overwrite=overwrite,
                created_at=created_at,
                created_by=created_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
            )

            if not label_row:
                self._label_row.add_classification_instance(classification_instance)

        def get_object_instances(self, filter_ontology_object: Optional[Object] = None) -> List[ObjectInstance]:
            """
            Args:
                filter_ontology_object:
                    Optionally filter by a specific ontology object.

            Returns:
                All the `ObjectInstance`s that match the filter.
            """
            return self._label_row.get_object_instances(
                filter_ontology_object=filter_ontology_object, filter_frames=self._frame
            )

        def get_classification_instances(
            self, filter_ontology_classification: Optional[Classification] = None
        ) -> List[ClassificationInstance]:
            """
            Args:
                filter_ontology_classification:
                    Optionally filter by a specific ontology object.

            Returns:
                All the `ObjectInstance`s that match the filter.
            """
            return self._label_row.get_classification_instances(
                filter_ontology_classification=filter_ontology_classification, filter_frames=self._frame
            )

        def _frame_level_data(self) -> LabelRowV2.FrameLevelImageGroupData:
            return self._label_row_read_only_data.frame_level_data[self._frame]

        def __repr__(self):
            return f"FrameView(label_row={self._label_row}, frame={self._frame})"

    @dataclass(frozen=True)
    class FrameLevelImageGroupData:
        """This is an internal helper class. A user should not directly interract with it."""

        image_hash: str
        image_title: str
        file_type: str
        frame_number: int
        width: int
        height: int
        data_link: Optional[str] = None

    @dataclass(frozen=True)
    class LabelRowReadOnlyData:
        """This is an internal helper class. A user should not directly interract with it."""

        label_hash: Optional[str]
        """This is None if the label row does not have any labels and was not initialised for labelling."""
        created_at: Optional[datetime]
        """This is None if the label row does not have any labels and was not initialised for labelling."""
        last_edited_at: Optional[datetime]
        """This is None if the label row does not have any labels and was not initialised for labelling."""
        data_hash: str
        data_type: DataType
        label_status: LabelStatus
        annotation_task_status: AnnotationTaskStatus
        is_shadow_data: bool
        number_of_frames: int
        duration: Optional[float]
        fps: Optional[float]
        dataset_hash: str
        dataset_title: str
        data_title: str
        width: Optional[int]
        height: Optional[int]
        data_link: Optional[str]
        frame_level_data: Dict[int, LabelRowV2.FrameLevelImageGroupData] = field(default_factory=dict)
        image_hash_to_frame: Dict[str, int] = field(default_factory=dict)
        frame_to_image_hash: Dict[int, str] = field(default_factory=dict)

    def _refresh_ontology_structure(self):
        ontology_hash = self._project_client.get_project()["ontology_hash"]
        ontology = self._querier.basic_getter(Ontology, ontology_hash)
        self._ontology_structure = ontology.structure

    def _to_object_answers(self) -> dict:
        ret = {}
        for obj in self._objects_map.values():
            all_static_answers = self._get_all_static_answers(obj)
            ret[obj.object_hash] = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }
        return ret

    def _to_object_actions(self) -> dict:
        ret = {}
        for obj in self._objects_map.values():
            all_static_answers = self._dynamic_answers_to_encord_dict(obj)
            if len(all_static_answers) == 0:
                continue
            ret[obj.object_hash] = {
                "actions": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }
        return ret

    def _to_classification_answers(self) -> dict:
        ret = {}
        for classification in self._classifications_map.values():
            classifications = []

            all_static_answers = classification.get_all_static_answers()
            for answer in all_static_answers:
                if answer.is_answered():
                    classifications.append(answer.to_encord_dict())

            ret[classification.classification_hash] = {
                "classifications": list(reversed(classifications)),
                "classificationHash": classification.classification_hash,
            }
        return ret

    @staticmethod
    def _get_all_static_answers(object_instance: ObjectInstance) -> List[dict]:
        """Essentially convert to the JSON format of all the static answers."""
        ret = []
        for answer in object_instance._get_all_static_answers():
            d_opt = answer.to_encord_dict()
            if d_opt is not None:
                ret.append(d_opt)
        return ret

    @staticmethod
    def _dynamic_answers_to_encord_dict(object_instance: ObjectInstance) -> List[dict]:
        ret = []
        for answer, ranges in object_instance._get_all_dynamic_answers():
            d_opt = answer.to_encord_dict(ranges)
            if d_opt is not None:
                ret.append(d_opt)
        return ret

    def _to_encord_data_units(self) -> dict:
        ret = {}
        frame_level_data = self._label_row_read_only_data.frame_level_data
        for value in frame_level_data.values():
            ret[value.image_hash] = self._to_encord_data_unit(value)

        return ret

    def _to_encord_data_unit(self, frame_level_data: FrameLevelImageGroupData) -> dict:
        ret = {}

        data_type = self._label_row_read_only_data.data_type
        if data_type == DataType.IMG_GROUP:
            data_sequence = str(frame_level_data.frame_number)
        elif data_type in (DataType.VIDEO, DataType.DICOM, DataType.IMAGE):
            data_sequence = frame_level_data.frame_number
        else:
            raise NotImplementedError(f"The data type {data_type} is not implemented yet.")

        ret["data_hash"] = frame_level_data.image_hash
        ret["data_title"] = frame_level_data.image_title

        if data_type != DataType.DICOM:
            ret["data_link"] = frame_level_data.data_link

        ret["data_type"] = frame_level_data.file_type
        ret["data_sequence"] = data_sequence
        ret["width"] = frame_level_data.width
        ret["height"] = frame_level_data.height
        ret["labels"] = self._to_encord_labels(frame_level_data)

        if self._label_row_read_only_data.duration is not None:
            ret["data_duration"] = self._label_row_read_only_data.duration
        if self._label_row_read_only_data.fps is not None:
            ret["data_fps"] = self._label_row_read_only_data.fps

        return ret

    def _to_encord_labels(self, frame_level_data: FrameLevelImageGroupData) -> dict:
        ret = {}
        data_type = self._label_row_read_only_data.data_type

        if data_type in [DataType.IMAGE, DataType.IMG_GROUP]:
            frame = frame_level_data.frame_number
            ret.update(self._to_encord_label(frame))

        elif data_type in [DataType.VIDEO, DataType.DICOM]:
            for frame in self._frame_to_hashes.keys():
                ret[str(frame)] = self._to_encord_label(frame)

        return ret

    def _to_encord_label(self, frame: int) -> dict:
        ret = {}

        ret["objects"] = self._to_encord_objects_list(frame)
        ret["classifications"] = self._to_encord_classifications_list(frame)

        return ret

    def _to_encord_objects_list(self, frame: int) -> list:
        # Get objects for frame
        ret: List[dict] = []

        objects = self.get_object_instances(filter_frames=frame)
        for object_ in objects:
            encord_object = self._to_encord_object(object_, frame)
            ret.append(encord_object)
        return ret

    def _to_encord_object(
        self,
        object_: ObjectInstance,
        frame: int,
    ) -> dict:
        ret = {}

        object_instance_annotation = object_.get_annotation(frame)
        coordinates = object_instance_annotation.coordinates
        ontology_hash = object_.ontology_item.feature_node_hash
        ontology_object = self._ontology_structure.get_child_by_hash(ontology_hash)

        ret["name"] = ontology_object.name
        ret["color"] = ontology_object.color
        ret["shape"] = ontology_object.shape.value
        ret["value"] = _lower_snake_case(ontology_object.name)
        ret["createdAt"] = object_instance_annotation.created_at.strftime(DATETIME_LONG_STRING_FORMAT)
        ret["createdBy"] = object_instance_annotation.created_by
        ret["confidence"] = object_instance_annotation.confidence
        ret["objectHash"] = object_.object_hash
        ret["featureHash"] = ontology_object.feature_node_hash
        ret["manualAnnotation"] = object_instance_annotation.manual_annotation

        if object_instance_annotation.last_edited_at is not None:
            ret["lastEditedAt"] = object_instance_annotation.last_edited_at.strftime(DATETIME_LONG_STRING_FORMAT)
        if object_instance_annotation.last_edited_by is not None:
            ret["lastEditedBy"] = object_instance_annotation.last_edited_by
        if object_instance_annotation.is_deleted is not None:
            ret["isDeleted"] = object_instance_annotation.is_deleted

        self._add_coordinates_to_encord_object(coordinates, ret)

        return ret

    def _add_coordinates_to_encord_object(self, coordinates: Coordinates, encord_object: dict) -> None:
        if isinstance(coordinates, BoundingBoxCoordinates):
            encord_object["boundingBox"] = coordinates.to_dict()
        elif isinstance(coordinates, RotatableBoundingBoxCoordinates):
            encord_object["rotatableBoundingBox"] = coordinates.to_dict()
        elif isinstance(coordinates, PolygonCoordinates):
            encord_object["polygon"] = coordinates.to_dict()
        elif isinstance(coordinates, PolylineCoordinates):
            encord_object["polyline"] = coordinates.to_dict()
        elif isinstance(coordinates, PointCoordinate):
            encord_object["point"] = coordinates.to_dict()
        else:
            raise NotImplementedError(f"adding coordinatees for this type not yet implemented {type(coordinates)}")

    def _to_encord_classifications_list(self, frame: int) -> list:
        ret: List[dict] = []

        classifications = self.get_classification_instances(filter_frames=frame)
        for classification in classifications:
            encord_classification = self._to_encord_classification(classification, frame)
            ret.append(encord_classification)

        return ret

    def _to_encord_classification(self, classification: ClassificationInstance, frame: int) -> dict:
        ret = {}

        annotation = classification.get_annotation(frame)
        classification_feature_hash = classification.ontology_item.feature_node_hash
        ontology_classification = self._ontology_structure.get_child_by_hash(classification_feature_hash)
        attribute_hash = classification.ontology_item.attributes[0].feature_node_hash
        ontology_attribute = self._ontology_structure.get_child_by_hash(attribute_hash)

        ret["name"] = ontology_attribute.name
        ret["value"] = _lower_snake_case(ontology_attribute.name)
        ret["createdAt"] = annotation.created_at.strftime(DATETIME_LONG_STRING_FORMAT)
        ret["createdBy"] = annotation.created_by
        ret["confidence"] = annotation.confidence
        ret["featureHash"] = ontology_classification.feature_node_hash
        ret["classificationHash"] = classification.classification_hash
        ret["manualAnnotation"] = annotation.manual_annotation

        if annotation.last_edited_at is not None:
            ret["lastEditedAt"] = annotation.last_edited_at.strftime(DATETIME_LONG_STRING_FORMAT)
        if annotation.last_edited_by is not None:
            ret["lastEditedBy"] = annotation.last_edited_by

        return ret

    def _is_classification_already_present(
        self, classification: Classification, frames: Iterable[int]
    ) -> Optional[int]:
        present_frames = self._classifications_to_frames.get(classification, set())
        for frame in frames:
            if frame in present_frames:
                return frame
        return None

    def _remove_frames_from_classification(self, classification: Classification, frames: Iterable[int]) -> None:
        present_frames = self._classifications_to_frames.get(classification, set())
        for frame in frames:
            present_frames.remove(frame)

    def _add_to_frame_to_hashes_map(self, label_item: Union[ObjectInstance, ClassificationInstance]) -> None:
        """This can be called by the ObjectInstance."""
        for frame_view in label_item.get_annotations():
            self.add_to_single_frame_to_hashes_map(label_item, frame_view.frame)

    def _remove_from_frame_to_hashes_map(self, frames: Iterable[int], item_hash: str):
        for frame in frames:
            self._frame_to_hashes[frame].remove(item_hash)

    def _parse_label_row_metadata(self, label_row_metadata: LabelRowMetadata) -> LabelRowV2.LabelRowReadOnlyData:
        data_type = DataType.from_upper_case_string(label_row_metadata.data_type)

        return LabelRowV2.LabelRowReadOnlyData(
            label_hash=label_row_metadata.label_hash,
            data_hash=label_row_metadata.data_hash,
            data_title=label_row_metadata.data_title,
            dataset_hash=label_row_metadata.dataset_hash,
            dataset_title=label_row_metadata.dataset_title,
            data_type=data_type,
            data_link=label_row_metadata.data_link,
            label_status=label_row_metadata.label_status,
            annotation_task_status=label_row_metadata.annotation_task_status,
            is_shadow_data=label_row_metadata.is_shadow_data,
            created_at=label_row_metadata.created_at,
            last_edited_at=label_row_metadata.last_edited_at,
            duration=label_row_metadata.duration,
            fps=label_row_metadata.frames_per_second,
            number_of_frames=label_row_metadata.number_of_frames,
            width=label_row_metadata.width,
            height=label_row_metadata.height,
        )

    def _parse_label_row_dict(self, label_row_dict: dict) -> LabelRowReadOnlyData:
        frame_level_data = self._parse_image_group_frame_level_data(label_row_dict["data_units"])
        image_hash_to_frame = {item.image_hash: item.frame_number for item in frame_level_data.values()}
        frame_to_image_hash = {item.frame_number: item.image_hash for item in frame_level_data.values()}
        data_type = DataType(label_row_dict["data_type"])

        if data_type == DataType.VIDEO:
            video_dict = list(label_row_dict["data_units"].values())[0]
            data_link = video_dict["data_link"]
            height = video_dict["height"]
            width = video_dict["width"]

        elif data_type == DataType.DICOM:
            dicom_dict = list(label_row_dict["data_units"].values())[0]
            data_link = None
            height = dicom_dict["height"]
            width = dicom_dict["width"]

        elif data_type == DataType.IMAGE:
            image_dict = list(label_row_dict["data_units"].values())[0]
            data_link = image_dict["data_link"]
            height = image_dict["height"]
            width = image_dict["width"]

        elif data_type == DataType.IMG_GROUP:
            data_link = None
            height = None
            width = None

        else:
            raise NotImplementedError(f"The data type {data_type} is not implemented yet.")

        return self.LabelRowReadOnlyData(
            label_hash=label_row_dict["label_hash"],
            dataset_hash=label_row_dict["dataset_hash"],
            dataset_title=label_row_dict["dataset_title"],
            data_title=label_row_dict["data_title"],
            data_hash=label_row_dict["data_hash"],
            data_type=data_type,
            label_status=LabelStatus(label_row_dict["label_status"]),
            annotation_task_status=label_row_dict["annotation_task_status"],
            is_shadow_data=self.is_shadow_data,
            created_at=label_row_dict["created_at"],
            last_edited_at=label_row_dict["last_edited_at"],
            frame_level_data=frame_level_data,
            image_hash_to_frame=image_hash_to_frame,
            frame_to_image_hash=frame_to_image_hash,
            duration=self.duration,
            fps=self.fps,
            number_of_frames=self.number_of_frames,
            data_link=data_link,
            height=height,
            width=width,
        )

    def _parse_labels_from_dict(self, label_row_dict: dict):
        classification_answers = label_row_dict["classification_answers"]

        for data_unit in label_row_dict["data_units"].values():
            data_type = label_row_dict["data_type"]
            if data_type in {DataType.IMG_GROUP.value, DataType.IMAGE.value}:
                frame = int(data_unit["data_sequence"])
                self._add_object_instances_from_objects(data_unit["labels"].get("objects", []), frame)
                self._add_classification_instances_from_classifications(
                    data_unit["labels"].get("classifications", []), classification_answers, int(frame)
                )
            elif data_type in {DataType.VIDEO.value, DataType.DICOM.value}:
                for frame, frame_data in data_unit["labels"].items():
                    self._add_object_instances_from_objects(frame_data["objects"], int(frame))
                    self._add_classification_instances_from_classifications(
                        frame_data["classifications"], classification_answers, int(frame)
                    )
            else:
                raise NotImplementedError(f"Got an unexpected data type `{data_type}`")

        self._add_objects_answers(label_row_dict)
        self._add_action_answers(label_row_dict)

    def _add_object_instances_from_objects(
        self,
        objects_list: List[dict],
        frame: int,
    ) -> None:
        for frame_object_label in objects_list:
            object_hash = frame_object_label["objectHash"]
            if object_hash not in self._objects_map:
                object_instance = self._create_new_object_instance(frame_object_label, frame)
                self.add_object_instance(object_instance)
            else:
                self._add_coordinates_to_object_instance(frame_object_label, frame)

    def _add_objects_answers(self, label_row_dict: dict):
        for answer in label_row_dict["object_answers"].values():
            object_hash = answer["objectHash"]
            object_instance = self._objects_map[object_hash]

            answer_list = answer["classifications"]
            object_instance.set_answer_from_list(answer_list)

    def _add_action_answers(self, label_row_dict: dict):
        for answer in label_row_dict["object_actions"].values():
            object_hash = answer["objectHash"]
            object_instance = self._objects_map[object_hash]

            answer_list = answer["actions"]
            object_instance.set_answer_from_list(answer_list)

    def _create_new_object_instance(self, frame_object_label: dict, frame: int) -> ObjectInstance:
        ontology = self._ontology_structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]

        label_class = ontology.get_child_by_hash(feature_hash)
        object_instance = ObjectInstance(label_class, object_hash=object_hash)

        coordinates = self._get_coordinates(frame_object_label)
        object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(frame_object_label)

        object_instance.set_for_frames(coordinates=coordinates, frames=frame, **asdict(object_frame_instance_info))
        return object_instance

    def _add_coordinates_to_object_instance(
        self,
        frame_object_label: dict,
        frame: int = 0,
    ) -> None:
        object_hash = frame_object_label["objectHash"]
        object_instance = self._objects_map[object_hash]

        coordinates = self._get_coordinates(frame_object_label)
        object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(frame_object_label)

        object_instance.set_for_frames(coordinates=coordinates, frames=frame, **asdict(object_frame_instance_info))

    def _get_coordinates(self, frame_object_label: dict) -> Coordinates:
        if "boundingBox" in frame_object_label:
            return BoundingBoxCoordinates.from_dict(frame_object_label)
        if "rotatableBoundingBox" in frame_object_label:
            return RotatableBoundingBoxCoordinates.from_dict(frame_object_label)
        elif "polygon" in frame_object_label:
            return PolygonCoordinates.from_dict(frame_object_label)
        elif "point" in frame_object_label:
            return PointCoordinate.from_dict(frame_object_label)
        elif "polyline" in frame_object_label:
            return PolylineCoordinates.from_dict(frame_object_label)
        elif "skeleton" in frame_object_label:
            raise NotImplementedError(f"Got a skeleton object, which is not supported yet")
        else:
            raise NotImplementedError(f"Getting coordinates for `{frame_object_label}` is not supported yet.")

    def _add_classification_instances_from_classifications(
        self, classifications_list: List[dict], classification_answers: dict, frame: int
    ):
        for frame_classification_label in classifications_list:
            classification_hash = frame_classification_label["classificationHash"]
            if classification_hash not in self._classifications_map:
                classification_instance = self._create_new_classification_instance(
                    frame_classification_label, frame, classification_answers
                )
                self.add_classification_instance(classification_instance)
            else:
                self._add_frames_to_classification_instance(frame_classification_label, frame)

    def _parse_image_group_frame_level_data(self, label_row_data_units: dict) -> Dict[int, FrameLevelImageGroupData]:
        frame_level_data: Dict[int, LabelRowV2.FrameLevelImageGroupData] = dict()
        for _, payload in label_row_data_units.items():
            frame_number = int(payload["data_sequence"])
            frame_level_image_group_data = self.FrameLevelImageGroupData(
                image_hash=payload["data_hash"],
                image_title=payload["data_title"],
                data_link=payload.get("data_link"),
                file_type=payload["data_type"],
                frame_number=frame_number,
                width=payload["width"],
                height=payload["height"],
            )
            frame_level_data[frame_number] = frame_level_image_group_data
        return frame_level_data

    def _create_new_classification_instance(
        self, frame_classification_label: dict, frame: int, classification_answers: dict
    ) -> ClassificationInstance:
        ontology = self._ontology_structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]

        label_class = ontology.get_child_by_hash(feature_hash)
        classification_instance = ClassificationInstance(label_class, classification_hash=classification_hash)

        frame_view = ClassificationInstance.FrameData.from_dict(frame_classification_label)
        classification_instance.set_for_frames(frame, **asdict(frame_view))
        answers_dict = classification_answers[classification_hash]["classifications"]
        self._add_static_answers_from_dict(classification_instance, answers_dict)

        return classification_instance

    def _add_static_answers_from_dict(
        self, classification_instance: ClassificationInstance, answers_list: List[dict]
    ) -> None:

        classification_instance.set_answer_from_list(answers_list)

    def _add_frames_to_classification_instance(self, frame_classification_label: dict, frame: int) -> None:
        object_hash = frame_classification_label["classificationHash"]
        classification_instance = self._classifications_map[object_hash]
        frame_view = ClassificationInstance.FrameData.from_dict(frame_classification_label)

        classification_instance.set_for_frames(frame, **asdict(frame_view))

    def _check_labelling_is_initalised(self):
        if not self.is_labelling_initialised:
            raise LabelRowError(
                "For this operation you will need to initialise labelling first. Call the `.initialise_labels()` "
                "to do so first."
            )

    def __repr__(self) -> str:
        return f"LabelRowV2(label_hash={self.label_hash}, data_hash={self.data_hash}, data_title={self.data_title})"


@dataclass
class AnswerForFrames:
    answer: Union[str, Option, Iterable[Option]]
    ranges: Ranges
    """
    The ranges are essentially a run length encoding of the frames where the unique answer is set.
    They are sorted in ascending order.
    """


AnswersForFrames = List[AnswerForFrames]


class ObjectInstance:
    """
    An object instance is an object that has coordinates and can be places on one or multiple frames in a label row.
    """

    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None):
        self._ontology_object = ontology_object
        self._frames_to_instance_data: Dict[int, ObjectInstance.FrameData] = dict()
        self._object_hash = object_hash or short_uuid_str()
        self._parent: Optional[LabelRowV2] = None
        """This member should only be manipulated by a LabelRowV2"""

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_object.attributes)
        # feature_node_hash of attribute to the answer.

        self._dynamic_answer_manager = DynamicAnswerManager(self)

    def is_assigned_to_label_row(self) -> Optional[LabelRowV2]:
        return self._parent

    @property
    def object_hash(self) -> str:
        """A unique identifier for the object instance."""
        return self._object_hash

    @property
    def ontology_item(self) -> Any:
        return deepcopy(self._ontology_object)

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
        elif not self._is_selectable_child_attribute(attribute):
            return None

        if is_dynamic is not None and is_dynamic is not attribute.dynamic:
            raise LabelRowError(
                f"The attribute is {'dynamic' if attribute.dynamic else 'static'}, but is_dynamic is set to "
                f"{is_dynamic}."
            )

        if attribute.dynamic:
            return self._dynamic_answer_manager.get_answer(attribute, filter_answer, filter_frame)

        static_answer = self._static_answer_map[attribute.feature_node_hash]

        return get_answer_from_object(static_answer)

    def set_answer(
        self,
        answer: Union[str, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Set the answer for a given ontology Attribute. This is the equivalent of e.g. selecting a checkbox in the
        UI after drowing the ObjectInstance. There is only one answer per ObjectInstance per Attribute, unless
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
        """
        if attribute is None:
            attribute = _infer_attribute_from_answer(self._ontology_object.attributes, answer)
        if not self._is_attribute_valid_child_of_object_instance(attribute):
            raise LabelRowError("The attribute is not a valid child of the object.")
        elif not self._is_selectable_child_attribute(attribute):
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

        set_answer_for_object(static_answer, answer)

    def set_answer_from_list(self, answers_list: List[Dict[str, Any]]) -> None:
        """
        This is a low level helper function and should usually not be used directly.

        Sets the answer for the classification from a dictionary.

        Args:
            answer_dict: The dictionary to set the answer from.
        """

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

            self._set_answer_from_dict(answer_dict, attribute)

    def delete_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, Option, Iterable[Option]] = None,
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
        """
        if isinstance(frame, str):
            frame = self._parent.get_frame_number(frame)
        return self.Annotation(self, frame)

    def copy(self) -> ObjectInstance:
        """
        Creates an exact copy of this ObjectInstance but with a new object hash and without being associated to any
        LabelRowV2. This is useful if you want to add the semantically same ObjectInstance to multiple
        `LabelRowV2`s.
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
            A list of `ObjectInstance.Annotation` in order of available frames.
        """
        ret = []
        for frame_num in sorted(self._frames_to_instance_data.keys()):
            ret.append(self.get_annotation(frame_num))
        return ret

    def remove_from_frames(self, frames: Frames):
        """Ensure that it will be removed from all frames."""
        frames_list = frames_class_to_frames_list(frames)
        for frame in frames_list:
            self._frames_to_instance_data.pop(frame)

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames_list, self.object_hash)

    def is_valid(self) -> None:
        """Check if is valid, could also return some human/computer  messages."""
        if len(self._frames_to_instance_data) == 0:
            raise LabelRowError("ObjectInstance is not on any frames. Please add it to at least one frame.")

        self.are_dynamic_answers_valid()

    def are_dynamic_answers_valid(self) -> None:
        """
        Whether there are any dynamic answers on frames that have no coordinates.
        """
        dynamic_frames = set(self._dynamic_answer_manager.frames())
        local_frames = set(_frame_views_to_frame_numbers(self.get_annotations()))

        if not len(dynamic_frames - local_frames) == 0:
            raise LabelRowError(
                "There are some dynamic answers on frames that have no coordinates. "
                "Please ensure that all the dynamic answers are only on frames where coordinates "
                "have been set previously."
            )

    class Annotation:
        """
        This class can be used to set or get data for a specific annotation (i.e. the ObjectInstance for a given
        frame number).
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
            self._object_instance.set_for_frames(coordinates, self._frame)

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
            """
            Set the created_by field with a user email or None if it should default to the current user of the SDK.
            """
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
            """
            Set the last_edited_by field with a user email or None if it should default to the current user of the SDK.
            """
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
        def reviews(self) -> List[dict]:
            """
            A read only property about the reviews that happened for this object on this frame.
            """
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.reviews

        @property
        def is_deleted(self) -> bool:
            """This property is only relevant for internal use."""
            self._check_if_frame_view_is_valid()
            return self._get_object_frame_instance_data().object_frame_instance_info.is_deleted

        def _get_object_frame_instance_data(self) -> ObjectInstance.FrameData:
            return self._object_instance._frames_to_instance_data[self._frame]

        def _check_if_frame_view_is_valid(self) -> None:
            if self._frame not in self._object_instance._frames_to_instance_data:
                raise LabelRowError(
                    "Tryinannotation to use an ObjectInstance.Annotation for an ObjectInstance that is not on the frameAnnotation"
                )

    @dataclass
    class FrameInfo:
        created_at: datetime = datetime.now()
        created_by: Optional[str] = None
        """None defaults to the user of the SDK once uploaded to the server."""
        last_edited_at: datetime = datetime.now()
        last_edited_by: Optional[str] = None
        """None defaults to the user of the SDK once uploaded to the server."""
        confidence: float = DEFAULT_CONFIDENCE
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
        reviews: Optional[List[dict]] = None
        is_deleted: Optional[bool] = None

        @staticmethod
        def from_dict(d: dict):
            if "lastEditedAt" in d:
                last_edited_at = parse(d["lastEditedAt"])
            else:
                last_edited_at = None

            return ObjectInstance.FrameInfo(
                created_at=parse(d["createdAt"]),
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
            reviews: Optional[List[dict]] = None,
            is_deleted: Optional[bool] = None,
        ) -> None:
            """Return a new instance with the specified fields updated."""
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
        coordinates: Coordinates
        object_frame_instance_info: ObjectInstance.FrameInfo
        # Probably the above can be flattened out into this class.

    def _set_answer_unsafe(
        self, answer: Union[str, Option, Iterable[Option]], attribute: Attribute, track_hash: str, ranges: Ranges
    ) -> None:
        if attribute.dynamic:
            self._dynamic_answer_manager.set_answer(answer, attribute, frames=ranges)

        else:
            static_answer = self._static_answer_map[attribute.feature_node_hash]
            set_answer_for_object(static_answer, answer)

    def _set_answer_from_dict(self, answer_dict: Dict[str, Any], attribute: Attribute) -> None:
        if attribute.dynamic:
            track_hash = answer_dict["trackHash"]
            ranges = ranges_list_to_ranges(answer_dict["range"])
        else:
            track_hash = None
            ranges = None

        if isinstance(attribute, TextAttribute):
            self._set_answer_unsafe(answer_dict["answers"], attribute, track_hash, ranges)
        elif isinstance(attribute, RadioAttribute):
            feature_hash = answer_dict["answers"][0]["featureHash"]
            option = _get_option_by_hash(feature_hash, attribute.options)
            self._set_answer_unsafe(option, attribute, track_hash, ranges)
        elif isinstance(attribute, ChecklistAttribute):
            options = []
            for answer in answer_dict["answers"]:
                feature_hash = answer["featureHash"]
                option = _get_option_by_hash(feature_hash, attribute.options)
                options.append(option)
            self._set_answer_unsafe(options, attribute, track_hash, ranges)
        else:
            raise NotImplementedError(f"The attribute type {type(attribute)} is not supported.")

    def _is_attribute_valid_child_of_object_instance(self, attribute: Attribute) -> bool:
        is_static_child = attribute.feature_node_hash in self._static_answer_map
        is_dynamic_child = self._dynamic_answer_manager.is_valid_dynamic_attribute(attribute)
        return is_dynamic_child or is_static_child

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        # I have the ontology classification, so I can build the tree from that. Basically do a DFS.
        ontology_object = self._ontology_object
        for search_attribute in ontology_object.attributes:
            if _search_child_attributes(attribute, search_attribute, self._static_answer_map):
                return True
        return False

    def _get_all_static_answers(self) -> List[Answer]:
        return list(self._static_answer_map.values())

    def _get_all_dynamic_answers(self) -> List[Tuple[Answer, Ranges]]:
        return self._dynamic_answer_manager.get_all_answers()

    def __repr__(self):
        return (
            f"ObjectInstance(object_hash={self._object_hash}, object_name={self._ontology_object.name}, "
            f"object_feature_hash={self._ontology_object.feature_node_hash})"
        )

    def __hash__(self) -> int:
        return hash(id(self))

    def __lt__(self, other: ObjectInstance) -> bool:
        return self._object_hash < other._object_hash


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
                    answer_value = get_answer_from_object(answer_object)
                    if answer_value != filter_answer:
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
        set_answer_for_object(default_answer, answer)

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
            if not (filter_answer is None or filter_answer == get_answer_from_object(answer)):
                continue
            actual_frames = self._answers_to_frames[answer]
            if not (filter_frames_set is None or len(actual_frames & filter_frames_set) > 0):
                continue

            ranges = frames_to_ranges(self._answers_to_frames[answer])
            ret.append(AnswerForFrames(answer=get_answer_from_object(answer), ranges=ranges))
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

    def __eq__(self, other: DynamicAnswerManager) -> bool:
        if not isinstance(other, DynamicAnswerManager):
            return False
        return (
            self._frames_to_answers == other._frames_to_answers and self._answers_to_frames == other._answers_to_frames
        )

    def __hash__(self) -> int:
        return hash(id(self))


def check_coordinate_type(coordinates: Coordinates, ontology_object: Object) -> None:
    expected_coordinate_type = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[ontology_object.shape]
    if type(coordinates) != expected_coordinate_type:
        raise LabelRowError(
            f"Expected a coordinate of type `{expected_coordinate_type}`, but got type `{type(coordinates)}`."
        )


AVAILABLE_COLORS = (
    "#D33115",
    "#E27300",
    "#16406C",
    "#FE9200",
    "#FCDC00",
    "#DBDF00",
    "#A4DD00",
    "#68CCCA",
    "#73D8FF",
    "#AEA1FF",
    "#FCC400",
    "#B0BC00",
    "#68BC00",
    "#16A5A5",
    "#009CE0",
    "#7B64FF",
    "#FA28FF",
    "#B3B3B3",
    "#9F0500",
    "#C45100",
    "#FB9E00",
    "#808900",
    "#194D33",
    "#0C797D",
    "#0062B1",
    "#653294",
    "#AB149E",
)


@dataclass
class OntologyStructure:
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    objects: List[Object] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Union[OntologyTypes, AttributeTypes, OptionTypes, None] = None,
    ) -> Union[OntologyClasses, AttributeClasses, OptionClasses]:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        for object_ in self.objects:
            if object_.feature_node_hash == feature_node_hash:
                check_type(object_, type_)
                return object_
            found_item = _get_attribute_by_hash(feature_node_hash, object_.attributes)
            if found_item is not None:
                check_type(found_item, type_)
                return found_item

        for classification in self.classifications:
            if classification.feature_node_hash == feature_node_hash:
                check_type(classification, type_)
                return classification
            found_item = _get_attribute_by_hash(feature_node_hash, classification.attributes)
            if found_item is not None:
                check_type(found_item, type_)
                return found_item

        raise OntologyError("Item not found.")

    def get_child_by_title(
        self,
        title: str,
        type_: Union[OntologyTypes, AttributeTypes, OptionTypes, None] = None,
    ) -> Union[OntologyClasses, AttributeClasses, OptionClasses]:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _handle_wrong_number_of_found_items(found_items, title, type_)
        return found_items[0]

    def get_children_by_title(
        self,
        title: str,
        type_: Union[OntologyTypes, AttributeTypes, OptionTypes, None] = None,
    ) -> List[Union[OntologyClasses, AttributeClasses, OptionClasses]]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        ret = []
        for object_ in self.objects:
            if object_.name == title:
                if does_type_match(object_, type_):
                    ret.append(object_)
            found_items = _get_attributes_by_title(title, object_.attributes)
            filtered_items = filter_by_type(found_items, type_)
            ret.extend(filtered_items)

        for classification in self.classifications:
            if classification.attributes[0].name == title:
                if does_type_match(classification, type_):
                    ret.append(classification)
            found_items = _get_attributes_by_title(title, classification.attributes)
            filtered_items = filter_by_type(found_items, type_)
            ret.extend(filtered_items)

        return ret

    @classmethod
    def from_dict(cls, d: dict) -> OntologyStructure:
        """
        Args:
            d: a JSON blob of an "ontology structure" (e.g. from Encord web app)

        Raises:
            KeyError: If the dict is missing a required field.
        """
        objects_ret: List[Object] = list()
        for object_dict in d["objects"]:
            objects_ret.append(Object.from_dict(object_dict))

        classifications_ret: List[Classification] = list()
        for classification_dict in d["classifications"]:
            classifications_ret.append(Classification.from_dict(classification_dict))

        return OntologyStructure(objects=objects_ret, classifications=classifications_ret)

    def to_dict(self) -> dict:
        """
        Returns:
            The dict equivalent to the ontology.

        Raises:
            KeyError: If the dict is missing a required field.
        """
        ret = dict()
        ontology_objects = list()
        ret["objects"] = ontology_objects
        for ontology_object in self.objects:
            ontology_objects.append(ontology_object.to_dict())

        ontology_classifications = list()
        ret["classifications"] = ontology_classifications
        for ontology_classification in self.classifications:
            ontology_classifications.append(ontology_classification.to_dict())

        return ret

    def add_object(
        self,
        name: str,
        shape: Shape,
        uid: Optional[int] = None,
        color: Optional[str] = None,
        feature_node_hash: Optional[str] = None,
    ) -> Object:
        """
        Adds an object class definition to the structure.

        .. code::

            structure = ontology_structure.OntologyStructure()

            eye = structure.add_object(
                name="Eye",
            )
            nose = structure.add_object(
                name="Nose",
            )
            nose_detail = nose.add_attribute(
                encord.objects.common.ChecklistAttribute,
            )
            nose_detail.add_option(feature_node_hash="2bc17c88", label="Is it a cute nose?")
            nose_detail.add_option(feature_node_hash="86eaa4f2", label="Is it a wet nose? ")

        Args:
            name: the user-visible name of the object
            shape: the kind of object (bounding box, polygon, etc). See :py:class:`encord.objects.common.Shape` enum for possible values
            uid: integer identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure
            color: the color of the object in the label editor. Normally auto-assigned, should be in '#1A2B3F' syntax.
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure

        Returns:
            the created object class that can be further customised with attributes.
        """
        if uid is None:
            if self.objects:
                uid = max([obj.uid for obj in self.objects]) + 1
            else:
                uid = 1
        else:
            if any([obj.uid == uid for obj in self.objects]):
                raise ValueError(f"Duplicate uid '{uid}'")

        if color is None:
            color_index = 0
            if self.objects:
                try:
                    color_index = AVAILABLE_COLORS.index(self.objects[-1].color) + 1
                    if color_index >= len(AVAILABLE_COLORS):
                        color_index = 0
                except ValueError:
                    pass
            color = AVAILABLE_COLORS[color_index]

        if feature_node_hash is None:
            feature_node_hash = str(uuid4())[:8]

        if any([obj.feature_node_hash == feature_node_hash for obj in self.objects]):
            raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

        obj = Object(uid, name, color, shape, feature_node_hash)
        self.objects.append(obj)
        return obj

    def add_classification(
        self,
        uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
    ) -> Classification:
        """
        Adds an classification definition to the ontology.

        .. code::

            structure = ontology_structure.OntologyStructure()

            cls = structure.add_classification(feature_node_hash="a39d81c0")
            cat_standing = cls.add_attribute(
                encord.objects.common.RadioAttribute,
                feature_node_hash="a6136d14",
                name="Is the cat standing?",
                required=True,
            )
            cat_standing.add_option(feature_node_hash="a3aeb48d", label="Yes")
            cat_standing.add_option(feature_node_hash="d0a4b373", label="No")

        Args:
            uid: integer identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure

        Returns:
            the created classification node. Note that classification attribute should be further specified by calling its `add_attribute()` method.
        """
        if uid is None:
            if self.classifications:
                uid = max([cls.uid for cls in self.classifications]) + 1
            else:
                uid = 1
        else:
            if any([cls.uid == uid for cls in self.classifications]):
                raise ValueError(f"Duplicate uid '{uid}'")

        if feature_node_hash is None:
            feature_node_hash = str(uuid4())[:8]

        if any([cls.feature_node_hash == feature_node_hash for cls in self.classifications]):
            raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

        cls = Classification(uid, feature_node_hash, list())
        self.classifications.append(cls)
        return cls


DATETIME_STRING_FORMAT = "%Y-%m-%d %H:%M:%S"


class OntologyUserRole(IntEnum):
    ADMIN = 0
    USER = 1


class Ontology(dict, Formatter):
    def __init__(
        self,
        title: str,
        structure: OntologyStructure,
        ontology_hash: str,
        description: Optional[str] = None,
    ):
        """
        DEPRECATED - prefer using the :class:`encord.ontology.Ontology` class instead.

        This class has dict-style accessors for backwards compatibility.
        Clients who are using this class for the first time are encouraged to use the property accessors and setters
        instead of the underlying dictionary.
        The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

        WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
        datastructure.
        """
        super().__init__(
            {
                "ontology_hash": ontology_hash,
                "title": title,
                "description": description,
                "structure": structure,
            }
        )

    @property
    def ontology_hash(self) -> str:
        return self["ontology_hash"]

    @property
    def title(self) -> str:
        return self["title"]

    @title.setter
    def title(self, value: str) -> None:
        self["title"] = value

    @property
    def description(self) -> str:
        return self["description"]

    @description.setter
    def description(self, value: str) -> None:
        self["description"] = value

    @property
    def structure(self) -> OntologyStructure:
        return self["structure"]

    @structure.setter
    def structure(self, value: OntologyStructure) -> None:
        self["structure"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> Ontology:
        return Ontology(
            title=json_dict["title"],
            description=json_dict["description"],
            ontology_hash=json_dict["ontology_hash"],
            structure=OntologyStructure.from_dict(json_dict["editor"]),
        )


def _frame_views_to_frame_numbers(
    frame_views: Sequence[Union[ObjectInstance.Annotation, ClassificationInstance.Annotation, LabelRowV2.FrameView]]
) -> List[int]:
    return [frame_view.frame for frame_view in frame_views]
