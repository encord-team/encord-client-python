"""
Working with the LabelRowV2
===========================

DENIS: probably the code links not working will be the blocker for me using this tool.

The :class:`encord.objects.LabelRowV2` class is a wrapper around the Encord label row data format. It
provides a convenient way to read, create, and manipulate labels.

This is just an illustrative example.

.. figure:: /images/cvat_project_export.png

    Export Project.

"""

#%%
# Imports and authentication
# --------------------------
# First, import dependencies and authenticate a project manager.
from pathlib import Path
from typing import List

from encord import EncordUserClient, Project
from encord.objects import LabelRowV2, Object, ObjectInstance, OntologyStructure
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.orm.project import Project as OrmProject

#%%
# .. note::
#
#   To interact with Encord, you need to authenticate a client. You can find more details
#   :ref:`here <authentication:User authentication>`.
#

# Authentication: adapt the following line to your private key path
private_key_path = Path.home() / ".ssh" / "id_ed25519"

with private_key_path.open() as f:
    private_key = f.read()

user_client = EncordUserClient.create_with_ssh_private_key(private_key)

# Find project to work with based on title.
project_orm: OrmProject = next((p["project"] for p in user_client.get_projects(title_eq="Your project name")))
project: Project = user_client.get_project(project_orm.project_hash)


#%%
# Get metadata around labels
# ------------------------------
#
# Sometimes you might want to inspect some metadata around the label rows, such as the label hash,
# when the label was created, the corresponding data hash, or the creation date of the label.

label_rows: List[LabelRowV2] = project.list_label_rows_v2()


for label_row in label_rows:
    print(f"Label hash: {label_row.label_hash}")
    print(f"Label created at: {label_row.created_at}")
    print(f"Annotation task status: {label_row.annotation_task_status}")

#%%
# Inspect the filters in :meth:`~encord.project.Project.list_label_rows_v2` to only get a subset of the label rows.
#
# You can find more examples around all the available read properties by inspecting the properties of the
# :class:`~encord.objects.LabelRowV2` class.
#
# Starting to read or write labels
# --------------------------------
#
# To start reading or writing labels, you need to call the :meth:`~encord.objects.LabelRowV2.initialise_labelling`
# method which will download the state of the label from the Encord server.
#
# Once this method has been called, you can create your first label.
# DENIS: think of creating a screenshot from the platform here.

first_label_row: LabelRowV2 = label_rows[0]

first_label_row.initialise_labelling()
# ^ Check the reference for possible arguments

# Once you have added new labels, you will need to call .save() to upload all labels to the server.
first_label_row.save()

#%%
# Creating/reading object instances
# ---------------------------------
# The :class:`encord.objects.LabelRowV2` class works with its corresponding ontology. If you add object instances
# or classification instances, these will be created from the ontology.
#
# Defining the ontology object
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
ontology_structure: OntologyStructure = first_label_row.ontology_structure
box_ontology_object: Object = ontology_structure.get_item_by_title(title="Box of a human", type_=Object)
# ^ optionally specify the `type_` to narrow the return type and also have a runtime check.

# %%
# Creating and saving an object instance
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#

box_object_instance: ObjectInstance = box_ontology_object.create_instance()

box_object_instance.set_for_frames(
    coordinates=BoundingBoxCoordinates(
        height=0.5,
        width=0.5,
        top_left_x=0.2,
        top_left_y=0.2,
    ),
    # Add the bounding box for the first frame
    frames=0,
)

# Link the object instance to the label row.
first_label_row.add_object_instance(box_object_instance)


first_label_row.save()  # Upload the label to the server

#%%
# Inspecting an object instance
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# You can now get all the object instances that are part of the label row.

# Check the optional filters for when you have many different object/classification instances.
all_object_instances: List[ObjectInstance] = first_label_row.get_object_instances()

assert all_object_instances[0] == box_object_instance

#%%
# Frame views of labels
# ^^^^^^^^^^^^^^^^^^^^^
#
# Using a per frame view of the label row to read/write the labels is also possible and can be convenient.
#
#

box_object_instance_copy: ObjectInstance = box_object_instance.copy()

frame_view: LabelRowV2.FrameView = first_label_row.get_frame_view(0)
# DENIS: TODO: this part maybe needs an API rethink.
