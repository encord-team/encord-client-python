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

from cord.orm.label_blurb import Label
from cord.utils.str_constants import *


def construct_answer_dictionaries(label):
    """
    Adds answer object and classification answer dictionaries from a blurb if they do not exist.
    Integrity checks are conducted upon saving of labels.

    Args:
        label: A label blurb.

    Returns:
        Label: A label blurb instance with updated answer dictionaries
    """
    label = Label(label)  # Cast to Label ORM
    labels = label.labels

    if OBJECT_ANSWERS in label:
        object_answers = label.object_answers
    else:
        object_answers = {}

    if CLASSIFICATION_ANSWERS in label:
        classification_answers = label.classification_answers
    else:
        classification_answers = {}

    for frame in labels:
        items = labels[frame].get(OBJECTS) + labels[frame].get(CLASSIFICATIONS)

        for item in items:
            if OBJECT_HASH in item:
                object_hash = item.get(OBJECT_HASH)
                if object_hash not in object_answers:
                    object_answers[object_hash] = {
                        OBJECT_HASH: object_hash,
                        CLASSIFICATIONS: [],
                    }

            if CLASSIFICATION_HASH in item:
                classification_hash = item.get(CLASSIFICATION_HASH)
                if classification_hash not in classification_answers:
                    classification_answers[classification_hash] = {
                        CLASSIFICATION_HASH: classification_hash,
                        CLASSIFICATIONS: [],
                    }

    label[OBJECT_ANSWERS] = object_answers
    label[CLASSIFICATION_ANSWERS] = classification_answers
    return label
