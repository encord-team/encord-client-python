from encord.user_client import EncordUserClient
from encord.orm.dataset import AddPrivateDataResponse
from typing import List
from encord.orm.cloud_integration import CloudIntegration

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
dataset_client = user_client.get_dataset_client(
    "<dataset_hash>"
)

# Choose integration
integrations: List[
    CloudIntegration
] = user_client.get_cloud_integrations()
print("Integration Options:")
print(integrations)

integration_idx = [i.title for i in integrations].index(
    "AWS"
)
integration = integrations[integration_idx].id

response: AddPrivateDataResponse = (
    dataset_client.add_private_data_to_dataset(
        integration, "path/to/json/file.json"
    )
)
print(response.dataset_data_list)
