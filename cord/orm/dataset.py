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
    A dataset defines a set of videos or image groups.
    ORM in primitive types.
    """

    DB_FIELDS = OrderedDict([
        ("video_hash", str),
        ("title", str),
        ("frames_per_second", str),
        ("duration", str),
        ("file_type", str),
        ("file_size", str),
        ("dataset_hash", str),
        ("dataset_title", str),
        ("dataset_description", str),
        ("created_at", str),
        ("last_edited_at", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "video_hash",
        "title",
        "frames_per_second",
    }


class SignedURL(base_orm.BaseORM):
    """ A signed URL object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("signed_url", str),
        ("title", str),
        ("user_hash", str),
        ("video_hash", str),
        ("file_link", str),
        ("cord_type", str),
        ("storage_location", str),
    ])


class Video(base_orm.BaseORM):
    """ A Video object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("video_hash", str),
        ("user_hash", str),
        ("title", str),
        ("file_link", str),
        ("cord_type", int),
        ("storage_location", int),
    ])

    NON_UPDATABLE_FIELDS = {
        "video_hash",
        "user_hash",
    }
