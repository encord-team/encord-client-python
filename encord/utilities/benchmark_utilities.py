from typing import Dict, List

from shapely.geometry import Point, Polygon, box

from encord.client import EncordClientProject
from encord.orm.label_row import LabelRow


def get_project_labels_consensus(
    baseline_project: EncordClientProject,
    comparing_projects: List[EncordClientProject],
    ontology_feature_node_hash_list: List[str],
    threshold: float = 0.7,
) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance metrics of a label generating agent when compared with consensus reached by other agents.

    Args:
        baseline_project:
            The project to be evaluated.
        comparing_projects:
            The list of projects where consensus is extracted.
        ontology_feature_node_hash_list:
            The list of feature node hashes denoting object classes from baseline_project ontology to be evaluated.
        threshold:
            Used in objects comparison. Two objects' instances are considered the same object if their Jaccard
            similarity coefficient is greater or equal than the threshold; otherwise, they represent distinct objects.

    Returns:
        Consensus score (precision and recall) for objects from baseline_project indexed by their feature node hashes.

    Raises:
        NotImplementedError:
            If objects using point or skeleton shapes have their feature node hashes in ontology_feature_node_hash.
        ValueError:
            If a LabelRow of an EncordClientProject has an invalid format.
    """
    # Use set so 'in' operation is O(1) in the average case instead of O(n)
    feature_node_hash_set = set(ontology_feature_node_hash_list)

    # Obtain LabelRows shared between baseline_project and projects in comparing_projects (same data_hash)
    data_hash_to_label_rows = dict()
    for label_row_metadata in baseline_project.get_project().label_rows:
        if label_row_metadata["label_status"] == "LABELLED":
            data_hash = label_row_metadata["data_hash"]
            label_hash = label_row_metadata["label_hash"]
            label_row = baseline_project.get_label_row(label_hash, get_signed_url=False)
            data_hash_to_label_rows[data_hash] = [label_row]
    for project in comparing_projects:
        for label_row_metadata in project.get_project().label_rows:
            if label_row_metadata["label_status"] != "LABELLED":
                continue
            data_hash = label_row_metadata["data_hash"]
            label_hash = label_row_metadata["label_hash"]
            if data_hash in data_hash_to_label_rows:
                label_row = project.get_label_row(label_hash, get_signed_url=False)
                data_hash_to_label_rows[data_hash].append(label_row)

    # Find consensus within LabelRows that share the same data_hash and compare it with the corresponding LabelRow in
    # baseline_project in order to extract consensus score
    consensus_score = dict()
    for label_row_list in data_hash_to_label_rows.values():
        if len(label_row_list) == 1:  # there is no consensus data to compare with
            continue
        frames_within_label_rows = [__extract_frames_within_label_row(label_row) for label_row in label_row_list]

        # Find frame consensus and add it to global consensus score
        baseline_frames = frames_within_label_rows[0]
        for index, frame in baseline_frames.items():
            # If frame is not found in comparing_frames, use a default value that indicates no available annotation
            comparing_frames = [
                current_frames[index] if index in current_frames else {"objects": [], "classifications": []}
                for current_frames in frames_within_label_rows[1:]
            ]
            __add_frame_consensus_score(frame, comparing_frames, feature_node_hash_set, threshold, consensus_score)

    # Transform true_positive, false_positive and false_negative score to precision and recall metrics
    for feature_hash, score in consensus_score.items():
        precision = score["TP"] if score["TP"] + score["FP"] == 0 else score["TP"] / (score["TP"] + score["FP"])
        recall = score["TP"] if score["TP"] + score["FN"] == 0 else score["TP"] / (score["TP"] + score["FN"])
        consensus_score[feature_hash] = {"precision": precision, "recall": recall}
    return consensus_score


# ---------------------------------------------------------
#                   Helper functions
# ---------------------------------------------------------
def __add_frame_consensus_score(base_frame, comparing_frames, label_types, threshold, consensus_score):
    """
    Update consensus score when comparing base_frame's objects with consensus objects obtained from comparing_frames.
    Two objects' instances are considered the same object if their Jaccard similarity coefficient is greater or equal
    than the threshold; otherwise, they represent distinct objects.
    """
    consensus_objects = __find_consensus_objects(comparing_frames, label_types, threshold)
    # Score each base_frame's object as true positive (TP) or false positive (FP) when compared to consensus objects
    for base_object in base_frame["objects"]:
        feature_hash = base_object["featureHash"]
        if feature_hash not in label_types:
            continue
        # Compare base_object with consensus objects of the same type to search for base_object's most similar object
        max_similarity = (-1, -1)  # (best_jaccard_similarity_coefficient, index_of_selected_consensus_object)
        consensus_objects.setdefault(feature_hash, dict())
        for comparing_index, comparing_object in consensus_objects[feature_hash].items():
            cur_similarity = (__calculate_jaccard_similarity(base_object, comparing_object), comparing_index)
            max_similarity = max(max_similarity, cur_similarity)
        score = consensus_score.setdefault(feature_hash, {"TP": 0, "FP": 0, "FN": 0})
        if max_similarity[0] >= threshold:
            score["TP"] += 1
            consensus_objects[feature_hash].pop(max_similarity[1])
        else:
            score["FP"] += 1
    # Score each unmatched consensus object as false negative (FN)
    for feature_hash, objects in consensus_objects.items():
        score = consensus_score.setdefault(feature_hash, {"TP": 0, "FP": 0, "FN": 0})
        score["FN"] += len(objects)


def __find_consensus_objects(comparing_frames, label_types, threshold):
    """
    Compare objects generated by different agents across the same frame and return those where at least half of the
    agents agreed on. Two objects' instances are considered the same object if their Jaccard similarity coefficient is
    greater or equal than the threshold; otherwise, they represent distinct objects.
    """
    comparing_objects = [frame["objects"] for frame in comparing_frames]

    # Cluster objects by their corresponding feature node hash in the ontology while keeping a separation between agents
    feature_hash_to_object_dict = dict()
    for objects in comparing_objects:
        feature_hash_to_objects = dict()
        for obj in objects:
            feature_hash = obj["featureHash"]
            if feature_hash in label_types:
                # Use dictionary so item deletion is O(1) in the average case instead of O(n)
                object_dict = feature_hash_to_objects.setdefault(feature_hash, dict())
                object_dict[len(object_dict)] = obj
        for feature_hash, object_dict in feature_hash_to_objects.items():
            object_dicts = feature_hash_to_object_dict.setdefault(feature_hash, [])
            object_dicts.append(object_dict)

    # Choose consensus objects as the ones appearing in at least half of the agents' annotations.
    consensus_objects = dict()
    amount_agents = len(comparing_frames)
    for feature_hash, object_dicts in feature_hash_to_object_dict.items():
        for base_index, base_dict in enumerate(object_dicts):
            objects_used_in_base_dict = list()
            for idx1, obj1 in base_dict.items():
                # Compare obj1 with all other agents' same object annotations to search for obj1's most similar object
                similarities_found = []  # Store tuples following (which_dict_the_object_came_from, object_index) format
                for comparing_index, comparing_dict in enumerate(object_dicts):
                    if base_index == comparing_index:  # skip comparison between same agent's annotations
                        continue
                    max_similarity = (-1, -1)  # (best_jaccard_similarity_coefficient, index_in_comparing_dict)
                    for idx2, obj2 in comparing_dict.items():
                        cur_similarity = (__calculate_jaccard_similarity(obj1, obj2), idx2)
                        max_similarity = max(max_similarity, cur_similarity)
                    if max_similarity[0] >= threshold:
                        similarities_found.append((comparing_index, max_similarity[1]))

                # Check if at least half of the agents agreed on obj1 and if so then delete those objects similar to
                # obj1 in order to avoid choosing other representation of the same object in a later iteration
                if (len(similarities_found) + 1) * 2 >= amount_agents:
                    objects_used_in_base_dict.append(idx1)
                    # Use dictionary so item deletion is O(1) in the average case instead of O(n)
                    object_dict = consensus_objects.setdefault(feature_hash, dict())
                    object_dict[len(object_dict)] = obj1
                    for dict_index, object_index in similarities_found:
                        object_dicts[dict_index].pop(object_index)

            # Delete current agent's agreed by majority objects to avoid deleting entries in the dict while iterating it
            for object_index in objects_used_in_base_dict:
                object_dicts[base_index].pop(object_index)
    return consensus_objects


def __calculate_jaccard_similarity(obj1, obj2):
    """
    Calculate Jaccard similarity coefficient (Intersection over Union) between objects obj1 and obj2.
    """
    if obj1["shape"] == "point" or obj2["shape"] == "point":
        raise NotImplementedError("Point object's shape doesn't yet support similarity calculation")
    if obj1["shape"] == "skeleton" or obj2["shape"] == "skeleton":
        raise NotImplementedError("Skeleton object's shape doesn't yet support similarity calculation")
    p1 = __transform_obj_to_polygon(obj1)
    p2 = __transform_obj_to_polygon(obj2)
    intersection = p1.intersection(p2).area
    union = p1.area + p2.area - intersection
    return intersection / union


def __transform_obj_to_polygon(obj):
    """
    Return the polygon represented in obj.
    """
    if obj["shape"] == "bounding_box":
        x = obj["boundingBox"]["x"]
        y = obj["boundingBox"]["y"]
        h = obj["boundingBox"]["h"]
        w = obj["boundingBox"]["w"]
        return box(x, y, x + w, y + h)
    elif obj["shape"] == "polygon":
        poly_dict = obj["polygon"]
        return Polygon([(poly_dict[str(i)]["x"], poly_dict[str(i)]["y"]) for i in range(len(poly_dict))])
    elif obj["shape"] == "point":
        x = obj["point"]["0"]["x"]
        y = obj["point"]["0"]["y"]
        return Point(x, y)
    elif obj["shape"] == "skeleton":
        raise NotImplementedError("Skeleton object's shape is not fully functional so no transformation is available")
    else:
        raise ValueError("{0} is not a supported object's shape".format(obj["shape"]))


def __extract_frames_within_label_row(label_row: LabelRow):
    """
    Extract all the frames within a LabelRow.

    Args:
        label_row: The LabelRow where the frames are going to be extracted.

    Returns:
        A dictionary following the pattern:
        {"frame": {"objects":[...], "classifications":[...]},
         "frame": {"objects":[...], "classifications":[...]}, ...}

    Raises:
        ValueError:
            If the LabelRow has an invalid format.
    """
    frames = dict()
    if label_row.data_type == "img_group":
        for data_unit in label_row.data_units.values():
            frames[data_unit["data_sequence"]] = data_unit["labels"]
    elif label_row.data_type == "video":
        for data_unit in label_row.data_units.values():
            frames = data_unit["labels"]
            break
    else:
        raise ValueError("{0} is not a supported LabelRow's data type".format(label_row.data_type))
    return frames
