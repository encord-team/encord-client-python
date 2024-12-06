"""
---
title: "Objects - HTML Node"
slug: "sdk-ref-objects-html-node"
hidden: false
metadata:
  title: "Objects - HTML Node"
  description: "Encord SDK Objects - HTML Node."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, List, Union, cast

from encord.orm.base_dto import BaseDTO


class HtmlNode(BaseDTO):
    """
    A class representing a single HTML node, with the node and offset.

    Attributes:
        node (str): The xpath of the node
        offset (int): The offset of the content from the xpath
    """

    node: str
    offset: int

    def __repr__(self):
        return f"(Node: {self.node} Offset: {self.offset})"


class HtmlRange(BaseDTO):
    """
    A class representing a section of HTML with a start and end node.

    Attributes:
        start (HtmlNode): The starting node of the range.
        end (HtmlNode): The ending node of the range.
    """

    start: HtmlNode
    end: HtmlNode

    def __repr__(self):
        return f"({self.start} - {self.end})"

    def to_dict(self):
        return {
            "start": {"node": self.start.node, "offset": self.start.offset},
            "end": {"node": self.end.node, "offset": self.end.offset},
        }

    def __hash__(self):
        return hash(self.__repr__())

    @classmethod
    def from_dict(cls, d: dict):
        return HtmlRange(
            start=HtmlNode(node=d["start"]["node"], offset=d["start"]["offset"]),
            end=HtmlNode(node=d["end"]["node"], offset=d["end"]["offset"]),
        )


HtmlRanges = List[HtmlRange]
