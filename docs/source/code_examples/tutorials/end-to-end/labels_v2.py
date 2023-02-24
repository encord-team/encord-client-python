"""
Working with the LabelRowV2
===========================

The :class:`encord.objects.LabelRowV2` class is a wrapper around the Encord label row data format. It
provides a convenient way to read, create, and manipulate labels.

"""

#%%
# Imports and authentication
# --------------------------
# First, import dependencies and authenticate a project manager.
from pathlib import Path

from encord import EncordUserClient, Project
from encord.orm.project import Project as OrmProject
from encord.utilities.label_utilities import construct_answer_dictionaries

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

ontology = project.ontology

#%%
# Saving objects
# --------------
#
# To save labels to Encord, you take two steps.
#
# 1. Define a map between your local object type identifiers and Encord ontology
#    objects.
# 2. Add objects to Encord label rows
#
# 1. Defining object mapping
# ^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# You need a way to map between your local object identifiers and the objects from the
# Encord ontology. The mapping in this example is based on the ontology names that
# were defined when :ref:`tutorials/projects:Adding components to a project ontology`.
# You find the Encord ontology object names with the following lines of code::
#
#     ontology = project.get_project()["editor_ontology"]
#     for obj in ontology["objects"]:
#         print(f"Type: {obj['shape']:15s} Name: {obj['name']}")
#
# The code will print something similar to this:
#
# .. code:: text
#
#     Type: polygon         Name: Dog (polygon)
#     Type: polyline        Name: Snake (polyline)
#     Type: bounding_box    Name: Tiger (bounding_box)
#     Type: point           Name: Ant (key-point)
#

#%%
# Below, is an example of how to define your own mapping between your local object
# identifiers and Encord ontology objects. Note that the keys in the dictionary could
# be any type of keys. So if your local object types are defined by integers, for
# example, you can use integers as keys.

LOCAL_TO_ENCORD_NAMES = {
    # local object identifier: Encord object name
    "Dog": "Dog (polygon)",
    "Snake": "Snake (polyline)",
    "Tiger": "Tiger (bounding_box)",
    "Ant": "Ant (key-point)",
}

local_to_encord_ont_objects = {k: find_ontology_object(ontology, v) for k, v in LOCAL_TO_ENCORD_NAMES.items()}

#%%
# 2. Saving objects to Encord
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# As the structure of label rows depends on the type of data in the label row, there
# are separate workflows for videos and image groups.
#
# **Saving objects to label rows with videos**
#
# Suppose you have the following local data that you want to save to Encord.

# A list of objects to save to Encord.
local_objects = [
    {
        "frame": 0,
        "objects": [
            {  # Polygon
                "type": "Dog",  # The local object type identifier
                # The data of the object
                "data": [[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2]],
                # If the object is present in multiple images, specify a unique id
                # across frames here
                "track_id": 0,
            },
            {  # Polyline
                "type": "Snake",
                "data": [[0.3, 0.3], [0.4, 0.3], [0.4, 0.4], [0.3, 0.4]],
                "track_id": 1,
            },
        ],
    },
    {
        "frame": 3,
        "objects": [
            {  # Polyline
                "type": "Snake",
                "data": [[0.4, 0.4], [0.5, 0.4], [0.5, 0.5], [0.4, 0.5]],
                "track_id": 1,
            },
            {  # Bounding box
                "type": "Tiger",
                "data": {"x": 0.7, "y": 0.7, "w": 0.2, "h": 0.2},
                "track_id": 2,
            },
            {  # Key-point
                "type": "Ant",
                "data": [0.3, 0.3],
                "track_id": 1,
            },
        ],
    },
    # ...
]

#%%
# The data is saved by the following code example.

# Title of video to which the local objects are associated
video_name = "example_video.mp4"

# Find the label row corresponding to the video associated with the local objects.
label_row: dict = next((lr for lr in project.label_rows if lr["data_title"] == video_name))

# Create or fetch details of the label row from Encord.
if label_row["label_hash"] is None:
    label_row: dict = project.create_label_row(label_row["data_hash"])
else:
    label_row: dict = project.get_label_row(label_row["label_hash"])

# Videos only have one data unit, so fetch the labels of that data unit.
encord_labels: dict = next((du for du in label_row["data_units"].values()))["labels"]

# Collection of Encord object_hashes to allow track_ids to persist across frames.
object_hash_idx: Dict[int, str] = {}

