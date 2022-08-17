from typing import List, Set

from encord.orm.model import ModelConfiguration


def get_all_model_iteration_uids(model_configurations: List[ModelConfiguration]) -> Set[str]:
    """A convenience function that works well with :meth:`encord.project.Project.list_models`"""
    model_iteration_uids = set()
    for model_configuration in model_configurations:
        model_iteration_uids.update(model_configuration.model_iteration_uids)
    return model_iteration_uids
