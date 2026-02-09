from encord._version import __version__
from encord.analytics import TaskAction, TaskActionType
from encord.dataset import Dataset
from encord.project import Project
from encord.user_client import EncordUserClient

# Make Pyright happy
__all__ = ["Dataset", "EncordUserClient", "Project", "TaskAction", "TaskActionType", "__version__"]
