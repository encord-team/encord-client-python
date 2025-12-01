"""---
title: "Objects - Ontology Labels"
slug: "sdk-ref-objects-ont-labels"
hidden: false
metadata:
  title: "Objects - Ontology Labels"
  description: "Encord SDK Objects - Ontology Labels."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Type, Union, cast
from typing import Any, Dict, Iterable, List, Literal, Optional, Sequence, Set, Tuple, Type, Union, cast, overload
from uuid import UUID

from encord.client import EncordClientProject
from encord.client import LabelRow as OrmLabelRow
from encord.common.deprecated import deprecated
from encord.common.range_manager import RangeManager
from encord.common.time_parser import format_datetime_to_long_string_optional, parse_datetime_optional
from encord.constants.enums import DataType, SpaceType, is_geometric
from encord.exceptions import LabelRowError, WrongProjectTypeError
from encord.http.bundle import Bundle, BundleResultHandler, BundleResultMapper, bundled_operation
from encord.http.limits import (
    LABEL_ROW_BUNDLE_CREATE_LIMIT,
    LABEL_ROW_BUNDLE_GET_LIMIT,
)
from encord.objects import Shape
from encord.objects.attributes import Attribute
from encord.objects.bundled_operations import (
    BundledCreateRowsPayload,
    BundledGetRowsPayload,
    BundledGetStorageItemPayload,
    BundledSaveRowsPayload,
    BundledSetPriorityPayload,
    BundledWorkflowCompletePayload,
    BundledWorkflowReopenPayload,
)
from encord.objects.classification import Classification
from encord.objects.classification_instance import (
    ClassificationInstance,
)
from encord.objects.constants import (  # pylint: disable=unused-import # for backward compatibility
    DEFAULT_CONFIDENCE,
    DEFAULT_MANUAL_ANNOTATION,
)
from encord.objects.coordinates import (
    AudioCoordinates,
    BitmaskCoordinates,
    BoundingBoxCoordinates,
    Coordinates,
    CuboidCoordinates,
    HtmlCoordinates,
    PointCoordinate,
    PointCoordinate3D,
    PolygonCoordinates,
    PolygonCoordsToDict,
    PolylineCoordinates,
    RotatableBoundingBoxCoordinates,
    SkeletonCoordinates,
    TextCoordinates,
    get_coordinates_from_frame_object_dict,
)
from encord.objects.frames import (
    Frames,
    Range,
    Ranges,
    frames_class_to_frames_list,
    ranges_list_to_ranges,
    ranges_to_list,
)
from encord.objects.html_node import HtmlRange, HtmlRangeDict
from encord.objects.metadata import DataGroupMetadata, DICOMSeriesMetadata, DICOMSliceMetadata
from encord.objects.ontology_object import Object
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.ontology_structure import OntologyStructure
from encord.objects.spaces.annotation.base_annotation import ClassificationAnnotation, ObjectAnnotation
from encord.objects.spaces.base_space import Space, SpaceT
from encord.objects.spaces.image_space import ImageSpace
from encord.objects.spaces.types import SpaceInfo
from encord.objects.spaces.video_space import VideoSpace
from encord.objects.types import (
    AttributeDict,
    BaseFrameObject,
    ClassificationAnswer,
    DynamicAttributeObject,
    FrameClassification,
    FrameObject,
    LabelRowDict,
    ObjectAction,
    ObjectAnswerForNonGeometric,
    _is_containing_metadata,
)
from encord.objects.utils import _lower_snake_case
from encord.ontology import Ontology
from encord.orm import storage as orm_storage
from encord.orm.label_row import (
    AnnotationTaskStatus,
    LabelRowMetadata,
    LabelStatus,
    WorkflowGraphNode,
)
from encord.storage import STORAGE_BUNDLE_CREATE_LIMIT, StorageItem
from encord.utilities.type_utilities import exhaustive_guard

log = logging.getLogger(__name__)

OntologyTypes = Union[Type[Object], Type[Classification]]
OntologyClasses = Union[Object, Classification]


class LabelRowV2:
    """This class represents a single label row. It corresponds to exactly one data row within a project and holds all
    the labels for that data row.

    You can access many metadata fields with this class directly. To read or write labels, you need to call
    :meth:`encord.objects.ontology_labels_impl.LabelRowV2.initialise_labels` first. To upload your added labels, call :meth:`encord.objects.ontology_labels_impl.LabelRowV2.save`.
    """

    def __init__(
        self,
        label_row_metadata: LabelRowMetadata,
        project_client: EncordClientProject,
        ontology: Ontology,
    ) -> None:
        self._project_client = project_client
        self._ontology = ontology

        self._label_row_read_only_data: LabelRowV2.LabelRowReadOnlyData = self._parse_label_row_metadata(
            label_row_metadata
        )

        self._is_labelling_initialised = False

        self._frame_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        # ^ frames to object and classification hashes

        self._metadata: Optional[Union[DICOMSeriesMetadata, DataGroupMetadata]] = None
        self._frame_metadata: defaultdict[int, Optional[DICOMSliceMetadata]] = defaultdict(lambda: None)

        self._space_map: dict[str, Space] = self._initiate_spaces(
            spaces_info=label_row_metadata.spaces,
        )
        self._space_objects_map: dict[str, ObjectInstance] = {}
        self._space_classifications_map: dict[str, ClassificationInstance] = {}

        self._classifications_to_frames: defaultdict[Classification, Set[int]] = defaultdict(set)
        self._classifications_to_ranges: defaultdict[Classification, RangeManager] = defaultdict(RangeManager)

        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()
        # ^ conveniently a dict is ordered in Python. Use this to our advantage to keep the labels in order
        # at least at the final objects_index/classifications_index level.

        self._storage_item: Optional[StorageItem] = None

    @property
    def label_hash(self) -> Optional[str]:
        """Returns the hash of the label row.

        Returns:
            Optional[str]: The label row hash or None if not set.
        """
        return self._label_row_read_only_data.label_hash

    @property
    def branch_name(self) -> str:
        """Returns the branch name of the label row.

        Returns:
            str: The branch name.
        """
        return self._label_row_read_only_data.branch_name

    @property
    def data_hash(self) -> str:
        """Returns the hash of the data row.

        Returns:
            str: The data row hash.
        """
        return self._label_row_read_only_data.data_hash

    @property
    def group_hash(self) -> Optional[str]:
        """Returns the group hash of the data row.

        Only present if this label row is a child of a data group

        Returns:
            Optional[str]: The data group hash.
        """
        return self._label_row_read_only_data.group_hash

    @property
    def dataset_hash(self) -> str:
        """Returns the hash of the dataset.

        Returns:
            str: The dataset hash.
        """
        return self._label_row_read_only_data.dataset_hash

    @property
    def dataset_title(self) -> str:
        """Returns the title of the dataset.

        Returns:
            str: The dataset title.
        """
        return self._label_row_read_only_data.dataset_title

    @property
    def data_title(self) -> str:
        """Returns the title of the data row.

        Returns:
            str: The data row title.
        """
        return self._label_row_read_only_data.data_title

    @property
    def data_type(self) -> DataType:
        """Returns the data type of the label row.

        Returns:
            DataType: The data type.
        """
        return self._label_row_read_only_data.data_type

    @property
    def file_type(self) -> Optional[str]:
        """Returns the file type of the data row.

        Returns:
            str | None: The file type or None if not set.
        """
        return self._label_row_read_only_data.file_type

    @property
    def client_metadata(self) -> Optional[dict]:
        """Returns the client metadata associated with the label row.

        Returns:
            dict | None: The client metadata or None if not set.
        """
        return self._label_row_read_only_data.client_metadata

    @property
    def label_status(self) -> LabelStatus:
        """Returns the current labeling status for the label row.

        **Note**: This method is not supported for workflow-based projects. Please see our
        :ref:`workflow documentation <tutorials/workflows:Workflows>` for more details.

        Returns:
            LabelStatus: The current labeling status.

        Raises:
            WrongProjectTypeError: If used with workflow-based projects.
        """
        if self.__is_tms2_project:
            raise WrongProjectTypeError(
                '"label_status" property returns incorrect results for workflow-based projects.\
             Please use "workflow_graph_node" property instead.'
            )

        return self._label_row_read_only_data.label_status

    @property
    def annotation_task_status(self) -> AnnotationTaskStatus:
        """Returns the current annotation task status for the label row.

        **Note**: This method is not supported for workflow-based projects. Please see our
        :ref:`workflow documentation <tutorials/workflows:Workflows>` for more details.

        Returns:
            AnnotationTaskStatus: The current annotation task status.

        Raises:
            WrongProjectTypeError: If used with workflow-based projects.
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
        """Returns the workflow graph node associated with the label row.

        Returns:
            Optional[WorkflowGraphNode]: The workflow graph node or None if not set.
        """
        return self._label_row_read_only_data.workflow_graph_node

    @property
    def is_shadow_data(self) -> bool:
        """Indicates if the label row is shadow data.

        Returns:
            bool: True if the label row is shadow data, False otherwise.
        """
        return self._label_row_read_only_data.is_shadow_data

    @property
    def created_at(self) -> Optional[datetime]:
        """Returns the creation date of the label row.

        Returns:
            Optional[datetime]: The creation date or None if not yet created.
        """
        return self._label_row_read_only_data.created_at

    @property
    def last_edited_at(self) -> Optional[datetime]:
        """Returns the last edited date of the label row.

        Returns:
            Optional[datetime]: The last edited date or None if not yet edited.
        """
        return self._label_row_read_only_data.last_edited_at

    @property
    def number_of_frames(self) -> int:
        """Returns the number of frames in the label row.

        Returns:
            int: The number of frames.
        """
        return self._label_row_read_only_data.number_of_frames

    @property
    def duration(self) -> Optional[float]:
        """Returns the duration of the video data type.

        Returns:
            Optional[float]: The duration or None if not applicable.
        """
        return self._label_row_read_only_data.duration

    @property
    def fps(self) -> Optional[float]:
        """Returns the frames per second (fps) of the video data type.

        Returns:
            Optional[float]: The fps or None if not applicable.
        """
        return self._label_row_read_only_data.fps

    @property
    def data_link(self) -> Optional[str]:
        """Returns the data link to the underlying object in either cloud storage or Encord storage. This will be `None`
        for DICOM series or image groups created without performance optimizations, as there is no single underlying
        file for these data types.

        This property will contain a signed URL if :meth:`encord.objects.ontology_labels_impl.LabelRowV2.initialise_labels` was called with `include_signed_url=True`.

        Returns:
            Optional[str]: The data link or None if not applicable.
        """
        return self._label_row_read_only_data.data_link

    @property
    def width(self) -> Optional[int]:
        """Returns the width of the image data type.

        This is `None` for image groups without performance optimization, as there is no single underlying width
        for this data type.

        Returns:
            Optional[int]: The width or None if not applicable.
        """
        return self._label_row_read_only_data.width

    @property
    def height(self) -> Optional[int]:
        """Returns the height of the image data type.

        This is `None` for image groups without performance optimization, as there is no single underlying height
        for this data type.

        Returns:
            Optional[int]: The height or None if not applicable.
        """
        return self._label_row_read_only_data.height

    @property
    def audio_codec(self) -> Optional[str]:
        """Returns the codec of the audio data type.

        This only applies to audio data types, and returns None for all other data types.

        Returns:
            Optional[str]: The codec or None if not applicable.
        """
        return self._label_row_read_only_data.audio_codec

    @property
    def audio_sample_rate(self) -> Optional[int]:
        """Returns the sample rate of the audio data type.

        This only applies to audio data types, and returns None for all other data types.

        Returns:
            Optional[int]: The sample rate or None if not applicable.
        """
        return self._label_row_read_only_data.audio_sample_rate

    @property
    def audio_bit_depth(self) -> Optional[int]:
        """Returns the bit depth of the audio data type.

        This only applies to audio data types, and returns None for all other data types.

        Returns:
            Optional[int]: The bit depth or None if not applicable.
        """
        return self._label_row_read_only_data.audio_bit_depth

    @property
    def audio_num_channels(self) -> Optional[int]:
        """Returns the number of channels of the audio data type.

        This only applies to audio data types, and returns None for all other data types.

        Returns:
            Optional[int]: The number of channels or None if not applicable.
        """
        return self._label_row_read_only_data.audio_num_channels

    @property
    def backing_item_uuid(self) -> Optional[UUID]:
        """Returns the unique identifier (UUID) for the backing storage item associated with this label row.

        While it is always included in server responses, it is marked as optional for backward compatibility with earlier versions.

        Returns:
            Optional[UUID]: The backing storage item id or None if not found.
        """
        # TODO: Mark required in 0.2 release
        return self._label_row_read_only_data.backing_item_uuid

    @property
    def task_uuid(self) -> Optional[UUID]:
        """Returns the workflow task uuids for the task associated with the data unit.

        This property only works for workflow-based projects.

        Returns:
            Optional[UUID]: The workflow task uuid or None if not applicable.

        Raises:
            WrongProjectTypeError: If used with non-workflow-based projects.
        """
        if not self.__is_tms2_project:
            raise WrongProjectTypeError('"task_uuid" property only works with workflow-based projects.')

        return self._label_row_read_only_data.task_uuid

    @property
    def priority(self) -> Optional[float]:
        """Returns the workflow priority for the task associated with the data unit.

        This property only works for workflow-based projects.

        It is None for label rows in the "complete" state.

        Returns:
            Optional[float]: The workflow priority or None if not applicable.

        Raises:
            WrongProjectTypeError: If used with non-workflow-based projects.
        """
        if not self.__is_tms2_project:
            raise WrongProjectTypeError('"priority" property only works with workflow-based projects.')

        return self._label_row_read_only_data.priority

    @property
    def is_valid(self) -> bool:
        """Indicates if the labels are valid.

        For labels uploaded via the SDK, a check is run to ensure that the labels are valid.
        This property returns `True` if the labels have correct structure and match the project ontology.

        If it is `False`, then loading the labels via `LabelRowV2` will raise an error, and the label editor
        will not be able to load the labels.

        You can call :meth:`encord.objects.ontology_labels_impl.LabelRowV2.get_validation_errors` to get the validation error messages.

        Returns:
            bool: True if the labels are valid, False otherwise.
        """
        return self._label_row_read_only_data.is_valid

    @property
    def ontology_structure(self) -> OntologyStructure:
        """Get the corresponding ontology structure."""
        return self._ontology.structure

    @property
    def is_labelling_initialised(self) -> bool:
        """Check if labelling is initialized.

        Returns:
            bool: `True` if labelling is initialized, `False` otherwise.

        If this is `False`, call the :meth:`encord.objects.ontology_labels_impl.LabelRowV2.initialise_labels` method to read or write specific
        ObjectInstances or ClassificationInstances.
        """
        return self._is_labelling_initialised

    @property
    def __is_tms2_project(self) -> bool:
        return self.workflow_graph_node is not None

    @property
    def assigned_user_email(self) -> Optional[str]:
        """Email of the user assigned to annotation or review task for a workflow-based project.
        In case of completed task, it is None.

        Returns:
            str | None: The email of the user assigned to the data.

        """
        return self._label_row_read_only_data.assigned_user_email

    @property
    def last_actioned_by_user_email(self) -> Optional[str]:
        """Email of the user who last actioned the data.

        Returns:
            str | None: The email of the user who last actioned the data.
        """
        return self._label_row_read_only_data.last_actioned_by_user_email

    def get_storage_item(self, get_signed_urls: bool = False) -> StorageItem:
        """Returns the storage item associated with the label row.
        This function can be used to get storage item details like storage folder, signed url, created at, item type, client metadata, etc.
        """
        if self._label_row_read_only_data.backing_item_uuid is None:
            raise LabelRowError("Storage item is not found for the label row")

        if not self._storage_item:
            self._storage_item = StorageItem._get_item(
                self._project_client._api_client,
                self._label_row_read_only_data.backing_item_uuid,
                get_signed_url=get_signed_urls,
            )

        return self._storage_item

    def initialise_storage_item(self, get_signed_url: bool = False, bundle: Optional[Bundle] = None) -> None:
        """Initialise the storage item associated with the label row.

        This function will download the storage item details from the Encord server.
        if you want to get the signed url, you can set the get_signed_url to True.

        Args:
            get_signed_url: If `True`,is set true, you can get the signed url from LabelRowV2.get_storage_item().get_signed_url()
            bundle: If not provided, initialization is performed independently. If provided,
                initialization is delayed and performed along with other objects in the same bundle.
        """

        if self._label_row_read_only_data.backing_item_uuid is None:
            raise LabelRowError("Storage item is not found for the label row")

        bundled_operation(
            bundle,
            operation=self._project_client._api_client.get_bound_operation(StorageItem._get_items_bulk),
            payload=BundledGetStorageItemPayload(
                item_uuids=[str(self._label_row_read_only_data.backing_item_uuid)],
                get_signed_url=get_signed_url,
            ),
            result_mapper=BundleResultMapper[orm_storage.StorageItem](
                result_mapping_predicate=lambda r: str(r.uuid),
                result_handler=BundleResultHandler(
                    predicate=str(self._label_row_read_only_data.backing_item_uuid), handler=self._set_orm_item
                ),
            ),
            limit=STORAGE_BUNDLE_CREATE_LIMIT,
        )

    def _set_orm_item(self, orm_storage_item: orm_storage.StorageItem) -> None:
        self._storage_item = StorageItem(self._project_client._api_client, orm_storage_item)

    def initialise_labels(
        self,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
        include_archived: bool = False,
        overwrite: bool = False,
        bundle: Optional[Bundle] = None,
        *,
        include_signed_url: bool = False,
    ) -> None:
        """Initialize labels from the Encord server.

        This function downloads or exports labels stored on the Encord server and performs
        any other reading or writing operations. If you only want to inspect a subset of labels,
        you can filter them. Note that filtering and later uploading will delete all previously
        filtered labels.

        If the label is not in progress, this sets the label status to `LabelStatus.LABEL_IN_PROGRESS`.

        Args:
            include_object_feature_hashes: If `None`, all objects will be included. Otherwise,
                only objects with the specified feature hashes will be included.
                WARNING: Use this filter only for reading labels. Saving a filtered subset will
                delete all other object instances stored in the Encord platform.
            include_classification_feature_hashes: If `None`, all classifications will be included.
                Otherwise, only classifications with the specified feature hashes will be included.
                WARNING: Use this filter only for reading labels. Saving a filtered subset will
                delete all other classification instances stored in the Encord platform.
            include_reviews: Whether to request read-only information about the reviews of the label row.
            include_archived: Whether to include labels whose ontology features are archived
            overwrite: If `True`, overwrite current labels with those stored in the Encord server.
                If `False` and the label row is already initialized, this function will raise an error.
            bundle: If not provided, initialization is performed independently. If provided,
                initialization is delayed and performed along with other objects in the same bundle.
            include_signed_url: If `True`, the :attr:`.data_link` property will contain a signed URL.
                See documentation for :attr:`.data_link` for more details.
        """
        if self.is_labelling_initialised and not overwrite:
            raise LabelRowError(
                "You are trying to re-initialise a label row that has already been initialized. This would overwrite "
                "current labels. If this is your intend, set the `overwrite` flag to `True`."
            )

        if not self.label_hash:
            # If label_hash is None, it means we need to explicitly create the label row first
            bundled_operation(
                bundle,
                operation=self._project_client.create_label_rows,
                payload=BundledCreateRowsPayload(
                    uids=[self.data_hash], get_signed_url=include_signed_url, branch_name=self.branch_name
                ),
                result_mapper=BundleResultMapper[OrmLabelRow](
                    result_mapping_predicate=lambda r: r["data_hash"],
                    result_handler=BundleResultHandler(predicate=self.data_hash, handler=self.from_labels_dict),
                ),
                limit=LABEL_ROW_BUNDLE_CREATE_LIMIT,
            )
        else:
            bundled_operation(
                bundle,
                operation=self._project_client.get_label_rows,
                payload=BundledGetRowsPayload(
                    uids=[self.label_hash],
                    get_signed_url=include_signed_url,
                    include_object_feature_hashes=include_object_feature_hashes,
                    include_classification_feature_hashes=include_classification_feature_hashes,
                    include_reviews=include_reviews,
                    include_archived=include_archived,
                ),
                result_mapper=BundleResultMapper[OrmLabelRow](
                    result_mapping_predicate=lambda r: r["label_hash"],
                    result_handler=BundleResultHandler(predicate=self.label_hash, handler=self.from_labels_dict),
                ),
                limit=LABEL_ROW_BUNDLE_GET_LIMIT,
            )

    def from_labels_dict(self, label_row_dict: dict) -> None:
        """Initialize the LabelRow from a label row dictionary.

        This function also initializes the label row. It resets all the labels currently
        stored within this class.

        Args:
            label_row_dict: The dictionary of all labels in the Encord format.
        """
        self._is_labelling_initialised = True

        self._label_row_read_only_data = self._parse_label_row_dict(label_row_dict)
        self._frame_to_hashes = defaultdict(set)
        self._classifications_to_frames = defaultdict(set)
        self._classifications_to_ranges = defaultdict(RangeManager)

        self._metadata = None
        self._frame_metadata = defaultdict(lambda: None)

        self._objects_map = dict()
        self._classifications_map = dict()

        # We need to do below three in order:
        # 1. Parse labels on root
        # 2. Parse labels on spaces
        # 3. Add dynamic attributes to objects on root & spaces
        self._parse_labels_from_dict(label_row_dict)
        spaces_dict = label_row_dict.get("spaces", {})
        self._parse_space_labels(
            spaces_info=spaces_dict,
            object_answers=label_row_dict["object_answers"],
            classification_answers=label_row_dict["classification_answers"],
        )
        self._add_action_answers(label_row_dict)

    def get_image_hash(self, frame_number: int) -> Optional[str]:
        """Get the corresponding image hash for the frame number.

        Args:
            frame_number: The frame number.

        Returns:
            Optional[str]: The image hash if the frame number is within bounds, `None` otherwise.

        Raises:
            LabelRowError: If this function is used for non-image data types.
        """
        self._check_labelling_is_initalised()

        if self.data_type not in (DataType.IMAGE, DataType.IMG_GROUP):
            raise LabelRowError("This function is only supported for label rows of image or image group data types.")

        return self._label_row_read_only_data.frame_to_image_hash.get(frame_number)

    def get_frame_number(self, image_hash: str) -> Optional[int]:
        """Get the corresponding frame number for the image hash.

        Args:
            image_hash: The image hash.

        Returns:
            Optional[int]: The frame number if the image hash is found, `None` otherwise.

        Raises:
            LabelRowError: If this function is used for non-image data types.
        """
        self._check_labelling_is_initalised()

        if self.data_type not in (DataType.IMAGE, DataType.IMG_GROUP):
            raise LabelRowError("This function is only supported for label rows of image or image group data types.")
        return self._label_row_read_only_data.image_hash_to_frame[image_hash]

    def get_spaces(self) -> list[Space]:
        return list(self._space_map.values())

    @overload
    def get_space(
        self,
        *,
        id: str,
        type_: Literal["video"],
    ) -> VideoSpace:
        pass

    @overload
    def get_space(self, *, id: str, type_: Literal["image"]) -> ImageSpace:
        pass

    @overload
    def get_space(self, *, layout_key: str, type_: Literal["video"]) -> VideoSpace:
        pass

    @overload
    def get_space(self, *, layout_key: str, type_: Literal["image"]) -> ImageSpace:
        pass

    def get_space(
        self,
        *,
        id: Optional[str] = None,
        layout_key: Optional[str] = None,
        type_: Union[Literal["video"], Literal["image"]],
    ) -> Space:
        """Retrieves a single space which matches the specified id and type.
        Throws an exception if more than one or no space with the specified id and type is found.
        Args:
            id: The id of the space to find.
            layout_key: The layout key of the data unit within its data group layout.
            type_: Type to check the type of the space.
        Returns:
            The child node with the specified title and type.
        Raises:
            OntologyError: If more than one or no matching child is found.
        """
        if id is not None and layout_key is not None:
            raise LabelRowError("Only one of id and layout_key can be specified.")

        if id is not None:
            for element in self._space_map.values():
                if element.space_id == id:
                    return element

        if layout_key is not None:
            for element in self._space_map.values():
                if isinstance(element, VideoSpace) or isinstance(element, ImageSpace):
                    if element.layout_key == layout_key:
                        return element

        raise LabelRowError(f"Could not find space with given id {id} ")

    def save(self, bundle: Optional[Bundle] = None, validate_before_saving: bool = False) -> None:
        """Upload the created labels to the Encord server.

        This will overwrite any labels that someone else has created on the platform in the meantime.

        Args:
            bundle: If not provided, save is executed immediately. If provided, save is executed
                as part of the bundle.
            validate_before_saving: Enable stricter server-side integrity checks. Default is `False`.
        """
        self._check_labelling_is_initalised()
        assert self.label_hash is not None  # Checked earlier, assert is just to silence mypy

        bundled_operation(
            bundle,
            self._project_client.save_label_rows,
            payload=BundledSaveRowsPayload(
                uids=[self.label_hash], payload=[self.to_encord_dict()], validate_before_saving=validate_before_saving
            ),
        )

    @property
    def metadata(self) -> Optional[Union[DICOMSeriesMetadata, DataGroupMetadata]]:
        """Get metadata for the given data type.

        Returns:
            Optional[DICOMSeriesMetadata]: Metadata for the data type, or `None` if not supported.

        Currently only supported for DICOM. Returns `None` for other formats.

        Label row needs to be initialized before using this property.
        """
        self._check_labelling_is_initalised()
        return self._metadata

    def get_frame_view(self, frame: Union[int, str] = 0) -> FrameView:
        """Get a view of the specified frame.

        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.

        Returns:
            FrameView: A view of the specified frame.
        """
        self._method_not_supported_for_audio()

        self._check_labelling_is_initalised()
        if isinstance(frame, str):
            frame_num = self.get_frame_number(frame)
            if frame_num is None:
                raise LabelRowError(f"Image hash {frame} not found in the label row")
        else:
            frame_num = frame

        return self.FrameView(self, self._label_row_read_only_data, frame_num)

    def _get_frame_metadata_list(self) -> List[LabelRowReadOnlyDataImagesDataEntry]:
        if self._label_row_read_only_data.data_type in [DataType.IMAGE, DataType.VIDEO]:
            return [
                self.LabelRowReadOnlyDataImagesDataEntry(
                    index=0,
                    title=self._label_row_read_only_data.data_title,
                    file_type=self._label_row_read_only_data.file_type or "",
                    height=self._label_row_read_only_data.height or 0,
                    width=self._label_row_read_only_data.width or 0,
                    image_hash=self._label_row_read_only_data.data_hash,
                )
            ]

        images_data = self._label_row_read_only_data.images_data
        if images_data is None:
            raise LabelRowError("Image data is not present in the label row")
        return images_data

    def get_frame_metadata(self, frame: Union[int, str] = 0) -> FrameViewMetadata:
        """Get metadata for a specific frame or image hash.

        Args:
            frame: The frame number or the image hash. Defaults to the first frame.

        Returns:
            FrameViewMetadata: Metadata for the specified frame or image hash.

        Raises:
            LabelRowError: If the specified frame or image hash is not found in the label row.
        """
        self._method_not_supported_for_audio()

        images_data = self._get_frame_metadata_list()
        if isinstance(frame, str):
            data_meta = None
            for data in images_data:
                if data.image_hash == frame:
                    data_meta = data
                    break
            if data_meta is None:
                raise LabelRowError(f"Image hash {frame} not found in the label row")
        else:
            data_meta = None
            for data in images_data:
                if data.index == frame:
                    data_meta = data
                    break
            if data_meta is None:
                raise LabelRowError(f"Frame {frame} not found in the label row")

        return self.FrameViewMetadata(data_meta)

    def get_frames_metadata(self) -> List[FrameViewMetadata]:
        """Get metadata for all frames in the image group.

        Returns:
            List[FrameViewMetadata]: A list of metadata for each frame.
        """
        views = []

        images_data = self._get_frame_metadata_list()

        for data in images_data:
            views.append(self.FrameViewMetadata(data))
        return views

    def get_frame_views(self) -> List[FrameView]:
        """Get views for all frames.

        Returns:
            List[FrameView]: A list of frame views in order of available frames.
        """
        self._check_labelling_is_initalised()
        ret = []
        for frame in range(self.number_of_frames):
            ret.append(self.get_frame_view(frame))
        return ret

    def get_object_instances(
        self, filter_ontology_object: Optional[Object] = None, filter_frames: Optional[Frames] = None
    ) -> List[ObjectInstance]:
        """Get all object instances that match the given filters.

        Args:
            filter_ontology_object: Optionally filter by a specific ontology object.
            filter_frames: Optionally filter by specific frames.

        Returns:
            List[ObjectInstance]: A list of `ObjectInstance`s that match the filters.
        """
        self._check_labelling_is_initalised()

        return self._get_object_instances(
            include_spaces=True, filter_ontology_object=filter_ontology_object, filter_frames=filter_frames
        )

    def _get_object_instances(
        self,
        include_spaces: bool,
        filter_ontology_object: Optional[Object] = None,
        filter_frames: Optional[Frames] = None,
    ) -> List[ObjectInstance]:
        """
        Internal method for getting all object instances that match the given filters.
        Also allows filtering by spaces, which the public method does not yet support.
        """
        self._check_labelling_is_initalised()

        ret: List[ObjectInstance] = list()

        if filter_frames is not None:
            filtered_frames_list = frames_class_to_frames_list(filter_frames)
        else:
            filtered_frames_list = list()

        # Objects on label row
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

        # Objects in space
        if include_spaces:
            object_hashes: set[str] = (
                set()
            )  # Needed to filter out duplicate object instances that exist on multiple spaces
            for space in self._space_map.values():
                for object_ in space._objects_map.values():
                    if object_.object_hash in object_hashes:
                        continue

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
                        if isinstance(space, VideoSpace):
                            object_hash_map_on_frame = space._frames_to_object_hash_to_annotation_data.get(frame, {})
                            if object_.object_hash in object_hash_map_on_frame:
                                append = True
                                break
                        elif isinstance(space, ImageSpace):
                            if frame != 0:
                                continue
                            if object_.object_hash in space._objects_map:
                                append = True
                                break

                    if append:
                        object_hashes.add(object_.object_hash)
                        ret.append(object_)

        return ret

    def add_object_instance(self, object_instance: ObjectInstance, force: bool = True) -> None:
        """Add an object instance to the label row. If the object instance already exists, it overwrites the current instance.

        Args:
            object_instance: The object instance to add.
            force: If `True`, overwrites the current objects; otherwise, it will replace the current object.

        Raises:
            LabelRowError: If the object instance is already part of another LabelRowV2.
        """
        self._method_not_supported_for_audio(range_only=object_instance.is_range_only())

        self._check_labelling_is_initalised()

        if object_instance._is_assigned_to_space():
            raise LabelRowError(
                "Object instance already exists on a space. It cannot be placed directly onto the label row. Please use Space.place_object instead."
            )

        object_instance.is_valid()
        object_hash = object_instance.object_hash

        # We want to ensure that we are only adding the object_instance to a label_row
        # IF AND ONLY IF the file type is text/html and the object_instance has range_html set
        if self.file_type == "text/html" and object_instance.range_html is None:
            raise LabelRowError(
                "Unable to assign object instance without a html range to a html file. "
                f"Please ensure the object instance exists on frame=0, and has coordinates of type {HtmlCoordinates}."
            )
        elif self.file_type != "text/html" and object_instance.range_html is not None:
            raise LabelRowError(
                "Unable to assign object instance with a html range to a non-html file. "
                f"Please ensure the object instance does not have coordinates of type {HtmlCoordinates}."
            )

        if object_instance.is_assigned_to_label_row():
            raise LabelRowError(
                "The supplied ObjectInstance is already part of a LabelRowV2. You can only add a ObjectInstance to one "
                "LabelRowV2. You can do a ObjectInstance.copy() to create an identical ObjectInstance which is not part of "
                "any LabelRowV2."
            )

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
        """Add a classification instance to the label row.

        Args:
            classification_instance: The classification instance to add.
            force: If `True`, overwrites the current objects; otherwise, it will replace the current object.

        Raises:
            LabelRowError: If the classification instance is already part of another LabelRowV2 or has overlapping frames.
        """
        self._check_labelling_is_initalised()

        if classification_instance._is_assigned_to_space():
            raise LabelRowError(
                "Classification instance already exists on a space. It cannot be placed directly onto the label row. Please use Space.place_classification instead."
            )

        classification_instance.is_valid()
        classification_hash = classification_instance.classification_hash

        # TODO: Need to update the docstring for this method, talk to Laverne.
        if not classification_instance.is_range_only() and not is_geometric(self.data_type):
            raise LabelRowError(
                f"To add a ClassificationInstance object to a label row where data_type = {self.data_type},"
                "the ClassificationInstance object needs to be created with the "
                "range_only property set to True."
                "You can do ClassificationInstance(range_only=True) or "
                "Classification.create_instance(range_only=True) to achieve this."
            )
        elif classification_instance.is_assigned_to_label_row():
            raise LabelRowError(
                "Provided ClassificationInstance object is already attached to a different LabelRowV2 object. "
                "You can only add a ClassificationInstance to one label row. "
                "You can do a ClassificationInstance.copy() to create an identical ClassificationInstance which is not part of any label row."
            )
        elif classification_hash in self._classifications_map and not force:
            raise LabelRowError(
                f"A ClassificationInstance for classification hash '{classification_hash}' already exists on the label row object. "
                f"Pass 'force=True' to override it."
            )
        elif is_geometric(self.data_type) and not classification_instance.is_range_only():
            frames = set(_frame_views_to_frame_numbers(classification_instance.get_annotations()))
            is_present, already_present_ranges = self._is_classification_present_on_frames(
                classification_instance.ontology_item,
                frames,
            )

            if is_present and not force:
                location_msg = (
                    "globally"
                    if classification_instance.is_global()
                    else f"and has overlapping frames on the ranges {already_present_ranges}"
                )
                raise LabelRowError(
                    f"A ClassificationInstance '{classification_hash}' was already added {location_msg}."
                    f"Make sure that you only add classifications which are on frames where the same type of "
                    f"classification does not yet exist."
                )

            self._classifications_to_frames[classification_instance.ontology_item].update(frames)
            self._add_to_frame_to_hashes_map(classification_instance, frames)

        self._add_classification_instance_for_range(
            classification_instance=classification_instance,
            force=force,
        )
        self._classifications_map[classification_hash] = classification_instance

    def _add_classification_instance_for_range(
        self,
        classification_instance: ClassificationInstance,
        force: bool,
    ):
        classification_hash = classification_instance.classification_hash
        ranges_to_add = classification_instance.range_list

        is_present, already_present_ranges = self._is_classification_present_on_frames(
            classification_instance.ontology_item, ranges_to_add
        )

        if is_present and not force:
            location_msg = (
                "globally"
                if classification_instance.is_global()
                else f"and has overlapping frames on the ranges {already_present_ranges}"
            )
            raise LabelRowError(
                f"A ClassificationInstance '{classification_hash}' was already added {location_msg}."
                f"Make sure that you only add classifications which are on frames where the same type of "
                f"classification does not yet exist."
            )

        if force:
            # If it's a global classification, make sure to remove all other instances of the same ontology feature
            if classification_instance.is_global():
                for c_instance in list(self._classifications_map.values()):
                    if c_instance.feature_hash == classification_instance.feature_hash:
                        self._classifications_map.pop(c_instance.classification_hash)

        classification_instance._parent = self
        self._classifications_to_ranges[classification_instance.ontology_item].add_ranges(ranges_to_add)

    def remove_classification(self, classification_instance: ClassificationInstance):
        """Remove a classification instance from a label row.

        Args:
            classification_instance: The classification instance to remove.
        """
        self._check_labelling_is_initalised()

        if classification_instance._is_assigned_to_space():
            raise LabelRowError(
                "Classification instance already exists on a space. It cannot be removed directly from the label row. Please use Space.remove_classification instead."
            )

        classification_hash = classification_instance.classification_hash
        self._classifications_map.pop(classification_hash)

        range_manager = self._classifications_to_ranges[classification_instance.ontology_item]
        ranges_to_remove = classification_instance.range_list
        range_manager.remove_ranges(ranges_to_remove)

        if len(range_manager.ranges) == 0:
            del self._classifications_to_ranges[classification_instance.ontology_item]

        all_frames = self._classifications_to_frames[classification_instance.ontology_item]
        actual_frames = _frame_views_to_frame_numbers(classification_instance.get_annotations())
        for actual_frame in actual_frames:
            all_frames.remove(actual_frame)
        if len(all_frames) == 0:
            del self._classifications_to_frames[classification_instance.ontology_item]

        # The instance no longer has a parent
        classification_instance._parent = None

    def add_to_single_frame_to_hashes_map(
        self, label_item: Union[ObjectInstance, ClassificationInstance], frame: int
    ) -> None:
        # This is an internal function, it is not meant to be called by the SDK user.
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
        """Get all classification instances that match the given filters.

        Args:
            filter_ontology_classification: Optionally filter by a specific ontology classification.
            filter_frames: Optionally filter by specific frames.

        Returns:
            List[ClassificationInstance]: All the `ClassificationInstance`s that match the filter.
        """
        self._check_labelling_is_initalised()

        return self._get_classification_instances(
            include_spaces=True,
            filter_ontology_classification=filter_ontology_classification,
            filter_frames=filter_frames,
        )

    def _get_classification_instances(
        self,
        include_spaces: bool,
        filter_ontology_classification: Optional[Classification] = None,
        filter_frames: Optional[Frames] = None,
    ) -> List[ClassificationInstance]:
        """
        Internal method for getting classification instances. Can choose whether to include classification instances on spaces in this.
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

            if classification.is_on_frame(filtered_frames_list):
                append = True

            if append:
                ret.append(classification)

        if include_spaces:
            # Needed to remove filter out duplicate classification instances across spaces
            classification_hashes: set[str] = set()
            for space in self._space_map.values():
                for classification in space.get_classifications():
                    if classification.classification_hash in classification_hashes:
                        continue

                    if not (
                        filter_ontology_classification is None
                        or classification.ontology_item.feature_node_hash
                        == filter_ontology_classification.feature_node_hash
                    ):
                        continue

                    # filter by frame
                    if filter_frames is None:
                        append = True
                    else:
                        append = False

                    for frame in filtered_frames_list:
                        if isinstance(space, VideoSpace):
                            # TODO: In VideoSpace, track classificationHash to ranges to improve performance here.
                            classifications_on_frames = space._frames_to_classification_hash_to_annotation_data.get(
                                frame, {}
                            )
                            if classification.classification_hash in classifications_on_frames:
                                append = True
                                break
                        elif isinstance(space, ImageSpace):
                            if frame != 0:
                                continue

                            if classification.classification_hash in space._classifications_map:
                                append = True
                                break

                    if append:
                        classification_hashes.add(classification.classification_hash)
                        ret.append(classification)

        return ret

    def remove_object(self, object_instance: ObjectInstance):
        """Remove an object instance from a label row.

        Args:
            object_instance: The object instance to remove.
        """
        self._check_labelling_is_initalised()

        if object_instance._is_assigned_to_space():
            raise LabelRowError(
                "Object instance already exists on a space. It cannot be removed directly from the label row. Please use Space.remove_object instead."
            )

        self._objects_map.pop(object_instance.object_hash, None)

        if not object_instance.is_range_only():
            self._remove_from_frame_to_hashes_map(
                _frame_views_to_frame_numbers(object_instance.get_annotations()), object_instance.object_hash
            )
        object_instance._parent = None

    def to_encord_dict(self) -> Dict[str, Any]:
        """Convert the label row to a dictionary in Encord format.

        This is an internal helper function. Likely this should not be used by a user. To upload labels use the
        :meth:`encord.objects.ontology_labels_impl.LabelRowV2.save` function.

        Returns:
            Dict[str, Any]: A dictionary representing the label row in Encord format.
        """
        self._check_labelling_is_initalised()

        ret: Dict[str, Any] = {}
        read_only_data = self._label_row_read_only_data

        ret["label_hash"] = read_only_data.label_hash
        ret["branch_name"] = read_only_data.branch_name
        ret["created_at"] = format_datetime_to_long_string_optional(read_only_data.created_at)
        ret["last_edited_at"] = format_datetime_to_long_string_optional(read_only_data.last_edited_at)
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
        ret["spaces"] = self._to_encord_spaces()

        return ret

    def workflow_reopen(self, bundle: Optional[Bundle] = None) -> None:
        """Return a label row to the first annotation stage for re-labeling.

        No data will be lost during this call. This method is only relevant for the projects that use the
        :ref:`Workflow <tutorials/workflows:Workflows>` feature, and will raise an error for pre-workflow projects.

        Args:
            bundle: Optional parameter. If passed, the method will be executed in a deferred way as part of the bundle.
        """
        if self.label_hash is None:
            # Label has not yet moved from the initial state, nothing to do
            return

        bundled_operation(
            bundle,
            self._project_client.workflow_reopen,
            payload=BundledWorkflowReopenPayload(label_hashes=[self.label_hash]),
        )

    def workflow_complete(self, bundle: Optional[Bundle] = None) -> None:
        """Move a label row to the final workflow node, marking it as 'Complete'.

        This method can be called only for labels for which :meth:`encord.objects.ontology_labels_impl.LabelRowV2.initialise_labels` was called at least once, and
        consequentially the "label_hash" field is not `None`. Labels need not be initialized every time the
        workflow_complete() method is called.

        This method is only relevant for the projects that use the :ref:`Workflow <tutorials/workflows:Workflows>`
        feature, and raises an error for projects that do not use Workflows.

        Args:
            bundle: Optional parameter. If passed, the method will be executed in a deferred way as part of the bundle.

        Raises:
            LabelRowError: If the label hash is None.
        """
        if self.label_hash is None:
            raise LabelRowError(
                "For this operation you need to initialize labelling first. Call the .initialise_labels() "
                "to do so first."
            )

        bundled_operation(
            bundle,
            self._project_client.workflow_complete,
            payload=BundledWorkflowCompletePayload(label_hashes=[self.label_hash]),
        )

    def set_priority(self, priority: float, bundle: Optional[Bundle] = None) -> None:
        """Set priority for a task in a workflow project.

        Args:
            priority: Float value from 0.0 to 1.0, where 1.0 is the highest priority.
            bundle: Optional parameter. If passed, the method will be executed in a deferred way as part of the bundle.

        Raises:
            WrongProjectTypeError: If the project is not a workflow-based project.
        """
        if not self.__is_tms2_project:
            raise WrongProjectTypeError("Setting priority only possible for workflow-based projects")

        bundled_operation(
            bundle,
            self._project_client.workflow_set_priority,
            payload=BundledSetPriorityPayload(priorities=[(self.data_hash, priority)]),
        )

    def get_validation_errors(self) -> Optional[List[str]]:
        """Get validation errors for the label row.

        Returns:
            List[str] | None: A list of error messages if the label row is invalid, otherwise `None`.
        """
        if not self.label_hash or self.is_valid:
            return None

        return self._project_client.get_label_validation_errors(self.label_hash)

    class FrameViewMetadata:
        """Class to inspect metadata for a frame view."""

        def __init__(self, images_data: LabelRowV2.LabelRowReadOnlyDataImagesDataEntry):
            self._image_data = images_data

        @property
        def title(self) -> str:
            return self._image_data.title

        @property
        def file_type(self) -> str:
            return self._image_data.file_type

        @property
        def width(self) -> int:
            return self._image_data.width

        @property
        def height(self) -> int:
            return self._image_data.height

        @property
        def image_hash(self) -> str:
            return self._image_data.image_hash

        @property
        def frame_number(self) -> int:
            return self._image_data.index

    class FrameView:
        """This class can be used to inspect object or classification instances on a given frame,
        or metadata such as image file size for a given frame.
        """

        def __init__(
            self, label_row: LabelRowV2, label_row_read_only_data: LabelRowV2.LabelRowReadOnlyData, frame: int
        ):
            self._label_row = label_row
            self._label_row_read_only_data = label_row_read_only_data
            self._frame = frame

        @property
        def image_hash(self) -> str:
            """Get the image hash for the current frame.

            Returns:
                str: The image hash.

            Raises:
                LabelRowError: If the data type is not IMAGE or IMG_GROUP.
            """
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("Image hash can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().image_hash

        @property
        def image_title(self) -> str:
            """Get the image title for the current frame.

            Returns:
                str: The image title.

            Raises:
                LabelRowError: If the data type is not IMAGE or IMG_GROUP.
            """
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("Image title can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().image_title

        @property
        def file_type(self) -> str:
            """Get the file type for the current frame.

            Returns:
                str: The file type.

            Raises:
                LabelRowError: If the data type is not IMAGE or IMG_GROUP.
            """
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("File type can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().file_type

        @property
        def frame(self) -> int:
            """Get the frame number.

            Returns:
                int: The frame number.
            """
            return self._frame

        @property
        def width(self) -> int:
            """Get the width of the frame.

            Raises:
                LabelRowError: If the width is not set for the data type.
            """
            if self._label_row.data_type == DataType.IMG_GROUP:
                return self._frame_level_data().width
            elif self._label_row.data_type == DataType.DICOM:
                frame_metadata = self._label_row._frame_metadata[self._frame]
                if frame_metadata is not None:
                    return frame_metadata.width
                elif self._label_row_read_only_data.width is not None:
                    return self._label_row_read_only_data.width
                else:
                    raise LabelRowError(f"Width is expected but not set for the data type {self._label_row.data_type}")
            elif self._label_row_read_only_data.width is not None:
                return self._label_row_read_only_data.width
            else:
                raise LabelRowError(f"Width is expected but not set for the data type {self._label_row.data_type}")

        @property
        def height(self) -> int:
            """Get the height of the frame.

            Raises:
                LabelRowError: If the height is not set for the data type.
            """
            if self._label_row.data_type == DataType.IMG_GROUP:
                return self._frame_level_data().height
            elif self._label_row.data_type == DataType.DICOM:
                frame_metadata = self._label_row._frame_metadata[self._frame]
                if frame_metadata is not None:
                    return frame_metadata.height
                elif self._label_row_read_only_data.height is not None:
                    return self._label_row_read_only_data.height
                else:
                    raise LabelRowError(f"Height is expected but not set for the data type {self._label_row.data_type}")
            elif self._label_row_read_only_data.height is not None:
                return self._label_row_read_only_data.height
            else:
                raise LabelRowError(f"Height is expected but not set for the data type {self._label_row.data_type}")

        @property
        def data_link(self) -> Optional[str]:
            """Get the data link for the current frame.

            Returns:
                Optional[str]: The data link, or `None` if not available.

            Raises:
                LabelRowError: If the data type is not IMAGE or IMG_GROUP.
            """
            if self._label_row.data_type not in [DataType.IMAGE, DataType.IMG_GROUP]:
                raise LabelRowError("Data link can only be retrieved for DataType.IMAGE or DataType.IMG_GROUP")
            return self._frame_level_data().data_link

        @property
        def metadata(self) -> Optional[DICOMSliceMetadata]:
            """Get annotation metadata for the current frame.

            Returns:
                Optional[DICOMSliceMetadata]: The metadata for the frame, or `None` if not applicable.

            Note:
                Currently only supported for DICOM, and will return `None` for other formats.
            """
            return self._label_row._frame_metadata[self._frame]

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
            """Add an object instance to the current frame.

            Args:
                object_instance: The object instance to add.
                coordinates: The coordinates for the object instance.
                overwrite: Whether to overwrite existing instance data (default is False).
                created_at: Optional creation timestamp.
                created_by: Optional creator identifier.
                last_edited_at: Optional last edited timestamp.
                last_edited_by: Optional last editor identifier.
                confidence: Optional confidence score.
                manual_annotation: Optional flag indicating manual annotation.

            Raises:
                LabelRowError: If the object instance is already assigned to a different label row.
            """
            label_row = object_instance.is_assigned_to_label_row()
            if label_row and self._label_row != label_row:
                raise LabelRowError(
                    "This object instance is already assigned to a different label row. It cannot be "
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
            """Add a classification instance to the current frame.

            Args:
                classification_instance: The classification instance to add.
                overwrite: Whether to overwrite existing instance data (default is False).
                created_at: Optional creation timestamp.
                created_by: Optional creator identifier.
                confidence: Confidence score (default is DEFAULT_CONFIDENCE).
                manual_annotation: Flag indicating manual annotation (default is DEFAULT_MANUAL_ANNOTATION).
                last_edited_at: Optional last edited timestamp.
                last_edited_by: Optional last editor identifier.

            Raises:
                LabelRowError: If the classification instance is already assigned to a different label row.
            """
            if created_at is None:
                created_at = datetime.now()

            if last_edited_at is None:
                last_edited_at = datetime.now()

            label_row = classification_instance.is_assigned_to_label_row()
            if label_row and self._label_row != label_row:
                raise LabelRowError(
                    "This classification instance is already assigned to a different label row. It cannot be "
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
            """Get object instances for the current frame.

            Args:
                filter_ontology_object: Optionally filter by a specific ontology object.

            Returns:
                List[ObjectInstance]: All `ObjectInstance`s that match the filter.
            """
            return self._label_row.get_object_instances(
                filter_ontology_object=filter_ontology_object, filter_frames=self._frame
            )

        def get_classification_instances(
            self, filter_ontology_classification: Optional[Classification] = None
        ) -> List[ClassificationInstance]:
            """Get classification instances for the current frame.

            Args:
                filter_ontology_classification: Optionally filter by a specific ontology classification.

            Returns:
                List[ClassificationInstance]: All `ClassificationInstance`s that match the filter.
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
        """Data related to a specific frame in an image group.

        Attributes:
            image_hash: Hash of the image.
            image_title: Title of the image.
            file_type: Type of the file (e.g., JPEG, PNG).
            frame_number: The number of the frame in the sequence.
            width: Width of the image.
            height: Height of the image.
            data_link: Optional link to additional data related to the image.
        """

        image_hash: str
        image_title: str
        file_type: str
        frame_number: int
        width: int
        height: int
        data_link: Optional[str] = None

    @dataclass(frozen=True)
    class LabelRowReadOnlyDataImagesDataEntry:
        """Read-only data entry for image data in a label row.

        Attributes:
            index: Index of the image.
            title: Title of the image.
            file_type: Type of the file (e.g., JPEG, PNG).
            height: Height of the image.
            width: Width of the image.
            image_hash: Hash of the image.
        """

        index: int
        title: str
        file_type: str
        height: int
        width: int
        image_hash: str

    @dataclass(frozen=True)
    class LabelRowReadOnlyData:
        """Read-only data for a label row.

        Attributes:
            label_hash: Optional hash for the label. `None` if not initialized for labeling.
            created_at: Optional creation timestamp. `None` if not initialized for labeling.
            last_edited_at: Optional last edited timestamp. `None` if not initialized for labeling.
            data_hash: Hash of the data.
            data_type: Type of the data (e.g., IMAGE, VIDEO).
            label_status: Status of the label.
            annotation_task_status: Optional status of the annotation task.
            workflow_graph_node: Optional workflow graph node related to the data.
            is_shadow_data: Boolean indicating if the data is shadow data.
            number_of_frames: Number of frames in the data.
            duration: Optional duration of the video or sequence.
            fps: Optional frames per second for video.
            dataset_hash: Hash of the dataset.
            dataset_title: Title of the dataset.
            data_title: Title of the data.
            audio_codec: Codec for audio data.
            audio_bit_depth: Bit depth for audio data.
            audio_sample_rate: Sample Rate for audio data.
            audio_num_channels: Number of channels for audio data.
            width: Optional width of the data.
            height: Optional height of the data.
            data_link: Optional link to additional data.
            task_uuid: Optional task uuid of the data.
            priority: Optional priority of the data.
            file_type: Optional file type of the data.
            client_metadata: Optional metadata provided by the client.
            images_data: Optional list of image data entries.
            branch_name: Name of the branch associated with the data.
            frame_level_data: Mapping from frame number to frame level data.
            image_hash_to_frame: Mapping from image hash to frame number.
            frame_to_image_hash: Mapping from frame number to image hash.
            is_valid: Boolean indicating if the data is valid.
            assigned_user_email: Optional email of the user assigned to the data.
            last_actioned_by_user_email: Optional email of the user who last actioned the data.
        """

        label_hash: Optional[str]
        created_at: Optional[datetime]
        last_edited_at: Optional[datetime]
        data_hash: str
        group_hash: Optional[str]
        data_type: DataType
        backing_item_uuid: Optional[UUID]
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
        audio_codec: Optional[str]
        audio_bit_depth: Optional[int]
        audio_num_channels: Optional[int]
        audio_sample_rate: Optional[int]
        width: Optional[int]
        height: Optional[int]
        data_link: Optional[str]
        task_uuid: Optional[UUID]
        priority: Optional[float]
        file_type: Optional[str]
        client_metadata: Optional[Dict[str, Any]]
        images_data: Optional[List[LabelRowV2.LabelRowReadOnlyDataImagesDataEntry]]
        branch_name: str
        frame_level_data: Dict[int, LabelRowV2.FrameLevelImageGroupData] = field(default_factory=dict)
        image_hash_to_frame: Dict[str, int] = field(default_factory=dict)
        frame_to_image_hash: Dict[int, str] = field(default_factory=dict)
        is_valid: bool = field(default=True)
        assigned_user_email: Optional[str] = None
        last_actioned_by_user_email: Optional[str] = None

    def _to_object_answers(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        for obj in self._objects_map.values():
            all_static_answers = self._get_all_static_answers(obj)
            ret[obj.object_hash] = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }

            # At some point, we also want to add these to the other modalities
            if not is_geometric(self.data_type):
                # For non-frame entities, all annotations exist only on one frame
                annotation = obj.get_annotation(0)
                object_answer_dict = ret[obj.object_hash]
                object_answer_dict["createdBy"] = annotation.created_by
                object_answer_dict["createdAt"] = format_datetime_to_long_string_optional(annotation.created_at)
                object_answer_dict["lastEditedBy"] = annotation.last_edited_by
                object_answer_dict["lastEditedAt"] = format_datetime_to_long_string_optional(annotation.last_edited_at)
                object_answer_dict["manualAnnotation"] = annotation.manual_annotation
                object_answer_dict["featureHash"] = obj.feature_hash
                object_answer_dict["name"] = obj.ontology_item.name
                object_answer_dict["color"] = obj.ontology_item.color
                object_answer_dict["shape"] = obj.ontology_item.shape.value
                object_answer_dict["value"] = _lower_snake_case(obj.ontology_item.name)

                if self.file_type == "text/html":
                    if obj.range_html is None:
                        raise LabelRowError("Html annotations should have range_html set within the TextCoordinates")
                    object_answer_dict["range_html"] = [x.to_dict() for x in obj.range_html]
                    object_answer_dict["range"] = []
                else:
                    if obj.range_list is None:
                        raise LabelRowError("Non-geometric annotations should have range set within the Coordinates")
                    object_answer_dict["range"] = [[range.start, range.end] for range in obj.range_list]

        for space in self._space_map.values():
            space_object_answers = space._to_object_answers()
            ret.update(space_object_answers)

        return ret

    def _to_object_actions(self) -> Dict[str, ObjectAction]:
        ret: Dict[str, Any] = {}
        for obj in self._objects_map.values():
            all_static_answers = self._dynamic_answers_to_encord_dict(obj)
            if len(all_static_answers) == 0:
                continue
            ret[obj.object_hash] = {
                "actions": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }

        for space in self._space_map.values():
            for obj in space._objects_map.values():
                # Currently, dynamic attributes only available for VideoSpace
                if isinstance(space, VideoSpace):
                    all_static_answers = space._dynamic_answers_to_encord_dict(obj)
                    if len(all_static_answers) == 0:
                        continue

                    if obj.object_hash in ret:
                        ret[obj.object_hash]["actions"].extend(list(all_static_answers))
                    else:
                        ret[obj.object_hash] = {
                            "actions": list(all_static_answers),
                            "objectHash": obj.object_hash,
                        }
        return ret

    def _to_classification_answers(self) -> Dict[str, ClassificationAnswer]:
        ret: Dict[str, ClassificationAnswer] = {}
        for classification in self._classifications_map.values():
            all_static_answers = classification.get_all_static_answers()
            classifications = [answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()]
            answered_classifications = cast(List[AttributeDict], classifications)
            ret[classification.classification_hash] = {
                "classifications": list(reversed(answered_classifications)),
                "classificationHash": classification.classification_hash,
                "featureHash": classification.feature_hash,
            }

            # If the classification includes instance data
            if classification._include_instance_data:
                ret[classification.classification_hash]["range"] = ranges_to_list(classification.range_list)
                ret[classification.classification_hash]["createdBy"] = classification.created_by
                ret[classification.classification_hash]["createdAt"] = format_datetime_to_long_string_optional(
                    classification.created_at
                )
                ret[classification.classification_hash]["lastEditedBy"] = classification.last_edited_by
                ret[classification.classification_hash]["lastEditedAt"] = format_datetime_to_long_string_optional(
                    classification.last_edited_at
                )
                ret[classification.classification_hash]["manualAnnotation"] = classification.manual_annotation

        for space in self._space_map.values():
            space_classification_answers = space._to_classification_answers()
            ret.update(space_classification_answers)

        return ret

    @staticmethod
    def _get_all_static_answers(object_instance: ObjectInstance) -> List[AttributeDict]:
        ret = []
        for answer in object_instance._get_all_static_answers():
            d_opt = answer.to_encord_dict()
            if d_opt is not None:
                ret.append(d_opt)
        return ret

    @staticmethod
    def _dynamic_answers_to_encord_dict(object_instance: ObjectInstance) -> List[DynamicAttributeObject]:
        ret: List[DynamicAttributeObject] = []
        for answer, ranges in object_instance._get_all_dynamic_answers():
            d_opt = answer.to_encord_dict(ranges)
            if d_opt is not None:
                ret.append(cast(DynamicAttributeObject, d_opt))

        return ret

    def _to_encord_spaces(self) -> Dict[str, SpaceInfo]:
        ret = {}
        for space_id, space in self._space_map.items():
            ret[space_id] = space._to_space_dict()

        return ret

    def _to_encord_data_units(self) -> Dict[str, Any]:
        frame_level_data = self._label_row_read_only_data.frame_level_data
        return {value.image_hash: self._to_encord_data_unit(value) for value in frame_level_data.values()}

    def _to_encord_data_unit(self, frame_level_data: FrameLevelImageGroupData) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}

        data_type = self._label_row_read_only_data.data_type

        if data_type == DataType.IMG_GROUP:
            data_sequence: Union[str, int] = str(frame_level_data.frame_number)

        elif (
            data_type == DataType.VIDEO
            or data_type == DataType.DICOM
            or data_type == DataType.IMAGE
            or data_type == DataType.NIFTI
            or data_type == DataType.PDF
            or data_type == DataType.SCENE
        ):
            data_sequence = frame_level_data.frame_number

        elif data_type == DataType.AUDIO or data_type == DataType.PLAIN_TEXT:
            data_sequence = 0

        elif data_type == DataType.DICOM_STUDY:
            pass
        elif data_type == DataType.GROUP:
            data_sequence = 0

        elif data_type == DataType.MISSING_DATA_TYPE:
            raise NotImplementedError(f"The data type {data_type} is not implemented yet.")

        else:
            exhaustive_guard(data_type)

        ret["data_hash"] = frame_level_data.image_hash
        ret["data_title"] = frame_level_data.image_title

        if data_type != DataType.DICOM and data_type != DataType.GROUP:
            ret["data_link"] = frame_level_data.data_link

        ret["data_type"] = frame_level_data.file_type
        ret["data_sequence"] = data_sequence

        if self.data_type == DataType.AUDIO:
            ret["audio_codec"] = self._label_row_read_only_data.audio_codec
            ret["audio_sample_rate"] = self._label_row_read_only_data.audio_sample_rate
            ret["audio_bit_depth"] = self._label_row_read_only_data.audio_bit_depth
            ret["audio_num_channels"] = self._label_row_read_only_data.audio_num_channels
        elif self.data_type == DataType.PLAIN_TEXT:
            pass
        elif self.data_type == DataType.GROUP:
            pass
            # ret["width"] = 0
            # ret["height"] = 0
            # ret["data_link"] = ""
        elif self.data_type == DataType.SCENE:
            ret["width"] = 0
            ret["height"] = 0
            ret["data_link"] = ""
            ret["data_fps"] = 0
        elif self.data_type == DataType.PDF:
            ret["height"] = 0
            ret["width"] = 0
            ret["data_fps"] = 0
        elif (
            self.data_type == DataType.IMAGE
            or self.data_type == DataType.NIFTI
            or self.data_type == DataType.VIDEO
            or self.data_type == DataType.IMG_GROUP
            or self.data_type == DataType.DICOM
            or self.data_type == DataType.DICOM_STUDY
        ):
            ret["width"] = frame_level_data.width
            ret["height"] = frame_level_data.height
        elif self.data_type == DataType.MISSING_DATA_TYPE:
            raise LabelRowError("Label row is missing data type.")
        else:
            exhaustive_guard(self.data_type)

        ret["labels"] = self._to_encord_labels(frame_level_data)

        if (
            self._label_row_read_only_data.duration is not None
            and self.data_type != DataType.PLAIN_TEXT
            and self.data_type != DataType.GROUP
        ):
            ret["data_duration"] = self._label_row_read_only_data.duration

        if (
            self._label_row_read_only_data.fps is not None
            and self.data_type != DataType.AUDIO
            and self.data_type != DataType.PLAIN_TEXT
            and self.data_type != DataType.GROUP
        ):
            ret["data_fps"] = self._label_row_read_only_data.fps

        return ret

    def _to_encord_labels(self, frame_level_data: FrameLevelImageGroupData) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        data_type = self._label_row_read_only_data.data_type

        if data_type == DataType.IMAGE or data_type == DataType.IMG_GROUP or data_type == DataType.GROUP:
            # single frame
            frame = frame_level_data.frame_number
            ret.update(self._to_encord_label(frame))

        elif (
            # multi-frame
            data_type == DataType.VIDEO
            or data_type == DataType.DICOM
            or data_type == DataType.NIFTI
            or data_type == DataType.PDF
            or data_type == DataType.SCENE
        ):
            for frame in self._frame_to_hashes.keys():
                ret[str(frame)] = self._to_encord_label(frame)

        elif data_type == DataType.AUDIO or data_type == DataType.PLAIN_TEXT:
            return {}

        elif data_type == DataType.DICOM_STUDY:
            pass

        elif data_type == DataType.MISSING_DATA_TYPE:
            raise NotImplementedError(f"The data type {data_type} is not implemented yet.")

        else:
            exhaustive_guard(data_type)

        return ret

    def _to_encord_label(self, frame: int) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}

        ret["objects"] = self._to_encord_objects_list(frame)
        ret["classifications"] = self._to_encord_classifications_list(frame)

        return ret

    def _to_encord_objects_list(self, frame: int) -> List:
        # Get objects for frame
        ret: List[dict] = []

        # Spaces are excluded here, because we export them in their own spaces dict.
        objects = self._get_object_instances(include_spaces=False, filter_frames=frame)
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
        ret["createdAt"] = format_datetime_to_long_string_optional(object_instance_annotation.created_at)
        ret["createdBy"] = object_instance_annotation.created_by
        ret["confidence"] = object_instance_annotation.confidence
        ret["objectHash"] = object_.object_hash
        ret["featureHash"] = ontology_object.feature_node_hash
        ret["manualAnnotation"] = object_instance_annotation.manual_annotation

        if object_instance_annotation.last_edited_at is not None:
            ret["lastEditedAt"] = format_datetime_to_long_string_optional(object_instance_annotation.last_edited_at)
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
            encord_object["polygons"] = coordinates.to_dict(PolygonCoordsToDict.multiple_polygons)
        elif isinstance(coordinates, PolylineCoordinates):
            encord_object["polyline"] = coordinates.to_dict()
        elif isinstance(coordinates, (PointCoordinate, PointCoordinate3D)):
            encord_object["point"] = coordinates.to_dict()
        elif isinstance(coordinates, BitmaskCoordinates):
            frame_view = self.get_frame_view(frame)
            if not (
                frame_view.height == coordinates._encoded_bitmask.height
                and frame_view.width == coordinates._encoded_bitmask.width
            ):
                raise ValueError("Bitmask dimensions don't match the media dimensions")
            encord_object["bitmask"] = coordinates.to_dict()
        elif isinstance(coordinates, SkeletonCoordinates):
            encord_object["skeleton"] = coordinates.to_dict()
        elif isinstance(coordinates, CuboidCoordinates):
            encord_object["cuboid"] = coordinates.to_dict()
        else:
            raise NotImplementedError(f"adding coordinatees for this type not yet implemented {type(coordinates)}")

    def _to_encord_classifications_list(self, frame: int) -> List:
        ret: List[Dict[str, Any]] = []

        classifications = self._get_classification_instances(include_spaces=False, filter_frames=frame)
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
        ret["createdAt"] = format_datetime_to_long_string_optional(annotation.created_at)
        ret["createdBy"] = annotation.created_by
        ret["confidence"] = annotation.confidence
        ret["featureHash"] = ontology_classification.feature_node_hash
        ret["classificationHash"] = classification.classification_hash
        ret["manualAnnotation"] = annotation.manual_annotation

        if annotation.last_edited_at is not None:
            ret["lastEditedAt"] = format_datetime_to_long_string_optional(annotation.last_edited_at)
        if annotation.last_edited_by is not None:
            ret["lastEditedBy"] = annotation.last_edited_by

        return ret

    def _is_classification_present_on_frames(
        self, classification: Classification, frames: Frames
    ) -> Tuple[bool, Ranges]:
        if classification.is_global and classification in self._classifications_to_ranges:
            return True, []
        else:
            range_manager = self._classifications_to_ranges.get(classification, RangeManager())
            intersection = range_manager.intersection(frames)
            return len(intersection) > 0, intersection

    def _add_frames_to_classification(self, classification_instance: ClassificationInstance, frames: Frames) -> None:
        classification = classification_instance.ontology_item

        range_manager = RangeManager(frame_class=frames)
        frames_set = range_manager.get_ranges_as_frames()

        self._classifications_to_ranges[classification].add_ranges(range_manager.get_ranges())

        if not classification_instance.is_range_only():
            self._classifications_to_frames[classification].update(frames_set)
            for frame in frames_set:
                self.add_to_single_frame_to_hashes_map(classification_instance, frame)

    def _remove_frames_from_classification(
        self, classification_instance: ClassificationInstance, frames: Frames
    ) -> None:
        classification = classification_instance.ontology_item

        range_manager = RangeManager(frame_class=frames)

        self._classifications_to_ranges[classification].remove_ranges(range_manager.get_ranges())

        if not classification_instance.is_range_only():
            present_frames = self._classifications_to_frames.get(classification, set())

            frames_set = range_manager.get_ranges_as_frames()
            for frame in frames_set:
                present_frames.remove(frame)
                self._frame_to_hashes[frame].remove(classification_instance.classification_hash)

    def _add_to_frame_to_hashes_map(
        self, label_item: Union[ObjectInstance, ClassificationInstance], frames: Iterable[int]
    ) -> None:
        for frame in frames:
            self.add_to_single_frame_to_hashes_map(label_item, frame)

    @deprecated("Only used in the ObjectInstance removal")
    def _remove_from_frame_to_hashes_map(self, frames: Iterable[int], item_hash: str):
        for frame in frames:
            self._frame_to_hashes[frame].remove(item_hash)

    def _initiate_spaces(
        self,
        spaces_info: Optional[dict[str, SpaceInfo]],
    ) -> dict[str, Space]:
        res: dict[str, Space] = dict()

        if spaces_info is None:
            return res

        for space_id, space_info in spaces_info.items():
            if space_info["space_type"] == SpaceType.VIDEO:
                video_space = VideoSpace(
                    space_id=space_id,
                    label_row=self,
                    child_info=space_info["info"],
                    number_of_frames=space_info["number_of_frames"],
                    width=space_info["width"],
                    height=space_info["height"],
                )
                # test_video_space._parse_space_dict(
                #     space_info, object_answers=object_answers, classification_answers=classification_answers
                # )
                res[space_id] = video_space
            elif space_info["space_type"] == SpaceType.IMAGE:
                image_space = ImageSpace(
                    space_id=space_id,
                    label_row=self,
                    child_info=space_info["info"],
                    width=space_info["width"],
                    height=space_info["height"],
                )
                # test_image_space._parse_space_dict(
                #     space_info, object_answers=object_answers, classification_answers=classification_answers
                # )
                res[space_id] = image_space

        return res

    def _parse_space_labels(
        self,
        spaces_info: dict[str, SpaceInfo],
        object_answers: dict,
        classification_answers: dict,
    ) -> None:
        res: dict[str, Space] = dict()

        for space_id, space_info in spaces_info.items():
            if space_info["space_type"] == SpaceType.VIDEO:
                video_space = self.get_space(id=space_id, type_="video")
                video_space._parse_space_dict(
                    space_info, object_answers=object_answers, classification_answers=classification_answers
                )
                res[space_id] = video_space
            elif space_info["space_type"] == SpaceType.IMAGE:
                image_space = self.get_space(id=space_id, type_="image")
                image_space._parse_space_dict(
                    space_info, object_answers=object_answers, classification_answers=classification_answers
                )
                res[space_id] = image_space

    def _parse_label_row_metadata(self, label_row_metadata: LabelRowMetadata) -> LabelRowV2.LabelRowReadOnlyData:
        data_type = DataType.from_upper_case_string(label_row_metadata.data_type)

        return LabelRowV2.LabelRowReadOnlyData(
            label_hash=label_row_metadata.label_hash,
            branch_name=label_row_metadata.branch_name,
            data_hash=label_row_metadata.data_hash,
            group_hash=label_row_metadata.group_hash,
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
            audio_codec=label_row_metadata.audio_codec,
            audio_sample_rate=label_row_metadata.audio_sample_rate,
            audio_num_channels=label_row_metadata.audio_num_channels,
            audio_bit_depth=label_row_metadata.audio_bit_depth,
            width=label_row_metadata.width,
            height=label_row_metadata.height,
            task_uuid=label_row_metadata.task_uuid,
            priority=label_row_metadata.priority,
            images_data=None
            if label_row_metadata.images_data is None
            else [LabelRowV2.LabelRowReadOnlyDataImagesDataEntry(**data) for data in label_row_metadata.images_data],
            client_metadata=label_row_metadata.client_metadata,
            file_type=label_row_metadata.file_type,
            is_valid=label_row_metadata.is_valid,
            backing_item_uuid=label_row_metadata.backing_item_uuid,
            assigned_user_email=label_row_metadata.assigned_user_email,
            last_actioned_by_user_email=label_row_metadata.last_actioned_by_user_email,
        )

    def _parse_label_row_dict(self, label_row_dict: dict) -> LabelRowReadOnlyData:
        frame_level_data = self._parse_image_group_frame_level_data(label_row_dict["data_units"])
        image_hash_to_frame = {item.image_hash: item.frame_number for item in frame_level_data.values()}
        frame_to_image_hash = {item.frame_number: item.image_hash for item in frame_level_data.values()}
        data_type = DataType(label_row_dict["data_type"])

        audio_codec = None
        audio_sample_rate = None
        audio_num_channels = None
        audio_bit_depth = None

        if data_type == DataType.VIDEO or data_type == DataType.IMAGE:
            data_dict = list(label_row_dict["data_units"].values())[0]
            data_link = data_dict["data_link"]
            file_type = data_dict.get("data_type")
            # Dimensions should be always there
            # But we have some older entries that don't have them
            # So setting them to None for now until the format is not guaranteed to be enforced
            height = data_dict.get("height")
            width = data_dict.get("width")

        elif data_type == DataType.GROUP or data_type == DataType.SCENE:
            data_dict = list(label_row_dict["data_units"].values())[0]
            file_type = data_dict.get("data_type")
            data_link = None
            width = None
            height = None

        elif data_type == DataType.DICOM or data_type == DataType.NIFTI:
            dicom_dict = list(label_row_dict["data_units"].values())[0]
            data_link = None
            file_type = dicom_dict["data_type"]

            height = dicom_dict["height"]
            width = dicom_dict["width"]

        elif data_type == DataType.AUDIO:
            data_dict = list(label_row_dict["data_units"].values())[0]
            data_link = data_dict["data_link"]
            file_type = data_dict.get("data_type")
            height = None
            width = None
            audio_codec = data_dict["audio_codec"]
            audio_sample_rate = data_dict["audio_sample_rate"]
            audio_num_channels = data_dict["audio_num_channels"]
            audio_bit_depth = data_dict["audio_bit_depth"]

        elif data_type == DataType.PLAIN_TEXT:
            data_dict = list(label_row_dict["data_units"].values())[0]
            data_link = data_dict["data_link"]
            file_type = data_dict.get("data_type")
            height = None
            width = None

        elif data_type == DataType.IMG_GROUP:
            data_link = None
            file_type = None
            height = None
            width = None

        elif data_type == DataType.DICOM_STUDY:
            pass

        elif data_type == DataType.PLAIN_TEXT or data_type == DataType.PDF:
            data_dict = list(label_row_dict["data_units"].values())[0]
            data_link = data_dict["data_link"]
            file_type = data_dict.get("data_type")
            height = None
            width = None

        elif data_type == DataType.MISSING_DATA_TYPE:
            raise NotImplementedError(f"The data type {data_type} is not implemented yet.")

        else:
            exhaustive_guard(data_type)

        return LabelRowV2.LabelRowReadOnlyData(
            label_hash=label_row_dict["label_hash"],
            branch_name=label_row_dict["branch_name"],
            dataset_hash=label_row_dict["dataset_hash"],
            dataset_title=label_row_dict["dataset_title"],
            data_title=label_row_dict["data_title"],
            data_hash=label_row_dict["data_hash"],
            group_hash=label_row_dict.get("group_hash", self._label_row_read_only_data.group_hash),
            data_type=data_type,
            label_status=LabelStatus(label_row_dict["label_status"]),
            annotation_task_status=label_row_dict.get("annotation_task_status"),
            workflow_graph_node=label_row_dict.get(
                "workflow_graph_node", self._label_row_read_only_data.workflow_graph_node
            ),
            is_shadow_data=self.is_shadow_data,
            created_at=parse_datetime_optional(label_row_dict["created_at"]),
            last_edited_at=parse_datetime_optional(label_row_dict["last_edited_at"]),
            frame_level_data=frame_level_data,
            image_hash_to_frame=image_hash_to_frame,
            frame_to_image_hash=frame_to_image_hash,
            duration=self.duration,
            fps=self.fps,
            number_of_frames=self.number_of_frames,
            data_link=data_link,
            height=height,
            width=width,
            audio_codec=audio_codec,
            audio_sample_rate=audio_sample_rate,
            audio_num_channels=audio_num_channels,
            audio_bit_depth=audio_bit_depth,
            task_uuid=label_row_dict.get("task_uuid", self._label_row_read_only_data.task_uuid),
            priority=label_row_dict.get("priority", self._label_row_read_only_data.priority),
            client_metadata=label_row_dict.get("client_metadata", self._label_row_read_only_data.client_metadata),
            images_data=label_row_dict.get("images_data", self._label_row_read_only_data.images_data),
            file_type=file_type,
            is_valid=bool(label_row_dict.get("is_valid", True)),
            backing_item_uuid=self.backing_item_uuid,
            assigned_user_email=label_row_dict.get(
                "assigned_user_email", self._label_row_read_only_data.assigned_user_email
            ),
            last_actioned_by_user_email=label_row_dict.get(
                "last_actioned_by_user_email", self._label_row_read_only_data.last_actioned_by_user_email
            ),
        )

    def _parse_labels_from_dict(self, label_row_dict: dict):
        classification_answers = label_row_dict["classification_answers"]
        object_answers = label_row_dict["object_answers"]

        # Attempt to instantiate all classifications - ranged only or with frames
        for classification_answer in classification_answers.values():
            if classification_instance := self._create_new_classification_instance_from_answer(classification_answer):
                self.add_classification_instance(classification_instance)

        for data_unit in label_row_dict["data_units"].values():
            data_type = DataType(label_row_dict["data_type"])
            labels = data_unit.get("labels", {})

            if data_type == DataType.IMG_GROUP or data_type == DataType.IMAGE:
                frame = int(data_unit["data_sequence"])
                self._add_object_instances_from_objects(labels.get("objects", []), frame)
                self._add_classification_instances_from_classifications_frame(
                    labels.get("classifications", []),
                    classification_answers,
                    frame,
                )
                self._add_objects_answers(object_answers)

            elif (
                data_type == DataType.VIDEO
                or data_type == DataType.DICOM
                or data_type == DataType.NIFTI
                or data_type == DataType.PDF
                or data_type == DataType.SCENE
            ):
                for frame, frame_data in labels.items():
                    frame_num = int(frame)
                    self._add_object_instances_from_objects(frame_data["objects"], frame_num)
                    self._add_classification_instances_from_classifications_frame(
                        frame_data["classifications"], classification_answers, frame_num
                    )
                    self._add_frame_metadata(frame_num, frame_data.get("metadata"))
                self._add_objects_answers(object_answers)

            elif data_type == DataType.GROUP:
                # TODO: Make this work for classifications
                pass
                # for frame, frame_data in labels.items():
                #     frame_num = int(frame)
                #     self._add_classification_instances_from_classifications(
                #         frame_data["classifications"], classification_answers, frame_num
                #     )
                #     self._add_frame_metadata(frame_num, frame_data.get("metadata"))

            elif data_type == DataType.DICOM_STUDY:
                pass  # TODO: _add_object_answers a NO-OP here as well?

            elif data_type == DataType.MISSING_DATA_TYPE:
                raise NotImplementedError(f"Got an unexpected data type `{data_type}`")

            elif data_type == DataType.AUDIO or data_type == DataType.PLAIN_TEXT:
                is_html = data_unit["data_type"] == "text/html"
                self._add_objects_instances_from_objects_without_frames(object_answers, html=is_html)
            else:
                exhaustive_guard(data_type)

            self._add_data_unit_metadata(data_type, data_unit.get("metadata"))

    def _add_frame_metadata(self, frame: int, metadata: Optional[Dict[str, str]]):
        if metadata is not None:
            self._frame_metadata[frame] = DICOMSliceMetadata.from_dict(metadata)
        else:
            self._frame_metadata[frame] = None

    def _add_data_unit_metadata(self, data_type: DataType, metadata: Optional[Dict[str, str]]) -> None:
        if metadata is None:
            self._metadata = None
            return

        if data_type == DataType.DICOM:
            self._metadata = DICOMSeriesMetadata.from_dict(metadata)
        elif data_type == DataType.GROUP:
            self._metadata = DataGroupMetadata.from_dict(metadata)
        else:
            log.warning(
                f"Unexpected metadata for the data type: {data_type}. Please update the Encord SDK to the latest version."
            )

    def _add_objects_instances_from_objects_without_frames(
        self,
        object_answers: dict,
        html: bool = False,
    ):
        if html:
            for object_answer in object_answers.values():
                object_instance = self._create_new_html_object_instance(object_answer, object_answer["range_html"])
                self.add_object_instance(object_instance)

        else:
            for object_answer in object_answers.values():
                ranges: Ranges = []
                for range_elem in object_answer["range"]:
                    ranges.append(Range(range_elem[0], range_elem[1]))

                object_instance = self._create_new_object_instance_with_ranges(object_answer, ranges)
                self.add_object_instance(object_instance)

    def _add_object_instances_from_objects(
        self,
        objects_list: List[FrameObject],
        frame: int,
    ) -> None:
        for frame_object_label in objects_list:
            object_hash = frame_object_label["objectHash"]
            if object_hash not in self._objects_map:
                object_instance = self._create_new_object_instance(frame_object_label, frame)
                self.add_object_instance(object_instance)
            else:
                self._add_coordinates_to_object_instance(frame_object_label, frame)

    def _add_objects_answers(self, object_answers: dict):
        for answer in object_answers.values():
            object_hash = answer["objectHash"]
            # In cases when we had an object, added some attributes for this object, and then removed the object,
            # in some label rows we still have such "orphaned" answers.
            # To avoid parser errors, we're omitting attributes for the object that is not in label rows.
            if object_instance := self._objects_map.get(object_hash):
                answer_list = answer["classifications"]
                object_instance.set_answer_from_list(answer_list)

    def _add_action_answers(self, label_row_dict: dict):
        for answer in label_row_dict["object_actions"].values():
            object_hash = answer["objectHash"]
            object_instance = self._objects_map.get(object_hash)

            if object_instance is not None:
                answer_list = answer["actions"]
                object_instance.set_answer_from_list(answer_list)
            else:
                answer_list = answer["actions"]
                for answer_dict in answer_list:
                    space_id = answer_dict.get("spaceId")
                    if space_id is None:
                        raise LabelRowError("Object action does not contain spaceId")

                    space = self.get_space(id=space_id, type_="video")
                    space._set_answer_from_list(object_hash, answers_list=[answer_dict])

    def _create_new_object_instance(self, frame_object_label: FrameObject, frame: int) -> ObjectInstance:
        ontology = self._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]

        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        object_instance = ObjectInstance(label_class, object_hash=object_hash)

        coordinates = get_coordinates_from_frame_object_dict(frame_object_label)
        object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(frame_object_label)

        object_instance.set_for_frames(
            coordinates=coordinates,
            frames=frame,
            created_at=object_frame_instance_info.created_at,
            created_by=object_frame_instance_info.created_by,
            last_edited_at=object_frame_instance_info.last_edited_at,
            last_edited_by=object_frame_instance_info.last_edited_by,
            confidence=object_frame_instance_info.confidence,
            manual_annotation=object_frame_instance_info.manual_annotation,
            reviews=object_frame_instance_info.reviews,
            is_deleted=object_frame_instance_info.is_deleted,
        )
        return object_instance

    # This is only to be used by non-frame modalities (e.g. Audio)
    def _create_new_object_instance_with_ranges(
        self,
        object_answer: ObjectAnswerForNonGeometric,
        ranges: Ranges,
    ) -> ObjectInstance:
        feature_hash = object_answer["featureHash"]
        object_hash = object_answer["objectHash"]

        label_class = self._ontology.structure.get_child_by_hash(feature_hash, type_=Object)

        frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
        frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.

        frame_object_dict = cast(BaseFrameObject, frame_info_dict)
        object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(frame_object_dict)

        expected_shape: Shape
        coordinates: Union[AudioCoordinates, TextCoordinates]
        if self._label_row_read_only_data.data_type == DataType.AUDIO:
            expected_shape = Shape.AUDIO
            coordinates = AudioCoordinates(range=ranges)
        elif self._label_row_read_only_data.data_type == DataType.PLAIN_TEXT:
            expected_shape = Shape.TEXT
            coordinates = TextCoordinates(range=ranges)
        else:
            unknown_data_type = self._label_row_read_only_data.data_type
            raise RuntimeError(f"Unexpected data type[{unknown_data_type}] for range based objects")
        if label_class.shape != expected_shape:
            raise LabelRowError("Unsupported object shape for data type")
        object_instance = ObjectInstance(label_class, object_hash=object_hash)

        object_instance.set_for_frames(
            coordinates,
            frames=0,
            created_at=object_frame_instance_info.created_at,
            created_by=object_frame_instance_info.created_by,
            confidence=object_frame_instance_info.confidence,
            manual_annotation=object_frame_instance_info.manual_annotation,
            last_edited_at=object_frame_instance_info.last_edited_at,
            last_edited_by=object_frame_instance_info.last_edited_by,
            reviews=object_frame_instance_info.reviews,
            overwrite=True,
            # Always overwrite during label row dict parsing, as older dicts known to have duplicates
        )
        answer_list = object_answer["classifications"]
        object_instance.set_answer_from_list(answer_list)

        return object_instance

    def _create_new_html_object_instance(
        self,
        object_answer: ObjectAnswerForNonGeometric,
        range_html: dict,
    ) -> ObjectInstance:
        feature_hash = object_answer["featureHash"]
        object_hash = object_answer["objectHash"]

        label_class = self._ontology.structure.get_child_by_hash(feature_hash, type_=Object)

        frame_info_dict = {k: v for k, v in object_answer.items() if v is not None}
        frame_info_dict.setdefault("confidence", 1.0)  # confidence sometimes not present.

        frame_object_dict = cast(BaseFrameObject, frame_info_dict)
        object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(frame_object_dict)

        object_instance = ObjectInstance(label_class, object_hash=object_hash)
        object_instance.set_for_frames(
            HtmlCoordinates(range=[HtmlRange.from_dict(x) for x in range_html]),
            frames=0,
            created_at=object_frame_instance_info.created_at,
            created_by=object_frame_instance_info.created_by,
            confidence=object_frame_instance_info.confidence,
            manual_annotation=object_frame_instance_info.manual_annotation,
            last_edited_at=object_frame_instance_info.last_edited_at,
            last_edited_by=object_frame_instance_info.last_edited_by,
            reviews=object_frame_instance_info.reviews,
            overwrite=True,
            # Always overwrite during label row dict parsing, as older dicts known to have duplicates
        )
        answer_list = object_answer["classifications"]
        object_instance.set_answer_from_list(answer_list)

        return object_instance

    def _add_coordinates_to_object_instance(
        self,
        frame_object_label: FrameObject,
        frame: int = 0,
    ) -> None:
        object_hash = frame_object_label["objectHash"]
        object_instance = self._objects_map[object_hash]

        coordinates = get_coordinates_from_frame_object_dict(frame_object_label)
        object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(frame_object_label)

        object_instance.set_for_frames(
            coordinates=coordinates,
            frames=frame,
            created_at=object_frame_instance_info.created_at,
            created_by=object_frame_instance_info.created_by,
            last_edited_at=object_frame_instance_info.last_edited_at,
            last_edited_by=object_frame_instance_info.last_edited_by,
            confidence=object_frame_instance_info.confidence,
            manual_annotation=object_frame_instance_info.manual_annotation,
            reviews=object_frame_instance_info.reviews,  # type: ignore
            is_deleted=object_frame_instance_info.is_deleted,
        )

    def _add_classification_instances_from_classifications_frame(
        self,
        classifications_list: List[FrameClassification],
        classification_answers: Dict[str, ClassificationAnswer],
        frame: int,
    ):
        for frame_classification_label in classifications_list:
            classification_hash = frame_classification_label["classificationHash"]
            if classification_hash in self._classifications_map:
                self._add_frames_to_classification_instance(frame_classification_label, frame)
            elif classification_instance := self._create_new_classification_instance_from_frame(
                frame_classification_label, frame, classification_answers
            ):
                self.add_classification_instance(classification_instance)

    def _parse_image_group_frame_level_data(self, label_row_data_units: dict) -> Dict[int, FrameLevelImageGroupData]:
        frame_level_data: Dict[int, LabelRowV2.FrameLevelImageGroupData] = {}
        for payload in label_row_data_units.values():
            frame_number = int(payload["data_sequence"])
            frame_level_image_group_data = self.FrameLevelImageGroupData(
                image_hash=payload["data_hash"],
                image_title=payload["data_title"],
                data_link=payload.get("data_link"),
                file_type=payload["data_type"],
                frame_number=frame_number,
                # Dimensions should be always there
                # But we have some older entries that don't have them
                # So setting them to 0 for now until the format is not guaranteed to be enforced
                width=payload.get("width", 0),
                height=payload.get("height", 0),
            )
            frame_level_data[frame_number] = frame_level_image_group_data
        return frame_level_data

    def _create_new_classification_instance_from_frame(
        self,
        frame_classification_label: FrameClassification,
        frame: int,
        classification_answers: Dict[str, ClassificationAnswer],
    ) -> Optional[ClassificationInstance]:
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]

        label_class = self._ontology.structure.get_child_by_hash(feature_hash, type_=Classification)
        classification_instance = ClassificationInstance(label_class, classification_hash=classification_hash)

        frame_view = ClassificationInstance.FrameData.from_dict(frame_classification_label)
        classification_instance.set_for_frames(
            frame,
            created_at=frame_view.created_at,
            created_by=frame_view.created_by,
            confidence=frame_view.confidence,
            manual_annotation=frame_view.manual_annotation,
            last_edited_at=frame_view.last_edited_at,
            last_edited_by=frame_view.last_edited_by,
            reviews=frame_view.reviews,
            overwrite=True,  # Always overwrite during label row dict parsing, as older dicts known to have duplicates
        )

        # For some older label rows we might have a classification entry, but without an assigned answer.
        # These cases are equivalent to not having classifications at all, so just ignoring them
        if classification_answer := classification_answers.get(classification_hash):
            answers_dict = classification_answer["classifications"]
            self._add_static_answers_from_dict(classification_instance, answers_dict)
            return classification_instance

        return None

    def _create_new_classification_instance_from_answer(
        self, classification_answer: ClassificationAnswer
    ) -> ClassificationInstance | None:
        """Create a ClassificationInstance from a classification answer if sufficient metadata is present"""
        if not _is_containing_metadata(classification_answer):
            return None

        feature_hash = classification_answer["featureHash"]
        classification_hash = classification_answer["classificationHash"]

        label_class = self._ontology.structure.get_child_by_hash(feature_hash, type_=Classification)

        range_view = ClassificationInstance.FrameData.from_dict(classification_answer)
        is_data_type_range_only = not is_geometric(self.data_type)

        classification_instance = ClassificationInstance(
            label_class,
            classification_hash=classification_hash,
            range_only=is_data_type_range_only,
            _created_with_answer=True,
        )

        frame_ranges = classification_answer.get("range", [])
        parsed_frame_ranges = ranges_list_to_ranges(frame_ranges or [])
        classification_instance.set_for_frames(
            frames=parsed_frame_ranges,
            created_at=range_view.created_at,
            created_by=range_view.created_by,
            confidence=range_view.confidence,
            manual_annotation=range_view.manual_annotation,
            last_edited_at=range_view.last_edited_at,
            last_edited_by=range_view.last_edited_by,
            reviews=range_view.reviews,
            overwrite=True,  # Always overwrite during label row dict parsing, as older dicts known to have duplicates
        )

        answers_list = classification_answer["classifications"]
        self._add_static_answers_from_dict(classification_instance, answers_list)

        return classification_instance

    def _add_static_answers_from_dict(
        self, classification_instance: ClassificationInstance, answers_list: List[AttributeDict]
    ) -> None:
        classification_instance.set_answer_from_list(answers_list)

    def _add_frames_to_classification_instance(
        self, frame_classification_label: FrameClassification, frame: int
    ) -> None:
        object_hash = frame_classification_label["classificationHash"]
        classification_instance = self._classifications_map[object_hash]
        frame_view = ClassificationInstance.FrameData.from_dict(frame_classification_label)
        classification_instance.set_frame_data(frame_view, frame)

    def _check_labelling_is_initalised(self):
        if not self.is_labelling_initialised:
            raise LabelRowError(
                "For this operation you will need to initialise labelling first. Call the `.initialise_labels()` "
                "to do so first."
            )

    def _method_not_supported_for_audio(self, range_only: bool = False):
        if self.data_type == DataType.AUDIO and not range_only:
            raise LabelRowError("This method is not supported for audio.")

    def __repr__(self) -> str:
        return f"LabelRowV2(label_hash={self.label_hash}, data_hash={self.data_hash}, data_title={self.data_title})"


def _frame_views_to_frame_numbers(
    frame_views: Sequence[
        Union[
            ObjectInstance.Annotation,
            ClassificationInstance.Annotation,
            LabelRowV2.FrameView,
            ObjectAnnotation,  # Here for backwards compatibility
            ClassificationAnnotation,  # Here for backwards compatibility
        ]
    ],
) -> List[int]:
    return [frame_view.frame for frame_view in frame_views]
