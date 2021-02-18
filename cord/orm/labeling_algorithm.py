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

from cord.exceptions import InvalidAlgorithmError

from cord.utils.str_constants import INTERPOLATION


class LabelingAlgorithm(base_orm.BaseORM):
    """
    Labeling algorithm base ORM.
    ORM:
    algorithm_name,
    algorithm_params,
    """

    DB_FIELDS = OrderedDict([
        ("algorithm_name", str),
        ("algorithm_parameters", dict),  # algorithm params
    ])


class LabelInterpolationParams(base_orm.BaseORM):
    """
    Labeling algorithm parameters for interpolation algorithm
    ORM:
    labels,
    project_hash,
    objects_to_track,
    tracking_Frame_range,
    user_hash
    """

    DB_FIELDS = OrderedDict([
        ("labels", dict),
        ("project_hash", str),
        ("objects_to_track", list),
        ("tracking_frame_range", list),
        ("user_hash" , str),
    ])

def LabelingAlgorithmParamGetter(name,algo_params):
    """
    Routes to correct labeling algorithm parameters
    """
    if name == INTERPOLATION:
        interpolation_params = LabelInterpolationParams({
            'labels': algo_params.get("labels"),
            'project_hash': algo_params.get("project_hash"),
            'objects_to_track': algo_params.get("objects_to_track"),
            'tracking_frame_range': algo_params.get("tracking_frame_range"),
            'user_hash': algo_params.get("user_hash"),
        })

        params = LabelingAlgorithm({
            'algorithm_name': INTERPOLATION,
            'algorithm_parameters': interpolation_params,
        })

        return params

    raise InvalidAlgorithmError("Invalid algorithm name")
