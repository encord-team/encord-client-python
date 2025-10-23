from encord._version import __version__
from encord.dataset import Dataset
from encord.project import Project
from encord.user_client import EncordUserClient

# Make Pyright happy
__all__ = ["EncordUserClient", "Project", "Dataset", "__version__"]