for local_frame_level_objects in local_objects:
    frame: int = local_frame_level_objects["frame"]

    # Note that we will append to list of existing objects in the label row.
    encord_frame_labels: dict = encord_labels.setdefault(str(frame), {"objects": [], "classifications": []})
    # Uncomment this line if you want to overwrite the objects on the platform
    # encord_frame_labels["objects"] = []

    for local_class in local_frame_level_objects["objects"]:
        local_obj_type: str = local_class["type"]
        encord_obj_type: dict = local_to_encord_ont_objects[local_obj_type]

        track_id = local_class.get("track_id")
        object_hash: Optional[str] = object_hash_idx.get(track_id)

        # Construct Encord object dictionary
        encord_object: dict = make_object_dict(encord_obj_type, local_class["data"], object_hash=object_hash)
        # Add to existing objects in this frame.
        encord_frame_labels["objects"].append(encord_object)

        # Remember object hash for next time.
        object_hash_idx.setdefault(track_id, encord_object["objectHash"])

# NB: This call is important to maintain a valid label_row structure!
label_row = construct_answer_dictionaries(label_row)
project.save_label_row(label_row["label_hash"], label_row)

#%%
# **Saving objects to label rows with image groups**
#
# Suppose you have the following local data that you want to save to Encord.

# A list of local objects to save to Encord.
local_objects = {
    # Local image name
    "000001.jpg": [
        {  # Polygon
            "type": "Dog",  # The local object type identifier
            # The data of the object
            "data": [[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2]],
            # If the object is present in multiple images, specify a unique id
            # across frames here
            "track_id": 0,
        },
        {  # Polyline
            "type": "Snake",
            "data": [[0.3, 0.3], [0.4, 0.3], [0.4, 0.4], [0.3, 0.4]],
            "track_id": 1,
        },
    ],
    "000002.jpg": [
        {  # Polyline
            "type": "Snake",
            "data": [[0.4, 0.4], [0.5, 0.4], [0.5, 0.5], [0.4, 0.5]],
            "track_id": 1,
        },
        {  # Bounding box
            "type": "Tiger",
            "data": {"x": 0.7, "y": 0.7, "w": 0.2, "h": 0.2},
            "track_id": 2,
        },
        {  # Key-point
            "name": "Ant",
            "data": [0.3, 0.3],
        },
    ],
    # ...
}

#%%
# The data is saved by the following code example.

# Take any label row, which contains images with names from `local_objects`.
label_row = project.label_rows[0]

# Create or fetch details of the label row.
if label_row["label_hash"] is None:
    label_row = project.create_label_row(label_row["data_hash"])
else:
    label_row = project.get_label_row(label_row["label_hash"])

# Collection of Encord object_hashes to allow track_ids to persist across frames.
object_hash_idx: Dict[int, str] = {}

# Image groups a variable number of data units so iterate over those.
for encord_data_unit in label_row["data_units"].values():
    if encord_data_unit["data_title"] not in local_objects:
        continue  # No match for this data unit.

    # Note: The following line will append objects to the list of existing objects on
    # the Encord platform. To overwrite, existing objects, uncomment this:
    # encord_data_unit["labels"] = {"objects": [], "classifications": []}
    encord_labels: dict = encord_data_unit["labels"]

    for local_class in local_objects[encord_data_unit["data_title"]]:
        local_obj_type: str = local_class["type"]
        encord_obj_type: dict = local_to_encord_ont_objects[local_obj_type]
        track_id = local_class.get("track_id")
        object_hash: Optional[str] = object_hash_idx.get(track_id)

        # Construct Encord object dictionary
        encord_object: dict = make_object_dict(encord_obj_type, local_class["data"], object_hash=object_hash)
        # Add to existing objects in this frame.
        encord_labels["objects"].append(encord_object)

        # Remember object hash for other data units in the image group.
        object_hash_idx.setdefault(track_id, encord_object["objectHash"])

# NB: This call is important to maintain a valid label_row structure!
label_row = construct_answer_dictionaries(label_row)
project.save_label_row(label_row["label_hash"], label_row)


