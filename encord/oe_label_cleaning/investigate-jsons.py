import json
import os
from pprint import pprint

import pandas as pd


def get_file_pairs(dir_path):
    # Check if the directory exists
    if not os.path.exists(dir_path):
        print(f"Directory '{dir_path}' does not exist.")
        exit()

    file_pairs = []
    # Loop through all files in the directory
    for filename in os.listdir(dir_path):
        # Check if the file is a JSON file and has the required suffixes
        if filename.lower().endswith("bkp.json"):
            file_edit = filename[: -len("bkp.json")] + "edit.json"
            file_pairs.append((filename, file_edit))
    return file_pairs


def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
    mod_copy = modified.copy()
    same = set(o for o in shared_keys if d1[o] == d2[o])

    for k, v in mod_copy.items():
        if (k in ["createdAt", "lastEditedAt"] and v[0][: len(v[0]) - len("GMT")].strip() == v[1].strip()) or (
            k == "value" and v[0] == "Usable Clip" and v[1] == "usable_clip"
        ):
            same.add(k)
            modified.pop(k)
    return added, removed, modified, same


def remove_uncorrupted_labels(b_class, e_class):
    b_class_copy = b_class.copy()
    e_class_copy = e_class.copy()
    diffs = []
    for b_cls in b_class:
        for e_cls in e_class:
            diff = []
            added, removed, modified, same = dict_compare(b_cls, e_cls)
            if (
                (added == set() or added == dict())
                and (removed == set() or removed == dict())
                and (modified == set() or modified == dict())
            ):
                print(f"REMOVING {b_cls['classificationHash']}")
                b_class_copy.remove(b_cls)
                e_class_copy.remove(e_cls)
            elif e_cls["classificationHash"] == b_cls["classificationHash"]:
                # pprint(added)
                # pprint(removed)
                diff = modified.copy()
                pprint(modified)
                diffs.append(diff)
                # pprint(same)
    return b_class_copy, e_class_copy, diffs


def compare_frames(b_dict, e_dict, dir_path):
    lab_hash = b_dict["label_hash"]
    problem_labels = {
        "Frame Number": [],
        "Label Type": [],
        "Labels Before": [],
        "Labels After": [],
        "Deduped Labels Before": [],
        "Deduped Labels After": [],
        "Differences": [],
        "Label Hash": [],
    }
    for data_unit, meta in b_dict["data_units"].items():
        print(lab_hash)
        for frame_num, labels in meta["labels"].items():
            b_class = labels["classifications"]
            b_objects = labels["objects"]
            e_labels = e_dict["data_units"][data_unit]["labels"]
            if frame_num in e_labels.keys():
                e_label = e_labels[frame_num]
                e_class = e_label["classifications"]
                # e_class_feat_hashes = [cls["featureHash"] for cls in e_class]
                e_objects = e_label["objects"]
                # e_obj_feat_hashes = [obj["featureHash"] for obj in e_objects]
            else:
                print("\nNo e labels for this value")
                e_class = []
                e_objects = []
            if len(e_class) != len(b_class):
                print(frame_num)
                deduped_b_class, deduped_e_class, diffs = remove_uncorrupted_labels(b_class, e_class)
                problem_labels["Frame Number"].append(frame_num)
                problem_labels["Label Type"].append(["Classification"])
                problem_labels["Labels Before"].append(b_class)
                problem_labels["Labels After"].append(e_class)
                problem_labels["Deduped Labels Before"].append(deduped_b_class)
                problem_labels["Deduped Labels After"].append(deduped_e_class)
                problem_labels["Differences"].append(diffs)
                problem_labels["Label Hash"].append(lab_hash)
            if len(e_objects) != len(b_objects):
                raise NotImplementedError("Fix for OBJECTS as well as CLASSIFICATIONS")
                # print(frame_num)
                # deduped_b_objects, deduped_e_objects, diffs = remove_uncorrupted_labels(b_objects, e_objects)
                # problem_labels["Frame Number"].append(frame_num)
                # problem_labels["Label Type"].append(["Objects"])
                # problem_labels["Labels Before"].append(b_objects)
                # problem_labels["Labels After"].append(e_objects)
                # problem_labels["Deduped Labels Before"].append(deduped_b_objects)
                # problem_labels["Deduped Labels After"].append(deduped_e_objects)
                # problem_labels["Differences"].append(diffs)
                # problem_labels["Label Hash"].append(lab_hash)
    problem_labels = pd.DataFrame.from_dict(problem_labels, orient="columns")
    problem_labels.to_csv(dir_path + "/" + lab_hash + "_problem_labels.csv", index=False)
    return problem_labels


def main():
    directory_path = "/encord/984cb43c-b6ea-4f13-bd53-b75e25b02358-NOT-WIP"
    file_pairs = get_file_pairs(directory_path)

    prob_labels = pd.DataFrame(
        {
            "Label Hash": [],
            "Frame Number": [],
            "Label Type": [],
            "Labels Before": [],
            "Labels After": [],
            "Deduped Labels Before": [],
            "Deduped Labels After": [],
            "Differences": [],
        }
    )
    for pair in file_pairs:
        bkp_file_path = os.path.join(directory_path, pair[0])
        edit_file_path = os.path.join(directory_path, pair[1])
        with open(bkp_file_path, "r") as b:
            bkp_json = json.load(b)
        with open(edit_file_path, "r") as e:
            edit_json = json.load(e)
        prob_label = compare_frames(bkp_json, edit_json, directory_path)
        prob_labels = pd.concat([prob_labels, prob_label])
    prob_labels.to_csv(directory_path + "/PROJECT PROBLEM LABELS.csv", index=False)


if __name__ == "__main__":
    main()
