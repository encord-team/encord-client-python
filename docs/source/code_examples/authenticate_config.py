from encord.client import EncordClient, EncordConfig

config = EncordConfig("<resource_id>", "<resource_api_key>")
client = EncordClient.initialise_with_config(config)
