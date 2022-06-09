"""
Reading project labels
======================

Use this script to read labels from your Encord project.

Imports and authentication
--------------------------
"""

# sphinx_gallery_thumbnail_path = 'images/end-to-end-thumbs/product-data.svg'
from dataclasses import dataclass
from functools import partial
from typing import Callable, Generator, List, Optional

from encord import EncordUserClient, ProjectManager
from encord.orm.project import Project
from encord.project_ontology.object_type import ObjectShape

#%%
# To interact with Encord, you need to authenticate a client. You can find more details
# :ref:`here <authentication:Authentication>`.

# Authenticate
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

# Find project to work with based on title.
project: Project = next((p["project"] for p in user_client.get_projects(title_eq="The title of the project")))
project_manager: ProjectManager = user_client.get_project_manager(project.project_hash)

# %%
# 1. The high-level view of your labels
# -------------------------------------
# Project data is grouped into label_rows, which point to individual image groups or
# videos. Each label row will have its own label status, as not all label rows may be
# annotated at a given point in time.
#
# Here is an example of listing the label status of a label row:

project: Project = project_manager.get_project()

# Fetch one label row as an example.
for label_row in project.label_rows:
    print(label_row)
    break

# %%
# Expected output:
#
# .. code-block::
#
#     {
#        "label_hash": "<label_hash>",  # or None
#        "data_hash": "<data_hash>",
#        "dataset_hash": "<dataset_hash>",
#        "data_title": "<data_title>",
#        "data_type": "IMG_GROUP",  # or VIDEO
#        "label_status": "NOT_LABELLED",
#        "annotation_task_status": "ASSIGNED"
#     }
#
# From the high-level data, you can, for example, compute some statistics of the
# progress of your annotators:

status_counts = {}
for label_row in project.label_rows:
    status = label_row["annotation_task_status"]
    status_counts[status] = status_counts.setdefault(status, 0) + 1
print(status_counts)

# %%
# Expected output:
#
# .. code-block::
#
#     {'RETURNED': 1, 'COMPLETED': 3, 'QUEUED': 20, 'IN_REVIEW': 3, 'ASSIGNED': 1}
#
# 2. Getting all label details
# ----------------------------
# The actual labels in the label rows are fetched by
# :class:`.EncordClientProject.get_label_row()`. This function will return a nested
# dictionary structure, with all details about classifications as well as objects.
# In this section, we show how to build a list of all bounding boxes that have been
# reviewed and marked as approved.
#
# First, we define a data class to hold the information of interest.


@dataclass(frozen=True)
class AnnotationObject:
    object: dict
    file_name: str
    data_url: str
    frame: Optional[int] = None


#%%
# Then we define a function which iterates over all objects of a label row fetched with
# :class:`.EncordClientProject.get_label_row()`. The function has a callable argument
# used to filter which objects should be returned.


def iterate_over_objects(
    label_row_details,
    include_object_fn: Callable[[dict], bool],
) -> Generator[AnnotationObject, None, None]:
    """
    Iterate over objects in a label row.

    :param label_row: the detailed label row to fetch objects from
    :param include_object_fn: A callable indicating whether to include an object.
    :return: Yields AnnotationObjects.
    """
    if label_row["data_type"] == "IMG_GROUP":
        # Image groups have multiple data_units (one for each image)
        for data_unit in label_row_details["data_units"].values():
            url = data_unit["data_link"]
            file_name = data_unit["data_title"]
            objects = data_unit["labels"]["objects"]
            for object in objects:
                if include_object_fn(object):
                    yield AnnotationObject(object, file_name, url)

    else:
        # Videos have a single data unit, but multiple frames.
        # Need to iterate through frames instead.
        data_unit = list(label_row_details["data_units"].values())[0]

        url = data_unit["data_link"]
        file_name = data_unit["data_title"]
        for frame, labels in data_unit["labels"].items():
            for object in labels["objects"]:
                if include_object_fn(object):
                    yield AnnotationObject(object, file_name, url, frame)


#%%
# Then we can define a function, which is used to choose which objects to include.


