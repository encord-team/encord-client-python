"""Build pathway selectors without resolving the workflow graph."""

from typing import Optional, Union
from uuid import UUID

from encord.orm.tasks_v3 import PathwayById, PathwayByName


def build_pathway_selector(
    pathway_id: Optional[Union[UUID, str]],
    pathway_name: Optional[str],
) -> Optional[Union[PathwayById, PathwayByName]]:
    if pathway_id is not None and pathway_name is not None:
        raise ValueError("Provide either pathway_id or pathway_name, not both.")
    if pathway_id is not None:
        return PathwayById(id=UUID(str(pathway_id)))
    if pathway_name is not None:
        if not pathway_name.strip():
            raise ValueError("pathway_name must not be blank.")
        return PathwayByName(name=pathway_name)
    return None
