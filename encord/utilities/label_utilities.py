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
from encord.constants.enums import DataType
from encord.constants.string_constants import *
from encord.orm.label_row import LabelRow


def construct_answer_dictionaries(label_row):
    """
    Adds answer object and classification answer dictionaries from a label row if they do not exist.
    Integrity checks are conducted upon saving of labels.

    Args:
        label_row: A label row.

    Returns:
        LabelRow: A label row instance with updated answer dictionaries
    """
    label_row = LabelRow(label_row)  # Cast to label row ORM
    data_type = label_row.data_type
    data_units = label_row.data_units

    object_answers = label_row.object_answers
    classification_answers = label_row.classification_answers

    for du in data_units:  # Iterate over data units in label row
        data_unit = data_units[du]

        if LABELS in data_unit:
            labels = data_unit.get(LABELS)

            if data_type in {DataType.IMG_GROUP.value, DataType.IMAGE.value}:  # Go through images
                items = labels.get(OBJECTS, {}) + labels.get(CLASSIFICATIONS, {})
                add_answers_to_items(items, classification_answers, object_answers)

            elif data_type in (DataType.VIDEO.value, DataType.DICOM.value):
                for frame in labels:  # Go through frames
                    items = labels[frame].get(OBJECTS, {}) + labels[frame].get(CLASSIFICATIONS, {})
                    add_answers_to_items(items, classification_answers, object_answers)

    label_row[OBJECT_ANSWERS] = object_answers
    label_row[CLASSIFICATION_ANSWERS] = classification_answers
    return label_row


# ---------------------------------------------------------
#                   Helper functions
# ---------------------------------------------------------
def add_answers_to_items(items, classification_answers, object_answers):
    """
    If object_hash (uid) or classification_hash (uid) are not in answer dictionaries,
    add key entry with empty classification list.
    """
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
