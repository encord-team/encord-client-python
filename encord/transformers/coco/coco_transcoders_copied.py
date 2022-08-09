from dataclasses import dataclass
from itertools import chain

from shapely.geometry import Polygon


@dataclass
class Size:
    width: int
    height: int


def get_size(*args, **kwargs) -> Size:
    return Size(1, 2)  # A stub for now


# DENIS: rework this next.
# probably best to load the ontology object to get this instead of trying to infer it from the labels.
# DENIS: decide what to do with nested objects!
# probably reasonable to have no reasonable supercategory. Maybe supercategory = category.
def get_categories(cord_json):
    categories = []
    category_ids = dict()
    names = set()
    id = 0

    def process_category(obj):
        nonlocal id
        objname = obj["name"] + "_" + obj["objectHash"]
        if objname not in names:
            cat = {"supercategory": obj["name"], "id": id, "name": objname}
            if obj["shape"] == "point":
                cat["keypoints"] = [obj["name"]]
                cat["skeleton"] = []
            if obj["shape"] == "skeleton":
                cat["keypoints"] = []
                cat["skeleton"] = []
                for point in obj["skeleton"].values():
                    cat["keypoints"].append(point["name"])
            categories.append(cat)
            category_ids[objname] = id
            names.add(objname)
            id += 1

    if cord_json["data_type"] == "img_group":
        for cord_image in cord_json["data_units"].values():
            for obj in cord_image["labels"]["objects"]:
                process_category(obj)
    elif cord_json["data_type"] == "video":
        cord_video = next(iter(cord_json["data_units"].values()))
        for frame in cord_video["labels"].values():
            for obj in frame["objects"]:
                process_category(obj)
    return categories, category_ids


def get_polygon_from_dict(polygon_dict, W, H):
    return [(polygon_dict[str(i)]["x"] * W, polygon_dict[str(i)]["y"] * H) for i in range(len(polygon_dict))]


# DENIS: I probably want this to work from the cord datastructure for frames.
def ConvertFromCordAnnotationFormatToCOCOAnnotationFormat(cord_json, out=None):
    """Serialize cord_json to a dict complying with coco annotation format"""
    coco_json = out if out is not None else {}

    # info section
    coco_json.setdefault(
        "info",
        {
            "contributor": None,
            "date_created": None,
            "url": None,
            "version": None,
            "year": None,
        },
    )

    prev_desc = coco_json["info"].get("description", "")
    this_desc = cord_json["data_title"]
    desc = f"{prev_desc}; {this_desc}" if prev_desc else this_desc
    coco_json["info"]["description"] = desc

    if cord_json["data_type"] == "video":
        # NB: Séraphin be careful, if you have multiple videos and need to use the data
        # urls. They will be overwritten.
        coco_json["info"]["url"] = next(iter(cord_json["data_units"].values()))["data_link"]

    # license section
    coco_json["licenses"] = []  # license example {'url':None, 'id':1, 'name':''}

    # categories section
    coco_json["categories"], category_ids = get_categories(cord_json)

    # image and annotations section
    extracted_images = coco_json.setdefault("images", [])
    extracted_annotations = coco_json.setdefault("annotations", [])
    annotation_id = len(extracted_annotations)

    def extract_annotations_from(frame_annotations, image_id):
        nonlocal annotation_id
        for annotation in frame_annotations:
            coco_annotation = {
                "area": None,
                "bbox": None,
                "category_id": None,
                "id": annotation_id,
                "image_id": image_id,
                "iscrowd": 0,
                "segmentation": None,
            }
            if annotation["shape"] == "bounding_box":
                x, y = (
                    annotation["boundingBox"]["x"] * size.width,
                    annotation["boundingBox"]["y"] * size.height,
                )
                w, h = (
                    annotation["boundingBox"]["w"] * size.width,
                    annotation["boundingBox"]["h"] * size.height,
                )
                coco_annotation["area"] = w * h
                coco_annotation["segmentation"] = [[x, y, x + w, y, x + w, y + h, x, y + h]]
            elif annotation["shape"] == "polygon":
                polygon = get_polygon_from_dict(annotation["polygon"], size.width, size.height)
                coco_annotation["segmentation"] = [list(chain(*polygon))]
                polygon = Polygon(polygon)
                coco_annotation["area"] = polygon.area
                x, y, x_max, y_max = polygon.bounds
                w, h = x_max - x, y_max - y
            elif annotation["shape"] == "point":
                x, y = (
                    annotation["point"]["0"]["x"] * size.width,
                    annotation["point"]["0"]["y"] * size.height,
                )
                w, h = 0, 0
                coco_annotation["area"] = 0
                coco_annotation["segmentation"] = [[x, y]]
                coco_annotation["keypoints"] = [x, y, 2]
                coco_annotation["num_keypoints"] = 1
            # DENIS: support polyline!
            elif annotation["shape"] == "skeleton":
                coco_annotation["area"] = 0
                coco_annotation["segmentation"] = []
                coco_annotation["keypoints"] = []
                for point in annotation["skeleton"].values():
                    coco_annotation["keypoints"] += [
                        point["x"] * size.width,
                        point["y"] * size.height,
                        2,
                    ]
                coco_annotation["num_keypoints"] = len(coco_annotation["keypoints"]) // 3
                xs, ys = (
                    coco_annotation["keypoints"][::3],
                    coco_annotation["keypoints"][1::3],
                )
                x, y, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
                w, h = x_max - x, y_max - y
            coco_annotation["bbox"] = [x, y, w, h]
            coco_annotation["category_id"] = category_ids[annotation["name"] + "_" + annotation["objectHash"]]
            extracted_annotations.append(coco_annotation)
            annotation_id += 1
        return annotation_id

    if cord_json["data_type"] == "img_group":
        for cord_image in cord_json["data_units"].values():
            size = get_size(cord_image["data_link"])
            cord_image_id = int(cord_image["data_sequence"])
            # fill image data
            coco_image = {
                "coco_url": cord_image["data_link"],
                "id": cord_image_id,
                "file_name": cord_image["data_title"],
                "height": size.height,
                "width": size.width,
                # "flickr_url" : None, 'license': None,
            }
            extracted_images.append(coco_image)
            # fill annotations data
            extract_annotations_from(cord_image["labels"]["objects"], cord_image_id)
    if cord_json["data_type"] == "video":
        cord_video = next(iter(cord_json["data_units"].values()))
        size = get_size(cord_video["data_link"], is_video=True)
        for frame_id, frame in cord_video["labels"].items():
            # fill image data
            cord_frame_id = int(frame_id)
            coco_image = {
                "id": cord_frame_id,
                "height": size.height,
                "width": size.width,
                "file_name": cord_video["data_title"],  # 'coco_url': None, "flickr_url" : None, 'license': None,
            }
            extracted_images.append(coco_image)
            # fill annotations data
            extract_annotations_from(frame["objects"], cord_frame_id)

    return coco_json
