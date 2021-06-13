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


class Dataset(base_orm.BaseORM):
    """
    A dataset is a collection of data rows.

    ORM:

    title,
    description,
    dataset_type (Cord storage vs. AWS/GCP/Azure),
    data_rows: [
        {
            data_hash (uid),
            data_title,
            data_type,
        }
    ]

    """

    DB_FIELDS = OrderedDict([
        ("title", str),
        ("description", str),
        ("dataset_type", str),
        ("data_rows", (list, str))
    ])

    NON_UPDATABLE_FIELDS = {
        "dataset_type",
    }


class SignedVideoURL(base_orm.BaseORM):
    """ A signed URL object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("signed_url", str),
        ("data_hash", str),
        ("title", str),
        ("file_link", str)
    ])


class SignedImageURL(base_orm.BaseORM):
    """ A signed URL object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("signed_url", str),
        ("data_hash", str),
        ("title", str),
        ("file_link", str)
    ])


class SignedImagesURL(base_orm.BaseListORM):
    """ A signed URL object with supporting information. """
    BASE_ORM_TYPE = SignedImageURL


class Video(base_orm.BaseORM):
    """ A video object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("title", str),
        ("file_link", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


class ImageGroup(base_orm.BaseORM):
    """ An image group object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("title", str),
        ("file_link", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


class Image(base_orm.BaseORM):
    """ An image object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("title", str),
        ("file_link", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }
