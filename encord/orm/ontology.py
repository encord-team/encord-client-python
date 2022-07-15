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
from __future__ import annotations

import dataclasses
import json
from collections import OrderedDict
from datetime import datetime
from enum import Enum, IntEnum
from typing import Dict, List, NoReturn, Optional

from dateutil import parser

from encord.constants.enums import DataType
from encord.objects.ontology_structure import OntologyStructure
from encord.orm import base_orm
from encord.orm.formatter import Formatter

DATETIME_STRING_FORMAT = "%Y-%m-%d %H:%M:%S"


class OntologyUserRole(IntEnum):
    ADMIN = 0
    USER = 1


class Ontology(dict, Formatter):
    def __init__(
        self,
        title: str,
        structure: OntologyStructure,
        ontology_hash: str,
        description: Optional[str] = None,
    ):
        """
        DEPRECATED - prefer using the :class:`encord.ontology.Ontology` class instead.

        This class has dict-style accessors for backwards compatibility.
        Clients who are using this class for the first time are encouraged to use the property accessors and setters
        instead of the underlying dictionary.
        The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

        WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
        datastructure.
        """
        super().__init__(
            {
                "ontology_hash": ontology_hash,
                "title": title,
                "description": description,
                "structure": structure,
            }
        )

    @property
    def ontology_hash(self) -> str:
        return self["ontology_hash"]

    @property
    def title(self) -> str:
        return self["title"]

    @title.setter
    def title(self, value: str) -> None:
        self["title"] = value

    @property
    def description(self) -> str:
        return self["description"]

    @description.setter
    def description(self, value: str) -> None:
        self["description"] = value

    @property
    def structure(self) -> OntologyStructure:
        return self["structure"]

    @structure.setter
    def structure(self, value: OntologyStructure) -> None:
        self["structure"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> Ontology:
        return Ontology(
            title=json_dict["title"],
            description=json_dict["description"],
            ontology_hash=json_dict["ontology_hash"],
            structure=OntologyStructure.from_dict(json_dict["editor"]),
        )


class CreateOntologyResponse(dict, Formatter):
    def __init__(
        self,
        title: str,
        storage_location: int,
        ontology_hash: str,
        user_hash: str,
    ):
        """
        This class has dict-style accessors for backwards compatibility.
        Clients who are using this class for the first time are encouraged to use the property accessors and setters
        instead of the underlying dictionary.
        The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

        WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
        datastructure.
        """

        super().__init__(
            {
                "title": title,
                "type": storage_location,
                "ontology_hash": dataset_hash,
                "user_hash": user_hash,
            }
        )

    @property
    def title(self) -> str:
        return self["title"]

    @title.setter
    def title(self, value: str) -> None:
        self["title"] = value

    @property
    def storage_location(self) -> StorageLocation:
        return StorageLocation(self["type"])

    @storage_location.setter
    def storage_location(self, value: StorageLocation) -> None:
        self["type"] = value.value

    @property
    def dataset_hash(self) -> str:
        return self["dataset_hash"]

    @dataset_hash.setter
    def dataset_hash(self, value: str) -> None:
        self["dataset_hash"] = value

    @property
    def user_hash(self) -> str:
        return self["user_hash"]

    @user_hash.setter
    def user_hash(self, value: str) -> None:
        self["user_hash"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> CreateDatasetResponse:
        return CreateDatasetResponse(
            title=json_dict["title"],
            storage_location=json_dict["type"],
            dataset_hash=json_dict["dataset_hash"],
            user_hash=json_dict["user_hash"],
        )
