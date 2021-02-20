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


class LabelingAlgorithm(base_orm.BaseORM):
    """
    Labeling algorithm base ORM.

    ORM:

    algorithm_name,
    algorithm_params

    """

    DB_FIELDS = OrderedDict([
        ("algorithm_name", str),
        ("algorithm_parameters", dict),  # algorithm params
    ])


class ObjectInterpolationParams(base_orm.BaseORM):
    """
    Labeling algorithm parameters for interpolation algorithm

    ORM:

    key_frames,
    objects_to_interpolate

    """

    DB_FIELDS = OrderedDict([
        ("key_frames", dict),
        ("objects_to_interpolate", list),
    ])
