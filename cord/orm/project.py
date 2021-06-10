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


class Project(base_orm.BaseORM):
    """
    A project defines a label ontology and is a collection of datasets and label rows.

    ORM:

    title,
    description,
    editor_ontology,
    datasets: [
       {
            dataset_hash (uid),
            title,
            description,
            dataset_type (internal vs. AWS/GCP/Azure),
       },
       ...
    ],
    label_rows: [
        {
            label_hash (uid),
            data_hash (uid),
            dataset_hash (uid),
            dataset_title,
            data_title,
            data_type,
            label_status
        },
        ...
    ]

    """

    DB_FIELDS = OrderedDict([
        ("title", str),
        ("description", str),
        ("editor_ontology", (dict, str)),
        ("datasets", (list, str)),
        ("label_rows", (list, str)),
    ])

    NON_UPDATABLE_FIELDS = {
        "editor_ontology",
        "datasets",
        "label_rows"
    }

    def get_labels_list(self):
        """
        Returns a list of all label row IDs (label_hash uid) in a project.
        """
        labels = self.to_dic().get('label_rows')
        res = []
        for label in labels:
            res.append(label.get('label_hash'))
        return res
