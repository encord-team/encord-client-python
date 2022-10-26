from pathlib import Path

import prettyprinter as pp
from encord import EncordUserClient
from encord.utilities.client_utilities import CvatImporterSuccess, LocalImport

# adapt the following line to your private key path
private_key_path = Path.home() / ".ssh" / "id_ed25519"

with private_key_path.open() as f:
    private_key = f.read()

user_client = EncordUserClient.create_with_ssh_private_key(private_key)

# We have placed the unzipped Pizza Project directory into a
# `data` folder relative to this script
data_folder = "data/Pizza Project"
dataset_name = "Pizza Images Dataset"
cvat_importer_ret = user_client.create_project_from_cvat(
    LocalImport(file_path=data_folder), dataset_name
)

# Check if the import was a success and inspect the return value
if type(cvat_importer_ret) == CvatImporterSuccess:
    print(f"project_hash = {cvat_importer_ret.project_hash}")
    print(f"dataset_hash = {cvat_importer_ret.dataset_hash}")
    pp.pprint(cvat_importer_ret.issues)
