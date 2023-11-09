from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ProjectDataset:
    dataset_hash: str
    title: str
    description: str

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> ProjectDataset:
        return ProjectDataset(
            dataset_hash=d["dataset_hash"],
            title=d["title"],
            description=d["description"],
        )

    @classmethod
    def from_list(cls, dataset_list: List[Dict[str, Any]]) -> List[ProjectDataset]:
        return [cls.from_dict(i) for i in dataset_list]
