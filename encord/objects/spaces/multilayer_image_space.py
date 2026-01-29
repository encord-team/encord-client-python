from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, cast

from encord.constants.enums import SpaceType
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.spaces.image_space import ImageSpace
from encord.objects.spaces.types import MultilayerImageSpaceInfo, SpaceInfo
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    ObjectAnswer,
    ObjectAnswerForGeometric,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class MultilayerImageSpace(ImageSpace):
    """Multilayer space implementation for images in a datagroup that share the same labels."""

    def __init__(self, space_id: str, label_row: LabelRowV2, space_info: SpaceInfo, width: int, height: int):
        super().__init__(space_id, label_row, space_info, width, height)

    """INTERNAL METHODS FOR DESERDE"""

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
            elif self.space_id == ROOT_SPACE_ID:
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

    def _to_space_dict(self) -> MultilayerImageSpaceInfo:
        """Export multilayer image space to dictionary format."""
        label_hashes: list[str] = list(self._objects_map.keys())
        label_hashes.extend(list(self._classifications_map.keys()))
        frame_label = self._build_frame_label_dict()
        return MultilayerImageSpaceInfo(
            space_type=SpaceType.MULTILAYER_IMAGE,
            width=self._width,
            height=self._height,
            labels={
                "0": frame_label,
            },
        )
