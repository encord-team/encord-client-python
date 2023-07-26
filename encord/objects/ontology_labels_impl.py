from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)
from uuid import uuid4

from encord.client import EncordClientProject
from encord.client import LabelRow as OrmLabelRow
from encord.constants.enums import DataType
from encord.exceptions import LabelRowError, OntologyError, WrongProjectTypeError
from encord.http.bundle import Bundle, BundleResultHandler, BundleResultMapper
from encord.http.limits import (
    LABEL_ROW_BUNDLE_CREATE_LIMIT,
    LABEL_ROW_BUNDLE_GET_LIMIT,
    LABEL_ROW_BUNDLE_SAVE_LIMIT,
)
from encord.objects.classification import Classification
from encord.objects.classification_instance import ClassificationInstance
from encord.objects.common import Attribute, OntologyNestedElement, Shape
from encord.objects.constants import (
    DATETIME_LONG_STRING_FORMAT,
    DEFAULT_CONFIDENCE,
    DEFAULT_MANUAL_ANNOTATION,
)
from encord.objects.coordinates import (
    BitmaskCoordinates,
    BoundingBoxCoordinates,
    Coordinates,
    PointCoordinate,
    PolygonCoordinates,
    PolylineCoordinates,
    RotatableBoundingBoxCoordinates,
)
from encord.objects.frames import Frames, frames_class_to_frames_list
from encord.objects.ontology_element import (
    OntologyElement,
    _assert_singular_result_list,
    _get_element_by_hash,
)
from encord.objects.ontology_object import Object
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.utils import _lower_snake_case, checked_cast, does_type_match
from encord.orm.formatter import Formatter
from encord.orm.label_row import (
    AnnotationTaskStatus,
    LabelRowMetadata,
    LabelStatus,
    WorkflowGraphNode,
)

log = logging.getLogger(__name__)

OntologyTypes = Union[Type[Object], Type[Classification]]
OntologyClasses = Union[Object, Classification]


@dataclass
class BundledGetRowsPayload:
    uids: List[str]
    get_signed_url: bool
    include_object_feature_hashes: Optional[Set[str]]
    include_classification_feature_hashes: Optional[Set[str]]
    include_reviews: bool


@dataclass
class BundledCreateRowsPayload:
    uids: List[str]


@dataclass
class BundledSaveRowsPayload:
    uids: List[str]
    payload: List[Dict]


