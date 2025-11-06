import prettyprinter as pp

from encord import EncordUserClient
from encord.utilities.client_utilities import CvatImporterSuccess, LocalImport

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Increase networking timeouts for this long running operation.
timeout = 1800
user_client.user_config.read_timeout = timeout
user_client.user_config.write_timeout = timeout
user_client.user_config.connect_timeout = timeout

# We have placed the unzipped Pizza Project directory into a
# `data` folder relative to this script
data_folder = "data/Pizza Project"
dataset_name = "Pizza Images Dataset"
cvat_importer_ret = user_client.create_project_from_cvat(LocalImport(file_path=data_folder), dataset_name)

# Check if the import was a success and inspect the return value
if type(cvat_importer_ret) == CvatImporterSuccess:
    print(f"project_hash = {cvat_importer_ret.project_hash}")
    print(f"dataset_hash = {cvat_importer_ret.dataset_hash}")
    pp.pprint(cvat_importer_ret.issues)
