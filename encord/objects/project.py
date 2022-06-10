from dataclasses import dataclass
from typing import List


@dataclass
class ProjectDataset:
    dataset_hash: str
    title: str
    description: str

    @staticmethod
    def from_dict(d: dict) -> "ProjectDataset":
        return ProjectDataset(
            dataset_hash=d["dataset_hash"],
            title=d["title"],
            description=d["description"],
        )

    @classmethod
    def from_list(cls, l: list) -> List["ProjectDataset"]:
        ret = []
        for i in l:
            ret.append(cls.from_dict(i))
        return ret