class LabelRowV2:
    """
    This class represents a single label row. It is corresponding to exactly one data row within a project. It holds all
    the labels for that data row.

    You can access a many metadata fields with this class directly. If you want to read or write labels you will need to
    call :meth:`.initialise_labels()` first. To upload your added labels call :meth:`.save()`.
    """

    def __init__(
        self, label_row_metadata: LabelRowMetadata, project_client: EncordClientProject, ontology: Ontology
    ) -> None:
        self._project_client = project_client
        self._ontology = ontology

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
        """
        Returns the current labeling status for the label row.

        **Note**: This method is not supported for workflow-based projects. Please see our
        :ref:`workflow documentation <tutorials/workflows:Workflows>`
        for more details.
        """

        if self.__is_tms2_project:
            raise WrongProjectTypeError(
                '"label"_status property returns incorrect results for workflow-based projects.\
             Please use "workflow_graph_node" property instead.'
            )

        return self._label_row_read_only_data.label_status

    @property
    def annotation_task_status(self) -> AnnotationTaskStatus:
        """
        Returns the current annotation task status for the label row.

        **Note**: This method is not supported for workflow-based projects. Please see our
        :ref:`workflow documentation <tutorials/workflows:Workflows>`
        for more details.
        """
        if self.__is_tms2_project:
            raise WrongProjectTypeError(
                '"annotation_task_status" property returns incorrect results for workflow-based projects.\
             Please use "workflow_graph_node" property instead.'
            )

        assert self._label_row_read_only_data.annotation_task_status is not None  # Never None for Workflow projects

        return self._label_row_read_only_data.annotation_task_status

    @property
    def workflow_graph_node(self) -> Optional[WorkflowGraphNode]:
        return self._label_row_read_only_data.workflow_graph_node

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
        return self._ontology.structure

    @property
    def is_labelling_initialised(self) -> bool:
        """
        Whether you can start labelling or not. If this is `False`, call the member :meth:`.initialise_labels()` to
        read or write specific ObjectInstances or ClassificationInstances.
        """
        return self._is_labelling_initialised

    @property
    def __is_tms2_project(self) -> bool:
        return self.workflow_graph_node is not None

    def initialise_labels(
        self,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
        overwrite: bool = False,
        bundle: Optional[Bundle] = None,
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
            bundle: If not passed, initialisation is performed independently. If passed, it will be delayed and
                initialised along with other objects in the same bundle.
        """
        if self.is_labelling_initialised and not overwrite:
            raise LabelRowError(
                "You are trying to re-initialise a label row that has already been initialised. This would overwrite "
                "current labels. If this is your intend, set the `overwrite` flag to `True`."
            )

        if bundle is not None:
            self.__batched_initialise(
                bundle,
                uid=self.label_hash,
                get_signed_url=False,
                include_object_feature_hashes=include_object_feature_hashes,
                include_classification_feature_hashes=include_classification_feature_hashes,
                include_reviews=include_reviews,
            )
        else:
            if self.label_hash is None:
                label_row_dict = self._project_client.create_label_row(self.data_hash)
            else:
                label_row_dict = self._project_client.get_label_row(
                    uid=self.label_hash,
                    get_signed_url=False,
                    include_object_feature_hashes=include_object_feature_hashes,
                    include_classification_feature_hashes=include_classification_feature_hashes,
                    include_reviews=include_reviews,
                )

            self.from_labels_dict(label_row_dict)

    def __batched_initialise(
        self,
        bundle: Bundle,
        uid,
        get_signed_url,
        include_object_feature_hashes,
        include_classification_feature_hashes,
        include_reviews,
    ):
        if self.label_hash is None:
            bundle.add(
                operation=self._project_client.create_label_rows,
                request_reducer=self._bundle_create_rows_reducer,
                result_mapper=BundleResultMapper[OrmLabelRow](
                    result_mapping_predicate=self._bundle_create_rows_mapping_predicate,
                    result_handler=BundleResultHandler(predicate=self.data_hash, handler=self.from_labels_dict),
                ),
                payload=BundledCreateRowsPayload(
                    uids=[self.data_hash],
                ),
                limit=LABEL_ROW_BUNDLE_CREATE_LIMIT,
            )
        else:
            bundle.add(
                operation=self._project_client.get_label_rows,
                request_reducer=self._bundle_get_rows_reducer,
                result_mapper=BundleResultMapper[OrmLabelRow](
                    result_mapping_predicate=self._bundle_get_rows_mapping_predicate,
                    result_handler=BundleResultHandler(predicate=self.label_hash, handler=self.from_labels_dict),
                ),
                payload=BundledGetRowsPayload(
                    uids=[uid],
                    get_signed_url=get_signed_url,
                    include_object_feature_hashes=include_object_feature_hashes,
                    include_classification_feature_hashes=include_classification_feature_hashes,
                    include_reviews=include_reviews,
                ),
                limit=LABEL_ROW_BUNDLE_GET_LIMIT,
            )

    @staticmethod
    def _bundle_create_rows_reducer(
        bundle_payload: BundledCreateRowsPayload, payload: BundledCreateRowsPayload
    ) -> BundledCreateRowsPayload:
        bundle_payload.uids += payload.uids
        return bundle_payload

    @staticmethod
    def _bundle_get_rows_reducer(
        bundle_payload: BundledGetRowsPayload, payload: BundledGetRowsPayload
    ) -> BundledGetRowsPayload:
        bundle_payload.uids += payload.uids
        return bundle_payload

    @staticmethod
    def _bundle_get_rows_mapping_predicate(entry: OrmLabelRow) -> str:
        return entry["label_hash"]

    @staticmethod
    def _bundle_create_rows_mapping_predicate(entry: OrmLabelRow) -> str:
        return entry["data_hash"]

    def from_labels_dict(self, label_row_dict: dict) -> None:
        """
        If you have a label row dictionary in the same format that the Encord servers produce, you can initialise the
        LabelRow from that directly. In most cases you should prefer using the `initialise_labels` method.

        This function also initialises the label row.

        Calling this function will reset all the labels that are currently stored within this class.

        Args:
            label_row_dict: The dictionary of all labels as expected by the Encord format.
        """
        self._is_labelling_initialised = True

        self._label_row_read_only_data = self._parse_label_row_dict(label_row_dict)
        self._frame_to_hashes = defaultdict(set)
        self._classifications_to_frames = defaultdict(set)

        self._objects_map = dict()
        self._classifications_map = dict()
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

    def save(self, bundle: Optional[Bundle] = None) -> None:
        """
        Upload the created labels with the Encord server. This will overwrite any labels that someone has created
        in the platform in the meantime.

        Args:
            bundle: if not passed, save is executed immediately. If passed, it is executed as a part of the bundle
        """
        self._check_labelling_is_initalised()

        dict_labels = self.to_encord_dict()

        if bundle is None:
            self._project_client.save_label_row(uid=self.label_hash, label=dict_labels)
        else:
            assert self.label_hash is not None  # Checked earlier, assert is mostly to silence mypy
            bundle.add(
                operation=self._project_client.save_label_rows,
                request_reducer=self._batch_save_rows_reducer,
                result_mapper=None,
                payload=BundledSaveRowsPayload(uids=[self.label_hash], payload=[dict_labels]),
                limit=LABEL_ROW_BUNDLE_SAVE_LIMIT,
            )

    @staticmethod
    def _batch_save_rows_reducer(
        bundle_payload: BundledSaveRowsPayload, payload: BundledSaveRowsPayload
    ) -> BundledSaveRowsPayload:
        bundle_payload.uids += payload.uids
        bundle_payload.payload += payload.payload
        return bundle_payload

    def get_frame_view(self, frame: Union[int, str] = 0) -> FrameView:
        """
        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.
        """
        self._check_labelling_is_initalised()
        if isinstance(frame, str):
            frame_num = self.get_frame_number(frame)
            if frame_num is None:
                raise LabelRowError(f"Image hash {frame} not found in the label row")
        else:
            frame_num = frame

        return self.FrameView(self, self._label_row_read_only_data, frame_num)

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

        frames = set(_frame_views_to_frame_numbers(object_instance.get_annotations()))
        self._add_to_frame_to_hashes_map(object_instance, frames)

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

        frames = set(_frame_views_to_frame_numbers(classification_instance.get_annotations()))

        classification_hash = classification_instance.classification_hash
        already_present_frame = self._is_classification_already_present(
            classification_instance.ontology_item,
            frames,
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

        self._classifications_to_frames[classification_instance.ontology_item].update(frames)
        self._add_to_frame_to_hashes_map(classification_instance, frames)

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

    def to_encord_dict(self) -> Dict[str, Any]:
        """
        This is an internal helper function. Likely this should not be used by a user. To upload labels use the
        :meth:`.save()` function.
        """
        self._check_labelling_is_initalised()

        ret: Dict[str, Any] = {}
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

    def workflow_reopen(self) -> None:
        """
        A label row is returned to the first annotation stage for re-labeling.
        No data will be lost during this call.

        This method is only relevant for the projects that use the :ref:`Workflow <tutorials/workflows:Workflows>`
        feature, and will raise an error for pre-workflow projects.
        """
        if self.label_hash is None:
            # Label has not yet moved from the initial state, nothing to do
            return

        self._project_client.workflow_reopen([self.label_hash])

    def workflow_complete(self) -> None:
        """
         A label row is moved to the final workflow node, marking it as 'Complete'.

         This method can be called only for labels for which :meth:`.initialise_labels()` was called at least ance, and
         consequentially the "label_hash" field is not `None`.
        Please note that labels need not be initialized every time the workflow_complete() method is called.

         This method is only relevant for the projects that use the :ref:`Workflow <tutorials/workflows:Workflows>`
         feature, and will raise an error for projects that don't use Workflows.
        """
        if self.label_hash is None:
            raise LabelRowError(
                "For this operation you will need to initialise labelling first. Call the .initialise_labels() "
                "to do so first."
            )

        self._project_client.workflow_complete([self.label_hash])

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
            elif self._label_row_read_only_data.width is not None:
                return self._label_row_read_only_data.width
            else:
                raise LabelRowError(f"Width is expected but not set for the data type {self._label_row.data_type}")

        @property
        def height(self) -> int:
            if self._label_row.data_type in [DataType.IMG_GROUP]:
                return self._frame_level_data().height
            elif self._label_row_read_only_data.height is not None:
                return self._label_row_read_only_data.height
            else:
                raise LabelRowError(f"Height is expected but not set for the data type {self._label_row.data_type}")

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
            created_at: Optional[datetime] = None,
            created_by: Optional[str] = None,
            confidence: float = DEFAULT_CONFIDENCE,
            manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
            last_edited_at: Optional[datetime] = None,
            last_edited_by: Optional[str] = None,
        ) -> None:
            if created_at is None:
                created_at = datetime.now()

            if last_edited_at is None:
                last_edited_at = datetime.now()

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
        """This is an internal helper class. A user should not directly interact with it."""

        image_hash: str
        image_title: str
        file_type: str
        frame_number: int
        width: int
        height: int
        data_link: Optional[str] = None

    @dataclass(frozen=True)
    class LabelRowReadOnlyData:
        """This is an internal helper class. A user should not directly interact with it."""

        label_hash: Optional[str]
        """This is None if the label row does not have any labels and was not initialised for labelling."""
        created_at: Optional[datetime]
        """This is None if the label row does not have any labels and was not initialised for labelling."""
        last_edited_at: Optional[datetime]
        """This is None if the label row does not have any labels and was not initialised for labelling."""
        data_hash: str
        data_type: DataType
        label_status: LabelStatus
        annotation_task_status: Optional[AnnotationTaskStatus]
        workflow_graph_node: Optional[WorkflowGraphNode]
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

    def _to_object_answers(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        for obj in self._objects_map.values():
            all_static_answers = self._get_all_static_answers(obj)
            ret[obj.object_hash] = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }
        return ret

    def _to_object_actions(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        for obj in self._objects_map.values():
            all_static_answers = self._dynamic_answers_to_encord_dict(obj)
            if len(all_static_answers) == 0:
                continue
            ret[obj.object_hash] = {
                "actions": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }
        return ret

    def _to_classification_answers(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
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
    def _get_all_static_answers(object_instance: ObjectInstance) -> List[Dict[str, Any]]:
        """Essentially convert to the JSON format of all the static answers."""
        ret = []
        for answer in object_instance._get_all_static_answers():
            d_opt = answer.to_encord_dict()
            if d_opt is not None:
                ret.append(d_opt)
        return ret

    @staticmethod
    def _dynamic_answers_to_encord_dict(object_instance: ObjectInstance) -> List[Dict[str, Any]]:
        ret = []
        for answer, ranges in object_instance._get_all_dynamic_answers():
            d_opt = answer.to_encord_dict(ranges)
            if d_opt is not None:
                ret.append(d_opt)
        return ret

    def _to_encord_data_units(self) -> Dict[str, Any]:
        ret = {}
        frame_level_data = self._label_row_read_only_data.frame_level_data
        for value in frame_level_data.values():
            ret[value.image_hash] = self._to_encord_data_unit(value)

        return ret

    def _to_encord_data_unit(self, frame_level_data: FrameLevelImageGroupData) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}

        data_type = self._label_row_read_only_data.data_type
        if data_type == DataType.IMG_GROUP:
            data_sequence: Union[str, int] = str(frame_level_data.frame_number)
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

    def _to_encord_labels(self, frame_level_data: FrameLevelImageGroupData) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        data_type = self._label_row_read_only_data.data_type

        if data_type in [DataType.IMAGE, DataType.IMG_GROUP]:
            frame = frame_level_data.frame_number
            ret.update(self._to_encord_label(frame))

        elif data_type in [DataType.VIDEO, DataType.DICOM]:
            for frame in self._frame_to_hashes.keys():
                ret[str(frame)] = self._to_encord_label(frame)

        return ret

    def _to_encord_label(self, frame: int) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}

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
    ) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}

        object_instance_annotation = object_.get_annotation(frame)
        coordinates = object_instance_annotation.coordinates
        ontology_hash = object_.ontology_item.feature_node_hash
        ontology_object = self._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

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

        self._add_coordinates_to_encord_object(coordinates, frame, ret)

        return ret

    def _add_coordinates_to_encord_object(
        self, coordinates: Coordinates, frame: int, encord_object: Dict[str, Any]
    ) -> None:
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
        elif isinstance(coordinates, BitmaskCoordinates):
            frame_view = self.get_frame_view(frame)
            if not (
                frame_view.height == coordinates._encoded_bitmask.height
                and frame_view.width == coordinates._encoded_bitmask.width
            ):
                raise ValueError("Bitmask resolution doesn't match the media resolution")
            encord_object["bitmask"] = coordinates.to_dict()
        else:
            raise NotImplementedError(f"adding coordinatees for this type not yet implemented {type(coordinates)}")

    def _to_encord_classifications_list(self, frame: int) -> list:
        ret: List[Dict[str, Any]] = []

        classifications = self.get_classification_instances(filter_frames=frame)
        for classification in classifications:
            encord_classification = self._to_encord_classification(classification, frame)
            ret.append(encord_classification)

        return ret

    def _to_encord_classification(self, classification: ClassificationInstance, frame: int) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}

        annotation = classification.get_annotation(frame)
        classification_feature_hash = classification.ontology_item.feature_node_hash
        ontology_classification = self._ontology.structure.get_child_by_hash(
            classification_feature_hash, type_=Classification
        )
        attribute_hash = classification.ontology_item.attributes[0].feature_node_hash
        ontology_attribute = self._ontology.structure.get_child_by_hash(attribute_hash, type_=Attribute)

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

    def _add_frames_to_classification(self, classification: Classification, frames: Iterable[int]) -> None:
        self._classifications_to_frames[classification].update(set(frames))

    def _remove_frames_from_classification(self, classification: Classification, frames: Iterable[int]) -> None:
        present_frames = self._classifications_to_frames.get(classification, set())
        for frame in frames:
            present_frames.remove(frame)

    def _add_to_frame_to_hashes_map(
        self, label_item: Union[ObjectInstance, ClassificationInstance], frames: Iterable[int]
    ) -> None:
        for frame in frames:
            self.add_to_single_frame_to_hashes_map(label_item, frame)

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
            workflow_graph_node=label_row_metadata.workflow_graph_node,
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
            annotation_task_status=label_row_dict.get("annotation_task_status", None),
            workflow_graph_node=label_row_dict.get("workflow_graph_node", None),
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
        ontology = self._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]

        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
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
            raise NotImplementedError("Got a skeleton object, which is not supported yet")
        elif "bitmask" in frame_object_label:
            return BitmaskCoordinates.from_dict(frame_object_label)
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
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]

        label_class = self._ontology.structure.get_child_by_hash(feature_hash, type_=Classification)
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


OntologyElementT = TypeVar("OntologyElementT", bound=OntologyElement)


@dataclass
class OntologyStructure:
    objects: List[Object] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Optional[Type[OntologyElementT]] = None,
    ) -> OntologyElementT:
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
                return checked_cast(object_, type_)

            found_item = _get_element_by_hash(feature_node_hash, object_.attributes)
            if found_item is not None:
                return checked_cast(found_item, type_)

        for classification in self.classifications:
            if classification.feature_node_hash == feature_node_hash:
                return checked_cast(classification, type_)
            found_item = _get_element_by_hash(feature_node_hash, classification.attributes)
            if found_item is not None:
                return checked_cast(found_item, type_)

        raise OntologyError(f"Item not found: can't find an item with a hash {feature_node_hash} in the ontology.")

    def get_child_by_title(
        self,
        title: str,
        type_: Optional[Type[OntologyElementT]] = None,
    ) -> OntologyElementT:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _assert_singular_result_list(found_items, title, type_)
        return found_items[0]

    def get_children_by_title(
        self,
        title: str,
        type_: Optional[Type[OntologyElementT]] = None,
    ) -> List[OntologyElementT]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        ret: List[OntologyElement] = []
        for object_ in self.objects:
            if object_.title == title and does_type_match(object_, type_):
                ret.append(object_)

            if type_ is None or issubclass(type_, OntologyNestedElement):
                found_items = object_.get_children_by_title(title, type_=type_)
                ret.extend(found_items)

        for classification in self.classifications:
            if classification.title == title and does_type_match(classification, type_):
                ret.append(classification)

            if type_ is None or issubclass(type_, OntologyNestedElement):
                found_items = classification.get_children_by_title(title, type_=type_)
                ret.extend(found_items)

        # type checks in the code above guarantee the type conformity of the return value
        # but there is no obvious way to tell that to mypy, so just casting here for now
        return cast(List[OntologyElementT], ret)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> OntologyStructure:
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

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns:
            The dict equivalent to the ontology.

        Raises:
            KeyError: If the dict is missing a required field.
        """
        ret: Dict[str, List[Dict[str, Any]]] = dict()
        ontology_objects: List[Dict[str, Any]] = list()
        ret["objects"] = ontology_objects
        for ontology_object in self.objects:
            ontology_objects.append(ontology_object.to_dict())

        ontology_classifications: List[Dict[str, Any]] = list()
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

        obj = Object(uid=uid, name=name, color=color, shape=shape, feature_node_hash=feature_node_hash)
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

        cls = Classification(uid=uid, feature_node_hash=feature_node_hash, attributes=list())
        self.classifications.append(cls)
        return cls


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