def include_object_fn_base(
    object: dict,
    object_type: Optional[ObjectShape] = None,
    only_approved: bool = True,
):
    # Filter object type
    if object_type and object["shape"].lower() != object_type.value.lower():
        return False

    # Filter reviewed status
    if only_approved and not object["reviews"] or not object["reviews"][-1]["approved"]:
        return False

    return True


# Trick to preselect object_type
include_object_fn_bbox: Callable[[dict], bool] = partial(include_object_fn_base, object_type=ObjectShape.BOUNDING_BOX)

#%%
# Now we can use the iterator and the filter to collect the objects.

reviewed_bounding_boxes: List[AnnotationObject] = []
for label_row in project.label_rows:
    if not label_row["label_hash"]:  # No objects in this label row yet.
        continue

    label_row_details = project_client.get_label_row(label_row["label_hash"])
    reviewed_bounding_boxes += list(iterate_over_objects(label_row_details, include_object_fn_bbox))

print(reviewed_bounding_boxes)


# %%
# Expected output:
#
# .. code-block:: python
#
#     [
#         AnnotationObject(
#             object={
#                 "name": "Name of the object annotated",
#                 "color": "#FE9200",
#                 "shape": "bounding_box",
#                 "value": "name_of_the_object_annotated",
#                 "createdAt": "Wed, 18 May 2022 14:07:14 GMT",
#                 "createdBy": "annotator1@your.domain",
#                 "confidence": 1,
#                 "objectHash": "<object_hash>",
#                 "featureHash": "<feature_hash>",
#                 "manualAnnotation": True,
#                 "boundingBox": {
#                     "h": 0.8427,
#                     "w": 0.5857,
#                     "x": 0.3134,
#                     "y": 0.1059,
#                 },
#                 "reviews": [
#                     {
#                         "exists": True,
#                         "comment": None,
#                         "approved": True,
#                         "instance": {
#                             "name": "nested_classifications",
#                             "range": [[0, 0]],
#                             "shape": "bounding_box",
#                             "objectHash": "<object_hash>",
#                             "featureHash": "<feature_hash>",
#                             "classifications": [],
#                         },
#                         "createdAt": "Wed, 18 May 2022 14:07:42 GMT",
#                         "createdBy": "reviewer1@your.domain",
#                         "rejections": None,
#                     }
#                 ],
#             },
#             file_name="your_file_name.jpg",
#             frame=None,  # or a number if video annotation,
#             data_url="<signed_link_to_data>",
#         )
#         # ...
#     ]
#
# From this template, it is possible to extract various subsets of objects by changing
# arguments to the ``include_object_fn_base``. For example, getting all polygons is done
# by changing the ``object_type`` argument to :class:`.ObjectShape.POLYGON`.
# Similarly, you can define your own filtering function to replace
# ``include_object_fn_base`` to select only the objects that you need for your purpose.
# Finally, if you want to get classifications rather than objects, you will have to
# change the ``"objects"`` dictionary lookups (line 129 and 141) to
# ``"classifications"`` and compose a new filtering function.
#
# 3. Fetching nested classifications
# ----------------------------------
# It is possible to make nested classifications on objects. The information about such
# nested classifications is stored in the ``classification_answers``, ``object_answers``
# and ``object_actions`` sections of the ``label_row_details``.
#
# Assuming that the reviewed bounding boxes fetched above have nested attributes, the
# following code example shows how to get the nested classification information.

print(label_row_details["object_answers"][reviewed_bounding_boxes[-1].object["objectHash"]])

# %%
# Expected output:
#
# .. code-block::
#
#     Expected output:
#     {
#         'classifications': [
#             {
#                 'answers':
#                     [
#                         {
#                             'featureHash': '<nested_feature_hash2>',
#                             'name': 'nested option 1',
#                             'value': 'nested_option_1'
#                         }
#                     ],
#                 'featureHash': '<nested_feature_hash>',
#                 'manualAnnotation': True,
#                 'name': 'Nested classification.',
#                 'value': 'nested_classification.'
#             }
#         ],
#         'objectHash': 'e413a414'
#     }
#
