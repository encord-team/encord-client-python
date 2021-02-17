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


class LabelingAlgorithm(base_orm.BaseORM):
    """
    Labeling algorithm base ORM.

    ORM:

    """

    DB_FIELDS = OrderedDict([])


class LabelInterpolationParams(base_orm.BaseORM):
    """
    Labeling algorithm parameters for interpolation algorithm

    ORM:

    algorithm_name,
    algorithm_params,

    """

    DB_FIELDS = OrderedDict([
        ("algorithm_name", str),
        ("algorithm_parameters", dict),  # Interpolation params
    ])

def LabelingAlgorithmParamGetter(name,algo_params):
    if name == "INTERPOLATION":
        params = LabelInterpolationParams({
            'algorithm_name': "INTERPOLATION",
            'algorithm_parameters': algo_params,
        })
        return params

    raise InvalidAlgorithmError("Invalid algorithm name")