from __future__ import annotations

from dataclasses import dataclass
from typing import List

from encord.objects.common import (
    Attribute,
    attribute_from_dict,
    attributes_to_list_dict,
)


@dataclass
class Classification:
    uid: int
    feature_node_hash: str
    attributes: List[Attribute]

    @classmethod
    def from_dict(cls, d: dict) -> Classification:
        attributes_ret: List[Attribute] = list()
        for attribute_dict in d["attributes"]:
            attributes_ret.append(attribute_from_dict(attribute_dict))

        return Classification(
            uid=int(d["id"]),
            feature_node_hash=d["featureNodeHash"],
            attributes=attributes_ret,
        )

    def to_dict(self) -> dict:
        ret = dict()
        ret["id"] = str(self.uid)
        ret["featureNodeHash"] = self.feature_node_hash

        attributes_list = attributes_to_list_dict(self.attributes)
        if attributes_list:
            ret["attributes"] = attributes_list

        return ret
