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

from collections import OrderedDict
from enum import Enum

from cord.orm import base_orm


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

    DB_FIELDS = OrderedDict([
        ("model_operation", int),
        ("model_parameters", dict)
    ])


class ModelRow(base_orm.BaseORM):
    """
    A model row contains a set of features and a model (resnet18, resnet34, resnet50, resnet101, resnet152,
    vgg16, vgg19, yolov5, faster_rcnn, mask_rcnn).

    ORM:

    model_hash (uid),
    title,
    description,
    features,
    model,

    """

    DB_FIELDS = OrderedDict([
        ("model_hash", str),
        ("title", str),
        ("description", str),
        ("features", list),
        ("model", str),
    ])


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

    DB_FIELDS = OrderedDict([
        ("files", list),
        ("conf_thresh", float),  # Confidence threshold
        ("iou_thresh", float),  # Intersection over union threshold
        ("device", str),
        ("detection_frame_range", list),
        ("allocation_enabled", bool)
    ])


class ModelTrainingWeights(base_orm.BaseORM):
    """
    Model training weights.

    ORM:

    training_config_link,
    training_weights_link,

    """

    DB_FIELDS = OrderedDict([
        ("model", str),
        ("training_config_link", str),
        ("training_weights_link", str),
    ])


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

    DB_FIELDS = OrderedDict([
        ("model_hash", str),
        ("label_rows", list),
        ("epochs", int),
        ("batch_size", int),
        ("weights", ModelTrainingWeights),
        ("device", str),
    ])
