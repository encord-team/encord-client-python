from encord.client import EncordClient
from encord.client import EncordConfig

config = EncordConfig("<resource_id>", "<resource_api_key>")
client = EncordClient.initialise_with_config(config)
