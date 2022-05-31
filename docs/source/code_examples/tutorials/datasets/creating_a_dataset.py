from encord import EncordUserClient
from encord.orm.dataset import CreateDatasetResponse, StorageLocation

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

dataset: CreateDatasetResponse = user_client.create_dataset("Example Title", StorageLocation.AWS)
print(dataset)
