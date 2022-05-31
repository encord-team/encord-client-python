from typing import List

from encord import DatasetManager, EncordUserClient
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import AddPrivateDataResponse

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
dataset_manager: DatasetManager = user_client.get_dataset_manager("<dataset_hash>")

# Choose integration
integrations: List[CloudIntegration] = user_client.get_cloud_integrations()
print("Integration Options:")
print(integrations)

integration_idx: int = [i.title for i in integrations].index("AWS")
integration: str = integrations[integration_idx].id

response: AddPrivateDataResponse = dataset_manager.add_private_data_to_dataset(integration, "path/to/json/file.json")
print(response.dataset_data_list)
