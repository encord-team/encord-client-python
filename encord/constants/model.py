"""---
title: "Model"
slug: "sdk-ref-model"
hidden: false
metadata:
  title: "Model"
  description: "Encord SDK Model classes."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from enum import Enum
from typing import Set, cast


class Device(Enum):
    CUDA = "cuda"
    CPU = "cpu"

    @classmethod
    def has_value(cls, value) -> bool:
        # pylint: disable-next=no-member
        return value in cls._value2member_map_


class AutomationModels(Enum):
    FAST_AI = "fast_ai"
    RESNET18 = "resnet18"
    RESNET34 = "resnet34"
    RESNET50 = "resnet50"
    RESNET101 = "resnet101"
    RESNET152 = "resnet152"
    VGG16 = "vgg16"
    VGG19 = "vgg19"
    FASTER_RCNN = "faster_rcnn"
    MASK_RCNN = "mask_rcnn"

    @staticmethod
    def classification_options() -> Set[AutomationModels]:
        """Returns:
        Model types that can be used for frame-level classifications.
        That is, model types that can be used with ``<feature_node_hash>``es from
        the ``classification`` part of the ontology.
        """
        return {
            AutomationModels.FAST_AI,
            AutomationModels.RESNET18,
            AutomationModels.RESNET34,
            AutomationModels.RESNET50,
            AutomationModels.RESNET101,
            AutomationModels.RESNET152,
            AutomationModels.VGG16,
            AutomationModels.VGG19,
        }

    @staticmethod
    def object_detection_options() -> Set[AutomationModels]:
        """Returns:
        Model types that can be used with bounding_box type
        ``<feature_node_hashes>`` from the ``objects`` part of the project ontology.
        """
        return {AutomationModels.FASTER_RCNN}

    @staticmethod
    def instance_segmentation_options() -> Set[AutomationModels]:
        """Returns:
        Model types that can be used with polygon type ``<feature_node_hashes>``
        from the ``objects`` part of the project ontology.
        """
        return {AutomationModels.MASK_RCNN}

    @classmethod
    def has_value(cls, value) -> bool:
        # pylint: disable-next=no-member
        return value in cls._value2member_map_


# For backward compatibility
FAST_AI = cast(str, AutomationModels.FAST_AI.value)
RESNET18 = cast(str, AutomationModels.RESNET18.value)
RESNET34 = cast(str, AutomationModels.RESNET34.value)
RESNET50 = cast(str, AutomationModels.RESNET50.value)
RESNET101 = cast(str, AutomationModels.RESNET101.value)
RESNET152 = cast(str, AutomationModels.RESNET152.value)
VGG16 = cast(str, AutomationModels.VGG16.value)
VGG19 = cast(str, AutomationModels.VGG19.value)
FASTER_RCNN = cast(str, AutomationModels.FASTER_RCNN.value)
MASK_RCNN = cast(str, AutomationModels.MASK_RCNN.value)
