from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Dict, Optional

# pylint: disable=unused-import
from encord.common.constants import DATETIME_STRING_FORMAT
from encord.objects.ontology_structure import OntologyStructure
from encord.orm.formatter import Formatter


class OntologyUserRole(IntEnum):
    ADMIN = 0
    USER = 1


class Ontology(dict, Formatter):
    def __init__(
        self,
        title: str,
        structure: OntologyStructure,
        ontology_hash: str,
        created_at: datetime,
        last_edited_at: datetime,
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
                "created_at": created_at,
                "last_edited_at": last_edited_at,
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

    @property
    def created_at(self) -> datetime:
        return self["created_at"]

    @property
    def last_edited_at(self) -> datetime:
        return self["last_edited_at"]

    @classmethod
    def from_dict(cls, json_dict: Dict) -> Ontology:
        return Ontology(
            title=json_dict["title"],
            description=json_dict["description"],
            ontology_hash=json_dict["ontology_hash"],
            structure=OntologyStructure.from_dict(json_dict["editor"]),
            created_at=json_dict["created_at"],
            last_edited_at=json_dict["last_edited_at"],
        )