#%%
# Saving classifications
# ----------------------
# The workflow is very similar for classifications. Much of the code will be
# identical to that above, but with slight modifications, highlighted with ``# NEW``.
# The steps are:
#
# 1. Define a classification identifier map.
#
#    1. For top-level classifications
#    2. *additional step*: map classification options.
#
# 2. Add classifications to frames or data units for videos and image groups,
#    respectively.
#
#    1. Add classification to ``labels`` dictionaries.
#    2. *additional step*: Add option to the label row's ``classification_answers``.
#
# 1. Defining classification mapping
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# To define the mapping, you need to know the names of the ontology classifications
# and their associated options.
# Use the following code snippet to list the names of the Encord classifications and
# their options::
#
#     ontology = projet_manager.get_project()["editor_ontology"]
#     for classification in ontology["classifications"]:
#         for att in classification["attributes"]:
#             options = (
#                 "No options for text"
#                 if att["type"] == "text"
#                 else [o["label"] for o in att["options"]]
#             )
#             print(f"Type: {att['type']:9s} Name: {att['name']:20s} options: {options}")
#
# This will produce an output similar to the following:
#
# .. code:: text
#
#     Type: radio     Name: Has Animal (radio)        options: ['yes', 'no']
#     Type: checklist Name: Other objects (checklist) options: ['person', 'car', 'leash'],
#     Type: text      Name: Description (text)        options: No options for text
#
# Below, is an example of how to define your own mapping between your "local"
# classification identifiers and Encord classifications.

LOCAL_TO_ENCORD_NAMES: dict = {  # NEW
    # Local classification identifier
    "has_animal": {
        # Encord classification name
        "name": "Has Animal (radio)",
        # Tuples of ("local option identifier", "encord option name")
        "options": [(1, "yes"), (0, "no")],
    },
    "other_objects": {
        "name": "Other objects (checklist)",
        "options": [(0, "person"), (1, "car"), (2, "leash")],
    },
    "description": {
        "name": "Description (text)",
        # No options for text
    },
}

local_to_encord_ont_classifications = {  # NEW
    k: find_ontology_classification(ontology, v) for k, v in LOCAL_TO_ENCORD_NAMES.items()
}

#%%
# 2. Saving classifications to Encord
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# As the structure of label rows depends on the type of data in the label row, there are
# separate workflows for videos and image groups.
#
# **Saving classifications to label rows with videos**
#
# Suppose you have the following local data that you want to save to Encord.

local_classifications = [  # NEW
    {
        "frame": 0,
        "classifications": [
            {  # Radio type classicifation
                "type": "has_animal",  # The local object type identifier
                # The data of the object
                "data": 0,
                # If the _same_ classification is present across multiple images,
                # specify a unique id across frames here
                "track_id": 0,
            },
            {  # Checklist type classification
                "type": "other_objects",
                "data": [
                    1,
                    2,
                ],  # Choose both car (local id 1) and leash (local id 2)
            },
            {  # Text type classification
                "type": "description",
                "data": "Your description of the frame",
            },
        ],
    },
    {
        "frame": 1,
        "classifications": [
            {
                "type": "has_animal",
                "data": 0,
                "track_id": 0,
            },
        ],
    },
    # ...
]

#%%
# The data is saved by the following code example.

# Title of video for which the objects are associated
video_name = "example_video.mp4"

# Find the label row corresponding to the video that the labels are associated to.
label_row: dict = next((lr for lr in project.label_rows if lr["data_title"] == video_name))

# Create or fetch details of the label row.
if label_row["label_hash"] is None:
    label_row: dict = project.create_label_row(label_row["data_hash"])
else:
    label_row: dict = project.get_label_row(label_row["label_hash"])

# Videos only have one data unit, so fetch the labels of that data unit.
encord_labels: dict = next((du for du in label_row["data_units"].values()))["labels"]
classification_answers = label_row["classification_answers"]  # New

# Collection of Encord object_hashes to allow track_ids to persist across frames.
object_hash_idx: Dict[int, str] = {}

