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

# Label row constants

LABELS = "labels"
OBJECTS = "objects"
CLASSIFICATIONS = "classifications"
OBJECT_HASH = "objectHash"
CLASSIFICATION_HASH = "classificationHash"
OBJECT_ANSWERS = "object_answers"
CLASSIFICATION_ANSWERS = "classification_answers"


# Labeling algorithm names
INTERPOLATION = "interpolation"
FITTED_BOUNDING_BOX = "fitted_bounding_box"


# Type of Cord API key
TYPE_PROJECT = "project"
TYPE_DATASET = "dataset"
TYPE_ONTOLOGY = "ontology"
ALL_RESOURCE_TYPES = [TYPE_PROJECT, TYPE_DATASET, TYPE_ONTOLOGY]
