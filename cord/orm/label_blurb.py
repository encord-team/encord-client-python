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


class Label(base_orm.BaseORM):
    """
    A label contains a frame labels blurb, object answers, and classification answers.

    The label DB object is specific to a data asset, and can contain thousands of frames with bounding boxes,
    polygons, and classifications.

    The data link consist of a signed URL expiring after 7 days.

    Each frame-level object and classification has unique identifiers 'objectHash' and 'classificationHash'.
    Each frame-level entity has a unique feature identifier 'featureHash', defined in the editor ontology.

    The objects and classifications answer dictionaries contain classification 'answers' (i.e. attributes
    that describe the object or classification). This is to avoid storing the information at every frame
    in the blurb.

    An object can be either a bounding box, or a polygon object.

    The labels dictionary is in the form:
    {
        "frame": {
            "objects": {
                [{object 1}, {object 2}, ...]
            }
            "classifications": {
                [{classification 1}, {classification 2}, ...]
            }
        }
    }

    The object answers dictionary is in the form:
    {
        "objectHash": {
            "objectHash": objectHash,
            "classifications": [{answer 1}, {answer 2}, ...]
        },
        ...
    }

    The classification answers dictionary is in the form:
    {
        "classificationHash": {
            "classificationHash": classificationHash,
            "classifications": [{answer 1}, {answer 2}, ...]
        },
        ...
    }

    ORM:

    label_hash (uid),
    data_hash (uid),
    data_title,
    data_link,
    label_status,
    labels: {
        ...
    },
    object_answers: {
        ...
    },
    classification_answers: {
        ...
    }

    """

    DB_FIELDS = OrderedDict([
        ("label_hash", str),
        ("data_hash", str),
        ("data_title", str),
        ("data_link", str),
        ("label_status", str),
        ("labels", (dict, str)),
        ("object_answers", (dict, str)),
        ("classification_answers", (dict, str)),
    ])

    NON_UPDATABLE_FIELDS = {
        "label_hash",
        "data_hash",
    }
