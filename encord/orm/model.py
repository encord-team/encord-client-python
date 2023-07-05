#
# Copyright (c) 2023 Cord Technologies Limited
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
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from dateutil.parser import parse

from encord.constants.model import AutomationModels
from encord.exceptions import EncordException
from encord.orm import base_orm
from encord.orm.formatter import Formatter
from encord.utilities.common import ENCORD_CONTACT_SUPPORT_EMAIL


class ModelOperations(Enum):
    INFERENCE = 0
    TRAIN = 1
    CREATE = 2


class Model(base_orm.BaseORM):
    """
    Model base ORM.

    ORM:

    model_operation,
    model_parameters,

    """

    DB_FIELDS = OrderedDict([("model_operation", int), ("model_parameters", dict)])


@dataclass
class ModelConfiguration(Formatter):
    model_uid: str
    title: str
    description: str
    feature_node_hashes: List[str]
    """The corresponding feature node hashes of the ontology object"""
    model: AutomationModels
    model_iteration_uids: List[str]
    """All the UIDs of individual model training instances"""

    @classmethod
    def from_dict(cls, json_dict: dict):
        return ModelConfiguration(
            model_uid=json_dict["model_uid"],
            title=json_dict["title"],
            description=json_dict["description"],
            feature_node_hashes=cls._get_feature_node_hashes(json_dict["feature_node_hashes"]),
            model=cls._get_automation_model(json_dict["model"]),
            model_iteration_uids=json_dict["model_iteration_uids"],
        )

    @staticmethod
    def _get_feature_node_hashes(features: dict) -> List[str]:
        return list(features.keys())

    @staticmethod
    def _get_automation_model(automation_model_str: str) -> AutomationModels:
        try:
            return AutomationModels(automation_model_str)
        except ValueError as e:
            raise EncordException(
                "A model was returned which was not recognised. Please upgrade your SDK "
                f"to the latest version or contact support at {ENCORD_CONTACT_SUPPORT_EMAIL}."
            ) from e


@dataclass
class ModelTrainingLabelMetadata:
    label_uid: str
    data_uid: str
    data_link: str

    @staticmethod
    def from_dict(json_dict: dict) -> "ModelTrainingLabelMetadata":
        return ModelTrainingLabelMetadata(
            label_uid=json_dict["label_uid"],
            data_uid=json_dict["data_uid"],
            data_link=json_dict["data_link"],
        )

    @classmethod
    def from_list(cls, json_list: list) -> List["ModelTrainingLabelMetadata"]:
        return [cls.from_dict(item) for item in json_list]


@dataclass
class ModelTrainingLabel:
    label_metadata_list: List[ModelTrainingLabelMetadata]
    feature_uids: List[str]

    @staticmethod
    def from_dict(json_dict: dict) -> "ModelTrainingLabel":
        return ModelTrainingLabel(
            label_metadata_list=ModelTrainingLabelMetadata.from_list(json_dict["label_metadata_list"]),
            feature_uids=json_dict["feature_uids"],
        )


@dataclass
class TrainingMetadata(Formatter):
    model_iteration_uid: str
    created_at: Optional[datetime] = None
    training_final_loss: Optional[float] = None
    model_training_labels: Optional[ModelTrainingLabel] = None

    @classmethod
    def from_dict(cls, json_dict: dict):
        return TrainingMetadata(
            model_iteration_uid=json_dict["model_iteration_uid"],
            created_at=cls.get_created_at(json_dict),
            training_final_loss=json_dict["training_final_loss"],
            model_training_labels=cls.get_model_training_labels(json_dict),
        )

    @staticmethod
    def get_created_at(json_dict: dict) -> Optional[datetime]:
        created_at = json_dict["created_at"]
        if created_at is None:
            return None

        return parse(created_at)

    @staticmethod
    def get_model_training_labels(json_dict: dict) -> Optional[ModelTrainingLabel]:
        model_training_labels = json_dict["model_training_labels"]
        if model_training_labels is None:
            return None

        return ModelTrainingLabel.from_dict(model_training_labels)


class ModelRow(base_orm.BaseORM):
    """
    A model row contains a set of features and a model (resnet18, resnet34, resnet50, resnet101, resnet152,
    vgg16, vgg19, faster_rcnn, mask_rcnn).

    ORM:

    model_hash (uid),
    title,
    description,
    features,
    model,

    """

    DB_FIELDS = OrderedDict(
        [
            ("model_hash", str),
            ("title", str),
            ("description", str),
            ("features", list),
            ("model", str),
        ]
    )


class ModelInferenceParams(base_orm.BaseORM):
    """
    Model inference parameters for running models trained via the platform.

    ORM:

    local_file_path,
    conf_thresh,
    iou_thresh,
    device
    detection_frame_range (optional)

    """

    DB_FIELDS = OrderedDict(
        [
            ("files", list),
            ("conf_thresh", float),  # Confidence threshold
            ("iou_thresh", float),  # Intersection over union threshold
            ("device", str),
            ("detection_frame_range", list),
            ("allocation_enabled", bool),
            ("data_hashes", list),
            ("rdp_thresh", float),
        ]
    )


class ModelTrainingWeights(base_orm.BaseORM):
    """
    Model training weights.

    ORM:

    training_config_link,
    training_weights_link,

    """

    DB_FIELDS = OrderedDict(
        [
            ("model", str),
            ("training_config_link", str),
            ("training_weights_link", str),
        ]
    )


class ModelTrainingParams(base_orm.BaseORM):
    """
    Model training parameters.

    ORM:

    model_hash,
    label_rows,
    epochs,
    batch_size,
    weights,
    device

    """

    DB_FIELDS = OrderedDict(
        [
            ("model_hash", str),
            ("label_rows", list),
            ("epochs", int),
            ("batch_size", int),
            ("weights", ModelTrainingWeights),
            ("device", str),
        ]
    )
