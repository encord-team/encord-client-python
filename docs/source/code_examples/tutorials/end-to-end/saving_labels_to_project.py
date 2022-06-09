"""
Saving project labels
=====================

Use this script to save your local labels to your Encord project.

The code uses a couple of utility functions for constructing dictionaries following the
structure of Encord label rows and finding ontology dictionaries from the Encord
ontology. You can safely skip those details.

.. raw:: html

   <details>
   <summary><a>Utility code</a></summary>
"""
# sphinx_gallery_thumbnail_path = 'images/end-to-end-thumbs/Artboard 10.svg'

import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pytz

GMT_TIMEZONE = pytz.timezone("GMT")
DATETIME_STRING_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"
Point = Union[Tuple[float, float], List[float]]
BBOX_KEYS = {"x", "y", "h", "w"}

# === UTILITIES === #
def __get_timestamp():
    now = datetime.now()
    new_timezone_timestamp = now.astimezone(GMT_TIMEZONE)
    return new_timezone_timestamp.strftime(DATETIME_STRING_FORMAT)


def __lower_snake_case(s: str):
    return "_".join(s.lower().split())


def make_object_dict(
    ontology_object: dict,
    object_data: Union[Point, Iterable[Point], Dict[str, float]] = None,
    object_hash: Optional[str] = None,
) -> dict:
    """
    :type ontology_object: The ontology object to associate with the ``object_data``.
    :type object_data: The data to put in the object dictionary. This has to conform
        with the ``shape`` parameter defined in
        ``ontology_object["shape"]``.
        - ``shape == "point"``: For key-points, the object data should be
          a tuple with x, y coordinates as floats.
        - ``shape == "bounding_box"``: For bounding boxes, the
          ``object_data`` needs to be a dict with info:
          {"x": float, "y": float, "h": float, "w": float} specifying the
          top right corner of the box (x, y) and the height and width of
          the bounding box.
        - ``shape in ("polygon", "polyline")``: For polygons and
          polylines, the format is an iterable  of points:
          [(x, y), ...] specifying (ordered) points in the
          polygon/polyline.
          If ``object_hash`` is none, a new hash will be generated.
    :type object_hash: If you want the object to have the same id across frames (for
        videos only), you can specify the object hash, which need to be
        an eight-character hex string (e.g., use
        ``str(uuid.uuid4())[:8]`` or the ``objectHash`` from an
        associated object.
    :returns: An object dictionary conforming with the Encord label row data format.
    """
    if object_hash is None:
        object_hash = str(uuid.uuid4())[:8]

    timestamp: str = __get_timestamp()
    shape: str = ontology_object.get("shape")

    object_dict = {
        "name": ontology_object["name"],
        "color": ontology_object["color"],
        "value": __lower_snake_case(ontology_object["name"]),
        "createdAt": timestamp,
        "createdBy": "robot@cord.tech",
        "confidence": 1,
        "objectHash": object_hash,
        "featureHash": ontology_object["featureNodeHash"],
        "lastEditedAt": timestamp,
        "lastEditedBy": "robot@encord.com",
        "shape": shape,
        "manualAnnotation": False,
        "reviews": [],
    }

    if shape in ["polygon", "polyline"]:
        # Check type
        try:
            data_iter = iter(object_data)
        except TypeError:
            raise ValueError(f"The `object_data` for {shape} should be an iterable of points.")

        object_dict[shape] = {str(i): {"x": round(x, 4), "y": round(y, 4)} for i, (x, y) in enumerate(data_iter)}

    elif shape == "point":
        # Check type
        if not isinstance(object_data, (list, tuple)):
            raise ValueError(f"The `object_data` for {shape} should be a list or tuple.")

        if len(object_data) != 2:
            raise ValueError(f"The `object_data` for {shape} should have two coordinates.")

        if not isinstance(object_data[0], float):
            raise ValueError(f"The `object_data` for {shape} should contain floats.")

        # Make dict
        object_dict[shape] = {"0": {"x": round(object_data[0], 4), "y": round(object_data[1], 4)}}

    elif shape == "bounding_box":
        # Check type
        if not isinstance(object_data, dict):
            raise ValueError(f"The `object_data` for {shape} should be a dictionary.")

        if len(BBOX_KEYS.union(set(object_data.keys()))) != 4:
            raise ValueError(f"The `object_data` for {shape} should have keys {BBOX_KEYS}.")

        if not isinstance(object_data["x"], float):
            raise ValueError(f"The `object_data` for {shape} should float values.")

        # Make dict
        object_dict["boundingBox"] = {k: round(v, 4) for k, v in object_data.items()}

    return object_dict


