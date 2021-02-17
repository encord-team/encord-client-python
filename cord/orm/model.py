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

from cord.orm import base_orm


class Model(base_orm.BaseORM):
    """
    Model base ORM.

    ORM:

    """

    DB_FIELDS = OrderedDict([])


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
        ("detection_frame_range", list)
    ])
