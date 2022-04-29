from encord.user_client import EncordUserClient
from encord.orm.dataset import DatasetType

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
dataset = user_client.create_dataset(
    "Traffic Data", DatasetType.AWS
)
print(dataset)
