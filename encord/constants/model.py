#
# Copyright (c) 2020 Cord Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import annotations

from enum import Enum
from typing import List


class AUTOMATION_MODELS(Enum):
    FAST_AI = "fast_ai"
    RESNET18 = "resnet18"
    RESNET34 = "resnet34"
    RESNET50 = "resnet50"
    RESNET101 = "resnet101"
    RESNET152 = "resnet152"
    VGG16 = "vgg16"
    VGG19 = "vgg19"
    YOLOV5 = "yolov5"
    FASTER_RCNN = "faster_rcnn"
    MASK_RCNN = "mask_rcnn"

    @staticmethod
    def classification_options() -> List[AUTOMATION_MODELS]:
        """
        Returns:
            Model types that can be used for frame-level classifications.
            That is, model types that can be used with ``<feature_node_hash>``es from
            the ``classification`` part of the ontology.
        """
        return [
            AUTOMATION_MODELS.FAST_AI,
            AUTOMATION_MODELS.RESNET18,
            AUTOMATION_MODELS.RESNET34,
            AUTOMATION_MODELS.RESNET50,
            AUTOMATION_MODELS.RESNET101,
            AUTOMATION_MODELS.RESNET152,
            AUTOMATION_MODELS.VGG16,
            AUTOMATION_MODELS.VGG19,
        ]

    @staticmethod
    def object_detection_options() -> List[AUTOMATION_MODELS]:
        """
        Returns:
            Model types that can be used with bounding_box type
            ``<feature_node_hashes>`` from the ``objects`` part of the project ontology.
        """
        return [AUTOMATION_MODELS.YOLOV5, AUTOMATION_MODELS.FASTER_RCNN]

    @staticmethod
    def instance_segmentation_options() -> List[AUTOMATION_MODELS]:
        """
        Returns:
            Model types that can be used with polygon type ``<feature_node_hashes>``
            from the ``objects`` part of the project ontology.
        """
        return [AUTOMATION_MODELS.MASK_RCNN]

    @staticmethod
    def has_value(cls, value):
        return value in set(v for v in cls._value2member_map_)


# For backward compatibility
FAST_AI = AUTOMATION_MODELS.FAST_AI
RESNET18 = AUTOMATION_MODELS.RESNET18
RESNET34 = AUTOMATION_MODELS.RESNET34
RESNET50 = AUTOMATION_MODELS.RESNET50
RESNET101 = AUTOMATION_MODELS.RESNET101
RESNET152 = AUTOMATION_MODELS.RESNET152
VGG16 = AUTOMATION_MODELS.VGG16
VGG19 = AUTOMATION_MODELS.VGG19
YOLOV5 = AUTOMATION_MODELS.YOLOV5
FASTER_RCNN = AUTOMATION_MODELS.FASTER_RCNN
MASK_RCNN = AUTOMATION_MODELS.MASK_RCNN
