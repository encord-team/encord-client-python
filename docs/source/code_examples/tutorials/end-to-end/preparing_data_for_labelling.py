"""
Preparing your data for labelling
=================================

This example shows you how to go from your raw data to a project with your label
structure (ontology) defined, your dataset attached, and ready to be labelled.

Imports
--------------
"""
from pathlib import Path

from encord.client import EncordClientDataset
from encord.orm.dataset import (
    CreateDatasetResponse,
    DataRow,
    Dataset,
    StorageLocation,
)
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.user_client import EncordUserClient

#%%
# Authenticating
# --------------
# To interact with Encord, you need to authenticate a client. You can find more details
# :ref:`here <authentication:Authentication>`.

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

#%%
# 1. Creating and populating the dataset
# --------------------------------------
# This section shows how to create a dataset and add both videos and images to the
# dataset.

# Create the dataset
dataset_response: CreateDatasetResponse = user_client.create_dataset(
    "Example Title", StorageLocation.CORD_STORAGE
)
dataset_hash = dataset_response.dataset_hash

# Add data to the dataset
dataset_client: EncordClientDataset = user_client.get_dataset_client(
    dataset_hash
)

image_files = sorted(
    [
        p.as_posix()
        for p in Path("path/to/images").iterdir()
        if p.suffix in {".jpg", ".png"}
    ]
)
dataset_client.create_image_group(image_files)

video_files = [
    p.as_posix()
    for p in Path("path/to/videos").iterdir()
    if p.suffix in {".mp4", ".webm"}
]

for v in video_files:
    dataset_client.upload_video(v)


#%%
# 2. Listing available data in the dataset
# ----------------------------------------
# In the following part, we list the data available in the dataset.

dataset: Dataset = dataset_client.get_dataset()
for data_row in dataset.data_rows:
    print(
        f"data-hash: '{data_row.uid}', "
        f"data-type: {data_row.data_type}, "
        f"title: '{data_row.title}'"
        f"created at: '{data_row.created_at}'"
    )

#%%
# 3. Preparing a project for annotations
# --------------------------------------
# For a project to be ready for your annotators to start annotating data, you need to
# first create the project and then add objects and/or classifications to the project
# ontology.

# == Creating project, including the dataset created above == #
project_hash = user_client.create_project(
    project_title="The title of the project",
    dataset_hashes=[dataset_hash],
    project_description="A description of what this project is all about.",
)

# == Adding objects and classifications to the project ontology == #
project_client = user_client.get_project_client(project_hash)

# Objects
project_client.add_object(name="Cat", shape=ObjectShape.POLYGON)
project_client.add_object(name="Dog", shape=ObjectShape.BOUNDING_BOX)
project_client.add_object(name="Snake", shape=ObjectShape.POLYLINE)
project_client.add_object(name="Fly", shape=ObjectShape.KEY_POINT)

# Classifications
project_client.add_classification(
    name="Some example text",
    classification_type=ClassificationType.TEXT,
    required=False,
    # Note no `options` defined for text classifications.
)
project_client.add_classification(
    name="Is outdoor",
    classification_type=ClassificationType.RADIO,
    required=True,
    options=["Yes", "No"],
)
project_client.add_classification(
    name="Accessories",
    classification_type=ClassificationType.CHECKLIST,
    required=False,
    options=["Leash", "Blanket", "Harness"],
)

#%%
# At this point, your data is ready to be annotated with the project-specific
# information defined in the project ontology.
