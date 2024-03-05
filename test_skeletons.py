# %%
%load_ext autoreload
%autoreload 2
import os
import encord
from encord import EncordUserClient
from encord.utilities.project_user import ProjectUserRole

# %%
client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=os.environ["ENCORD_SSH_KEY"], domain="localhost:6969"
)
client.get_projects()
SKELETON_PROJECT_HASH = "2a757614-52ce-4153-ab38-85f85b00df7f"
project = client.get_project("2a757614-52ce-4153-ab38-85f85b00df7f")
# %%
