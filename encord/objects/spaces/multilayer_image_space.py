from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional, Sequence, cast

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.coordinates import (
    GeometricCoordinates,
    add_coordinates_to_frame_object_dict,
    get_geometric_coordinates_from_frame_object_dict,
)
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.spaces.annotation.base_annotation import (
    _AnnotationData,
    _AnnotationMetadata,
)
from encord.objects.spaces.annotation.geometric_annotation import (
    _GeometricAnnotationData,
    _GeometricObjectAnnotation,
)
from encord.objects.spaces.annotation.global_annotation import _GlobalClassificationAnnotation
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.image_space import ImageSpace
from encord.objects.spaces.multiframe_space.multiframe_space import FrameOverlapStrategy
from encord.objects.spaces.types import ImageSpaceInfo, MultiLayerImageSpaceInfo, SpaceInfo
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    FrameClassification,
    FrameObject,
    LabelBlob,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    _is_global_classification_on_space,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.ontology_labels_impl import LabelRowV2


class MultiLayerImageSpace(ImageSpace):
    """Multilayer space implementation for images in a datagroup that share the same labels."""

    def __init__(self, space_id: str, label_row: LabelRowV2, space_info: SpaceInfo, width: int, height: int):
        super().__init__(space_id, label_row, space_info, width, height)

    """INTERNAL METHODS FOR DESERDE"""

    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> Dict[str, ObjectAnswer]:
        ret: dict[str, ObjectAnswerForGeometric] = {}
        for object_instance in self.get_object_instances():
            all_static_answers = self._label_row._get_all_static_answers(object_instance)
            object_index_element: ObjectAnswerForGeometric = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": object_instance.object_hash,
            }
            ret[object_instance.object_hash] = object_index_element

        return cast(Dict[str, ObjectAnswer], ret)

    def _to_classification_answers(
        self, existing_classification_answers: Dict[str, ClassificationAnswer]
    ) -> Dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}
        for classification in self.get_classification_instances():
            all_static_answers = classification.get_all_static_answers()
            classifications: list[AttributeDict] = [
                cast(AttributeDict, answer.to_encord_dict()) for answer in all_static_answers if answer.is_answered()
            ]

            classification_answer: ClassificationAnswer
            if classification.is_global():
                classification_answer = self._to_global_classification_answer(
                    classification_instance=classification,
                    classifications=classifications,
                    space_range={"range": [], "type": "frame"},
                )
            elif self.space_id == "root":
                classification_answer = {
                    "classifications": classifications,
                    "classificationHash": classification.classification_hash,
                    "featureHash": classification.feature_hash,
                    "spaces": {},
                }

            else:
                classification_answer = {
                    "classifications": classifications,
                    "classificationHash": classification.classification_hash,
                    "featureHash": classification.feature_hash,
                    "spaces": {
                        self.space_id: {
                            "range": [[0, 0]],  # For images, there is only one frame
                            "type": "frame",
                        }
                    },
                }

            ret[classification.classification_hash] = classification_answer
        return ret

    def _to_space_dict(self) -> MultiLayerImageSpaceInfo:
        """Export multilayer image space to dictionary format."""
        label_hashes: list[str] = list(self._objects_map.keys())
        label_hashes.extend(list(self._classifications_map.keys()))
        frame_label = self._build_frame_label_dict()
        return MultiLayerImageSpaceInfo(
            space_type=SpaceType.MULTI_LAYER_IMAGE,
            width=self._width,
            height=self._height,
            labels={
                "0": frame_label,
            },
        )
