# Import dependencies
import uuid

from encord import EncordUserClient

# Authenticate with Encord using the path to your private key
user_client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path="/Users/encord/.ssh/real_dev-private-key.txt", domain="http://localhost:6969"
)

# name = user_client.get_storage_folder("5f688928-5668-4037-9b8a-daa0e09f0915").name
# print(name)
collection = user_client.get_collection("8920ba66-6660-49eb-8aac-c468acef9a03")
print(collection)

collections = user_client.get_collections(collection_hash_list=["6e63713e-0416-4c41-a52b-48cdc0753aa1"])
# print(len(collections))
# id = user_client.create_collection("6e63713d-0416-4c41-a52b-48cdc0753da1", "Types are better now", )
# user_client.delete_collection("8920ba66-6660-49eb-8aac-c468acef9a02")
# user_client.update_collection("8920ba66-6660-49eb-8aac-c468acef9a02", "Typed name wrong")
# user_client.update_collection(collections[2].collection_hash, description="Typed description")