def make_classification_dict_and_answer_dict(
    ontology_class: dict,
    answers: Union[List[dict], dict, str],
    classification_hash: Optional[str] = None,
):
    """

    :type ontology_class: The ontology classification dictionary obtained from the
                          project ontology.
    :type answers: The classification option (potentially list) or text answer to apply.
                   If this is a dictionary, it is interpreted as an option of either a
                   radio button answer or a checklist answer.
                   If it is a string, it is interpreted as the actual text answer.
    :type classification_hash: If a classification should persist with the same id over
                               multiple frames (for videos), you can reuse the
                               ``classificationHash`` of a classifications from a
                               previous frame.

    :returns: A classification and an answer dictionary conforming with the Encord label
              row data format.
    """
    if classification_hash is None:
        classification_hash = str(uuid.uuid4())[:8]

    if isinstance(answers, dict):
        answers = [answers]

    if isinstance(answers, list):  # Radio og checklist
        answers_list: List[dict] = []
        for answer in answers:
            try:
                attribute = next((attr for attr in ontology_class["attributes"] if answer in attr["options"]))
            except StopIteration:
                raise ValueError(f"Couldn't find answer `{answer['label']}` in the ontology class")
            answers_list.append(
                {
                    "featureHash": answer["featureNodeHash"],
                    "name": answer["label"],
                    "value": answer["value"],
                }
            )

    else:  # Text attribute
        try:
            attribute = next((attr for attr in ontology_class["attributes"] if attr["type"] == "text"))
            answers_list = [answers]
        except StopIteration:
            raise ValueError(f"Couldn't find ontology with type text for the string answer {answers}")

    classification_dict = {
        "classificationHash": classification_hash,
        "confidence": 1,
        "createdAt": __get_timestamp(),
        "createdBy": "robot@encord.com",
        "featureHash": ontology_class["featureNodeHash"],
        "manualAnnotation": False,
        "name": attribute["name"],
        "reviews": [],
        "value": __lower_snake_case(attribute["name"]),
    }

    classification_answer = {
        "classificationHash": classification_hash,
        "classifications": [
            {
                "answers": answers_list,
                "featureHash": attribute["featureNodeHash"],
                "manualAnnotation": False,
                "name": attribute["name"],
                "value": __lower_snake_case(attribute["name"]),
            }
        ],
    }

    return classification_dict, classification_answer


def find_ontology_object(ontology: dict, encord_name: str):
    try:
        obj = next((o for o in ontology["objects"] if o["name"].lower() == encord_name.lower()))
    except StopIteration:
        raise ValueError(f"Couldn't match Encord ontology name `{encord_name}` to objects in the " f"Encord ontology.")
    return obj


def __find_option(top_level_classification: dict, encord_option_name: Optional[str]):
    if top_level_classification["type"] == "text":
        # Text classifications do not have options
        return None
    try:
        option = next((o for o in top_level_classification["options"] if o["label"].lower() == encord_option_name))
    except StopIteration:
        raise ValueError(f"Couldn't match option name {encord_option_name} to any ontology object.")
    return option


def find_ontology_classification(ontology: dict, local_to_encord_classifications: dict):
    encord_name = local_to_encord_classifications["name"]
    top_level_attribute = None
    for classification in ontology["classifications"]:
        for attribute in classification["attributes"]:
            if attribute["name"].lower() == encord_name.lower():
                top_level_attribute = attribute
                break
        if top_level_attribute:
            break

    if top_level_attribute is None:
        raise ValueError(f"Couldn't match {encord_name} to Encord classification.")

    options = {
        o[0]: __find_option(top_level_attribute, o[1]) for o in local_to_encord_classifications.get("options", [])
    }
    return {"classification": top_level_attribute, "options": options}


#%%
#
# .. raw:: html
#
#    </details>

#%%
# Imports and authentication
# --------------------------
# First, import dependencies and athenticate a project manager.

from encord import EncordUserClient, ProjectManager
from encord.orm.project import Project
from encord.utilities.label_utilities import construct_answer_dictionaries

# Authenticate
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

# Find project to work with based on title.
project: Project = next((p["project"] for p in user_client.get_projects(title_eq="Your project name")))
project_manager: ProjectManager = user_client.get_project_manager(project.project_hash)

project: Project = project_manager.get_project()
ontology = project["editor_ontology"]

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
#     ontology = project_manager.get_project()["editor_ontology"]
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
    label_row: dict = project_manager.create_label_row(label_row["data_hash"])
else:
    label_row: dict = project_manager.get_label_row(label_row["label_hash"])

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
project_manager.save_label_row(label_row)

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
    label_row = project_manager.create_label_row(label_row["data_hash"])
else:
    label_row = project_manager.get_label_row(label_row["label_hash"])

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
project_manager.save_label_row(label_row)


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
    label_row: dict = project_manager.create_label_row(label_row["data_hash"])
else:
    label_row: dict = project_manager.get_label_row(label_row["label_hash"])

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

    for local_class in local_frame_level_classifications["objects"]:
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
        encord_frame_labels["classifications"].append(encord_class_dict)

        if classification_hash is None:  # Save answers once for each track id.
            classification_answers[encord_class_dict["classificationHash"]] = encord_answers

        # Remember object hash for next time.
        object_hash_idx.setdefault(track_id, encord_class_dict["classificationHash"])
        # NEW end

# NB: This call is important to maintain a valid label_row structure!
label_row = construct_answer_dictionaries(label_row)
project_manager.save_label_row(label_row)

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
    label_row = project_manager.create_label_row(label_row["data_hash"])
else:
    label_row = project_manager.get_label_row(label_row["label_hash"])

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
project_manager.save_label_row(label_row)
