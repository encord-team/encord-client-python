from encord.client import EncordClientProject
from typing import List
from shapely.geometry import Polygon, box, Point
from pprint import pprint


def get_project_labels_consensus(
    baseline_project: EncordClientProject,
    comparing_projects: List[EncordClientProject],
    label_types: List[str],
    threshold: float = 0.7,
):
    label_types = set(label_types)  # Use O(1) average case instead of O(n) on 'in' operation

    # ontology = baseline_project.get_project_ontology()
    # objects = set()
    # for obj in ontology.ontology_objects:
    #     if obj.feature_node_hash in label_types:
    #         objects.add(obj)
    #
    # classifications = set()
    # for cls in ontology.ontology_classifications:
    #     if cls.feature_node_hash in label_types:
    #         classifications.add(cls)

    data_hash_to_label_hash = dict()
    for label_row in baseline_project.get_project().label_rows:
        if label_row["label_status"] == "LABELLED":
            lr = baseline_project.get_label_row(label_row["label_hash"], get_signed_url=False)
            data_hash_to_label_hash[label_row["data_hash"]] = [lr]

    for index, project in enumerate(comparing_projects):
        for label_row in project.get_project().label_rows:
            if label_row["data_hash"] in data_hash_to_label_hash and label_row["label_status"] == "LABELLED":
                lr = project.get_label_row(label_row["label_hash"], get_signed_url=False)
                data_hash_to_label_hash[label_row["data_hash"]].append(lr)

    consensus_score = dict()
    for dh, lr_list in data_hash_to_label_hash.items():
        if len(lr_list) == 1:  # there is no consensus data to compare with
            continue

        if lr_list[0]["data_type"] == "img_group":
            # print("img_group data_unit")  # TODO ERASE DEBUG LINE
            for i in range(len(lr_list)):
                new_data_unit = dict()
                for data_unit in lr_list[i]["data_units"].values():
                    new_data_unit[data_unit["data_sequence"]] = data_unit["labels"]
                lr_list[i] = new_data_unit
        elif lr_list[0]["data_type"] == "video":
            # print("video data_unit")  # TODO ERASE DEBUG LINE
            for i in range(len(lr_list)):
                for data_unit in lr_list[i]["data_units"].values():
                    lr_list[i] = data_unit["labels"]
                    break
        else:
            raise ValueError(lr_list[0]["data_type"])

        base_lr = lr_list[0]
        # if dh != "27b601ef-c080-4c6e-9bed-ad382cfaefad":  # TODO ERASE DEBUG LINE
        #     continue
        # print("\ndata_hash {0}".format(dh))  # TODO ERASE DEBUG LINE
        # print(type(base_lr))  # TODO ERASE DEBUG LINE
        for index, frame in base_lr.items():
            comparing_frames = [
                data_unit[index] if index in data_unit else {"objects": [], "classifications": []}
                for data_unit in lr_list[1:]
            ]
            # print("frame #{0}".format(index))
            add_frame_consensus(frame, comparing_frames, label_types, threshold, consensus_score)
            # except:
            #     print(index, len(lr_list), dh)
            #     # print(frame)
            #     for data_unit in lr_list:
            #         if index not in data_unit:
            #             print("why")
            #         else:
            #             print("ok")
            #     for project in comparing_projects:
            #         print("Checking {0}".format(project.get_project()["title"]))
            #         for label_row in project.get_project().label_rows:
            #             if label_row["data_hash"] == dh and label_row["label_status"] == "LABELLED":
            #                 lr = project.get_label_row(label_row["label_hash"], get_signed_url=False)
            #                 print(lr)
            #
            #     x = 0 / 0

    # print(consensus_score) # TODO ERASE DEBUG LINE
    # TODO After writing the classifications part check if this still ok
    for feature_hash, d in consensus_score.items():
        precision = d["TP"] if d["TP"] + d["FP"] == 0 else d["TP"] / (d["TP"] + d["FP"])
        recall = d["TP"] if d["TP"] + d["FN"] == 0 else d["TP"] / (d["TP"] + d["FN"])
        consensus_score[feature_hash] = {"precision": precision, "recall": recall}

    return consensus_score


