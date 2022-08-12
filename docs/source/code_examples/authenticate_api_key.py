from types import Union

from encord.client import EncordClient, EncordClientDataset, EncordClientProject

# The client will either be an EncordClientDataset if the
# resource_id belongs to a dataset or it will be an
# EncordClientProject if the resource_id belongs to a project.
client: Union[
    EncordClientProject, EncordClientDataset
] = EncordClient.initialise("<resource_id>", "<resource_api_key>")