for local_frame_level_classifications in local_classifications:
    frame: int = local_frame_level_classifications["frame"]

    # Note that we will append to list of existing objects in the label row.
    encord_frame_labels: dict = encord_labels.setdefault(str(frame), {"objects": [], "classifications": []})
    # Uncomment this line if you want to overwrite the classifications on the platform
    # encord_frame_labels["classifications"] = []

    for local_class in local_frame_level_classifications["classification"]:
        local_class_type: str = local_class["type"]

        # NEW start
        encord_class_info: dict = local_to_encord_ont_classifications[local_class_type]
        encord_classification: dict = encord_class_info["classification"]
        option_map: dict = encord_class_info["options"]

        if not option_map:  # Text classification
            answers = local_class["data"]
        elif isinstance(local_class["data"], (list, tuple)):  # Multi-option checklist
            answers = [option_map[o] for o in local_class["data"]]
        else:  # Single option
            answers = option_map[local_class["data"]]
        # NEW end

        track_id = local_class.get("track_id")
        classification_hash: Optional[str] = object_hash_idx.get(track_id)

        # NEW start
        # Construct Encord object dictionary
        (encord_class_dict, encord_answers,) = make_classification_dict_and_answer_dict(
            encord_classification,
            answers,
            classification_hash=classification_hash,
        )

        # Check if the same annotation already exist, if it exists, replace it with the local annotation
        frame_classifications = encord_labels[str(frame)]["classifications"]
        label_already_exist = False
        for i in range(len(frame_classifications)):
            if frame_classifications[i]["name"] == encord_classification["name"]:
                classification_answers.pop(frame_classifications[i]["classificationHash"])
                frame_classifications[i] = encord_class_dict
                label_already_exist = True
                break
        if not label_already_exist:
            encord_labels[str(frame)]["classifications"].append(encord_class_dict)

        if classification_hash is None:  # Save answers once for each track id.
            classification_answers[encord_class_dict["classificationHash"]] = encord_answers

        # Remember object hash for next time.
        object_hash_idx.setdefault(track_id, encord_class_dict["classificationHash"])
        # NEW end

# NB: This call is important to maintain a valid label_row structure!
label_row = construct_answer_dictionaries(label_row)
project.save_label_row(label_row["label_hash"], label_row)

#%%
# **Saving classification to label rows with image groups**
#
# Suppose you have the following local data that you want to save to Encord.

# A list of local objects to save to Encord.
local_classifications = {
    # Local image name
    "000001.jpg": [
        {  # Radio type classicifation
            "type": "has_animal",  # The local object type identifier
            "data": 0,  # The data of the object
            # If the _same_ classification is present across multiple images,
            # specify a unique id across frames here
            "track_id": 0,
        },
        {  # Checklist classification
            "type": "other_objects",
            "data": [
                1,
                2,
            ],  # Choose both car (local id 1) and leash (local id 2)
        },
        {  # Text classification
            "type": "description",
            "data": "Your description of the frame",
        },
    ],
    # ...
}

#%%
# The data is saved by the following code example.


# Take any label row, which contains images from your local dictionary.
label_row = project.label_rows[0]

# Create or fetch details of the label row.
if label_row["label_hash"] is None:
    label_row = project.create_label_row(label_row["data_hash"])
else:
    label_row = project.get_label_row(label_row["label_hash"])

classification_answers = label_row["classification_answers"]

# Collection of Encord object_hashes to allow track_ids to persist across frames.
object_hash_idx: Dict[int, str] = {}

# Image groups a variable number of data units so iterate over those.
for encord_data_unit in label_row["data_units"].values():
    if encord_data_unit["data_title"] not in local_objects:
        continue  # No match for this data unit.

    # Note: The following line will append objects to the list of existing objects on
    # the Encord platform. To overwrite, existing objects, uncomment this:
    # encord_data_unit["labels"]["classifications"] = []
    encord_labels: dict = encord_data_unit["labels"]

    for local_class in local_classifications[encord_data_unit["data_title"]]:
        local_class_type: str = local_class["type"]

        # NEW start
        encord_class_info: dict = local_to_encord_ont_classifications[local_class_type]
        encord_classification: dict = encord_class_info["classification"]
        option_map: dict = encord_class_info["options"]

        if not option_map:  # Text classification
            answers = local_class["data"]
        elif isinstance(local_class["data"], (list, tuple)):  # Multi-option checklist
            answers = [option_map[o] for o in local_class["data"]]
        else:  # Single option
            answers = option_map[local_class["data"]]
        # NEW end

        track_id = local_class.get("track_id")
        classification_hash: Optional[str] = object_hash_idx.get(track_id)

        # NEW start
        # Construct Encord object dictionary
        (encord_class_dict, encord_answers,) = make_classification_dict_and_answer_dict(
            encord_classification,
            answers,
            classification_hash=classification_hash,
        )
        # Add to existing classifications in this frame.
        encord_labels["classifications"].append(encord_class_dict)

        if classification_hash is None:  # Save answers once for each track id.
            classification_answers[encord_class_dict["classificationHash"]] = encord_answers

        # Remember object hash for next time.
        object_hash_idx.setdefault(track_id, encord_class_dict["classificationHash"])

# NB: This call is important to maintain a valid label_row structure!
label_row = construct_answer_dictionaries(label_row)
project.save_label_row(label_row["label_hash"], label_row)