# ---------------------------------------------------------
#                   Helper functions
# ---------------------------------------------------------
def add_frame_consensus(base_frame, comparing_frames, label_types, threshold, consensus_score):  # TODO add return value
    consensus_objects = find_consensus_objects(comparing_frames, label_types, threshold)
    # print("consensus object quantity {0}".format(len(consensus_objects)))  # TODO ERASE DEBUG LINE
    # print(
    #     "amount of objects {0}".format(len([obj for obj in base_frame["objects"] if obj["featureHash"] in label_types]))
    # )
    for obj1 in base_frame["objects"]:
        feature_hash = obj1["featureHash"]
        if feature_hash not in label_types:
            continue
        max_similarity = (-1, -1)
        consensus_objects.setdefault(feature_hash, dict())  # default if an object's type is missing in the consensus
        for index, obj2 in consensus_objects[feature_hash].items():
            cur_similarity = (calculate_similarity(obj1, obj2), index)
            max_similarity = max(max_similarity, cur_similarity)
        d = consensus_score.setdefault(feature_hash, {"TP": 0, "FP": 0, "FN": 0})
        if max_similarity[0] >= threshold:
            d["TP"] += 1
            consensus_objects[feature_hash].pop(max_similarity[1])
            # print("good", max_similarity[0], obj1)  # TODO ERASE DEBUG LINE
        else:
            d["FP"] += 1
            # print("bad", max_similarity[0], obj1)  # TODO ERASE DEBUG LINE
    for feature_hash, objects in consensus_objects.items():
        d = consensus_score.setdefault(feature_hash, {"TP": 0, "FP": 0, "FN": 0})
        d["FN"] += len(objects)

    # TODO add classifications consensus


def find_consensus_objects(comparing_frames, label_types, threshold):
    comparing_objects = [frame["objects"] for frame in comparing_frames]
    feature_hash_to_obj_dict = dict()
    # Cluster frames' objects by their corresponding type on the ontology
    for objects in comparing_objects:
        feature_hash_to_objects = dict()
        for obj in objects:
            feature_hash = obj["featureHash"]
            if feature_hash in label_types:
                # Use dictionary so item deletion average case is O(1) when choosing consensus objects
                obj_dict = feature_hash_to_objects.setdefault(feature_hash, dict())
                obj_dict[len(obj_dict)] = obj
        for key, value in feature_hash_to_objects.items():
            lst = feature_hash_to_obj_dict.setdefault(key, [])
            lst.append(value)
    # print(
    #     len(feature_hash_to_obj_dict), [len(e) for d in feature_hash_to_obj_dict.values() for e in d]
    # )  # TODO ERASE DEBUG LINE
    # Choose consensus objects
    consensus_objects = dict()
    for feature_hash, object_dicts in feature_hash_to_obj_dict.items():
        for i, dict1 in enumerate(object_dicts):
            delete_objs = list()
            for idx1, obj1 in dict1.items():
                found_similarities = []
                for j, dict2 in enumerate(object_dicts):
                    if i == j:
                        continue
                    max_similarity = (-1, -1)
                    for idx2, obj2 in dict2.items():
                        cur_similarity = (calculate_similarity(obj1, obj2), idx2)
                        max_similarity = max(max_similarity, cur_similarity)
                    # print((i, idx1), (j, idx2), max_similarity)  # TODO ERASE DEBUG LINE
                    if max_similarity[0] >= threshold:
                        found_similarities.append((j, max_similarity[1]))
                if (len(found_similarities) + 1) * 2 >= len(comparing_frames):
                    delete_objs.append(idx1)
                    obj_dict = consensus_objects.setdefault(feature_hash, dict())
                    obj_dict[len(obj_dict)] = obj1
                    for list_index, obj_index in found_similarities:
                        object_dicts[list_index].pop(obj_index)
            for obj_id in delete_objs:
                object_dicts[i].pop(obj_id)
    return consensus_objects


def calculate_similarity(obj1, obj2):  # TODO add similarity calculation for points (now is always zero)
    p1 = transform_obj_to_polygon(obj1)
    p2 = transform_obj_to_polygon(obj2)
    intersection = p1.intersection(p2).area
    union = p1.area + p2.area - intersection
    return intersection / union


def transform_obj_to_polygon(obj):
    if obj["shape"] == "bounding_box":
        x = obj["boundingBox"]["x"]
        y = obj["boundingBox"]["y"]
        h = obj["boundingBox"]["h"]
        w = obj["boundingBox"]["w"]
        return box(x, y, x + w, y + h)
    elif obj["shape"] == "polygon":
        poly_dict = obj["polygon"]
        return Polygon([(poly_dict[str(i)]["x"], poly_dict[str(i)]["y"]) for i in range(len(poly_dict))])
    elif obj["shape"] == "point":  # TODO test if 'point' is the correct type on the sdk
        raise ValueError("Skeletons are not fully functional so no comparison is allowed")
        # return Point(obj["point"]["x"], obj["point"]["t"])  # TODO Is it a correct way to obtain point coordinates?
    else:
        raise ValueError(obj["shape"])  # TODO check how the displayed error looks like
