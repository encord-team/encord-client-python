from encord.user_client import EncordUserClient
from encord.utilities.client_utilities import APIKeyScopes

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
api_key = user_client.create_project_api_key(
    "<project_hash>",
    "Example API key title",
    [
        APIKeyScopes.LABEL_READ,
        APIKeyScopes.LABEL_WRITE,
    ]
)
print(api_key)
