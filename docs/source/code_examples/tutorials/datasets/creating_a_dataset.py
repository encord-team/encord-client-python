from encord.orm.dataset import StorageLocation
from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
dataset = user_client.create_dataset(
    "Traffic Data", StorageLocation.AWS
)
print(dataset)
