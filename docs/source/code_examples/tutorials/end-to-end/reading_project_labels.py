"""
Reading project labels
======================

This example shows you how to read labels from your project.

"""
# sphinx_gallery_thumbnail_path = 'images/end-to-end-thumbs/product-data.svg'
from encord.client import EncordClientProject
from encord.orm.project import Project
from encord.user_client import EncordUserClient

#%%
# Authenticating
# --------------
# To interact with Encord, you need to authenticate a client. You can find more details
# :ref:`here <authentication:Authentication>`.

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

# Find project to work with based on title.
project: Project = next(
    (
        p["project"]
        for p in user_client.get_projects(
        title_eq="Title of project you want to list"
    )
    )
)
project_client = user_client.get_project_client(project.project_hash)

#%%
# 1. The high-level view of your labels
# -------------------------------------
# Generally, project data is grouped into label_rows, which point to individual image
# groups or videos. Each label row will have its own label status, as not all label
# rows may be annotated at a given point in time.
#
# First, we list the high-level state of each label row:


# This project instance is populated with high-level `label_row` info and ontology.
project: Project = project_client.get_project()

# Fetch one label row as an example.
for label_row in project.label_rows:
    print(label_row)
    break

#%%
# Expected output
#
# .. code-block:: python
#
#     {
#       "annotation_task_status": "<annotation_task_status>",
#       "data_hash": "<data_hash>",
#       "data_title": "<data_title>",
#       "data_type": "IMG_GROUP",  # or "VIDEO"
#       "dataset_hash": "<dataset_hash>",
#       "label_hash": "<label_hash>",  # or none
#       "label_status": "<label_status>"
#     }
#
# See :ref:`tutorials/projects:Getting label rows` for more details of possible values
# for the different attributes.

