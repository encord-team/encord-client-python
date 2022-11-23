"""TODO: think properly about the structure, the transcoders and how we want to subclass or extend this so people
can plug into the different parts easily.

ideas
* a class where the individual parts can be overwritten
* a class where the individual transformers can be re-assigned
*

TODO:
* parallel downloads with a specific flag
* saving the annotation file with a specific flag
* labels class for better type support.
"""
import logging
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from itertools import chain
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, Union

import requests
from shapely.geometry import Polygon
from tqdm import tqdm

from encord.objects.common import Attribute, PropertyType, Shape
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure
from encord.transformers.coco.coco_datastructure import (
    CocoAnnotation,
    SuperClass,
    as_dict_custom,
)

logger = logging.getLogger(__name__)

DOWNLOAD_FILES_DEFAULT = False
DOWNLOAD_FILE_PATH_DEFAULT = Path(".")
INCLUDE_VIDEOS_DEFAULT = True
INCLUDE_UNANNOTATED_VIDEOS_DEFAULT = False
INCLUDE_TRACK_ID_DEFAULT = False
INCLUDE_BOUNDING_BOX_ROTATION_DEFAULT = False
INCLUDE_FLAT_CLASSIFICATIONS = False

RESERVED_CLASSIFICATION_FIELDS = {"encord_track_uuid", "track_id", "rotation"}


@dataclass
class Size:
    width: int
    height: int


@dataclass
class ImageLocation:
    data_hash: str
    file_name: str


@dataclass
class VideoLocation:
    data_hash: str
    file_name: str
    frame_num: int


DataLocation = Union[ImageLocation, VideoLocation]


class EncodingError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def get_size(*args, **kwargs) -> Size:
    # TODO: this belongs in a utils folder.
    return Size(1, 2)  # A stub for now


def get_polygon_from_dict(polygon_dict, W, H):
    return [(polygon_dict[str(i)]["x"] * W, polygon_dict[str(i)]["y"] * H) for i in range(len(polygon_dict))]


# TODO: TODO: focus on doing the parser for now for segmentations for images as it was intended. Seems like
#   for other formats I can still add stuff or have the clients extend what we have.

# TODO: should these labels be the data structure that I've invented for them instead of the encord dict?
class CocoEncoder:
    """This class has been purposefully built in a modular fashion for extensibility in mind. You are encouraged to
    subclass this encoder and change any of the custom functions. The return types are given for convenience, but these
    can also be subclassed for your needs.
    All functions which could be static are deliberately not made static so you have the option to access the `self`
    object at any time.
    """

    def __init__(self, labels_list: List[dict], ontology: OntologyStructure):
        self._labels_list = labels_list
        self._ontology = ontology
        self._coco_json = dict()
        self._current_annotation_id = 0
        self._object_hash_to_track_id_map = {}
        self._coco_categories_id_to_ontology_object_map = dict()  # TODO: do we need this?
        self._feature_hash_to_coco_category_id_map = dict()
        self._data_hash_to_image_id_map = dict()
        """Map of (data_hash, frame_offset) to the image id"""

        # self._data_location_to_image_id_map = dict()

        self._download_files = DOWNLOAD_FILES_DEFAULT
        self._download_file_path = DOWNLOAD_FILE_PATH_DEFAULT
        self._include_videos = INCLUDE_VIDEOS_DEFAULT
        self._include_unannotated_videos = INCLUDE_UNANNOTATED_VIDEOS_DEFAULT
        self._include_track_id = INCLUDE_TRACK_ID_DEFAULT
        self._include_bounding_box_rotation = INCLUDE_BOUNDING_BOX_ROTATION_DEFAULT
        self._include_flat_classifications = INCLUDE_FLAT_CLASSIFICATIONS

    def encode(
        self,
        *,
        download_files: bool = DOWNLOAD_FILES_DEFAULT,
        download_file_path: Path = DOWNLOAD_FILE_PATH_DEFAULT,
        include_videos: bool = INCLUDE_VIDEOS_DEFAULT,
        include_unannotated_videos: bool = INCLUDE_UNANNOTATED_VIDEOS_DEFAULT,
        include_track_id: bool = INCLUDE_TRACK_ID_DEFAULT,
        include_bounding_box_rotation: bool = INCLUDE_BOUNDING_BOX_ROTATION_DEFAULT,
        include_flat_classifications: bool = INCLUDE_FLAT_CLASSIFICATIONS,
    ) -> dict:
        """
        Args:
            download_files: If set to true, the images are downloaded into a local directory and the `coco_url` of the
                images will point to the location of the local directory. TODO: can also maybe have a Path obj here.
            download_file_path:
                Root path to where the images and videos are downloaded or where downloaded images are looked up from.
                For example, if `include_unannotated_videos = True` then this is the root path of the
                `videos/<data_hash>` directory.
            include_unannotated_videos:
                This will be ignored if the files are not downloaded (whether they are being downloaded now or they
                were already there) in which case it will default to False. The code will assume that the video is
                downloaded and expanded correctly in the same way that would happen if the video was downloaded via
                the `download_files = True` argument.
            include_track_id: Add the object_hash as `attributes: {encord_track_uuid: x}` and a numeric tracking
                id as `attributes: {track_id: y}` (compatible with CVAT to COCO export)
            include_bounding_box_rotation: Add the bounding box rotation theta as `attributes: {rotation: x}`
                (compatible with CVAT to COCO export)
            include_flat_classifications: This will include dynamic and non-dynamic classifications as part of
                every label. The responses will be pasted from the range into every single label, duplicating the
                payload in cases where the range would usually cover more than one label. these will be added
                into the `attributes` field. The postfix `_classification` will be added if there is a name
                clash with one of the RESERVED_CLASSIFICATION_FIELDS. The classifications will only include one level
                of nesting. Further nesting will not be considered.
        """
        self._download_files = download_files
        self._download_file_path = download_file_path
        self._include_videos = include_videos
        self._include_unannotated_videos = include_unannotated_videos
        self._include_track_id = include_track_id
        self._include_bounding_box_rotation = include_bounding_box_rotation
        self._include_flat_classifications = include_flat_classifications

        self._coco_json["info"] = self.get_info()
        self._coco_json["categories"] = self.get_categories()
        self._coco_json["images"] = self.get_images()
        self._coco_json["annotations"] = self.get_annotations()

        return self._coco_json

    def get_info(self) -> dict:
        return {
            "description": self.get_description(),
            "contributor": None,  # TODO: these fields also need a response
            "date_created": None,  # TODO: there is something in the labels, alternatively can start to return more from the SDK
            "url": None,
            "version": None,
            "year": None,
        }

    def get_description(self) -> Optional[str]:
        if len(self._labels_list) == 0:
            return None
        else:
            return self._labels_list[0]["data_title"]

    def get_categories(self) -> List[dict]:
        """This does not translate classifications as they are not part of the Coco spec."""
        categories = []
        for object_ in self._ontology.objects:
            categories.append(self.get_category(object_))

        return categories

    def get_category(self, object_: Object) -> dict:
        super_category = self.get_super_category(object_)
        ret = {
            "supercategory": super_category,
            "id": self.add_to_object_map_and_get_next_id(object_),
            "name": self.get_category_name(object_),
        }
        if super_category == "point":
            # TODO: we will have to do something similar for skeletons.
            ret["keypoints"] = "keypoint"
            ret["skeleton"] = []
        return ret

    def get_super_category(self, object_: Object) -> str:
        return object_.shape.value

    def add_to_object_map_and_get_next_id(self, object_: Object) -> int:
        id_ = len(self._coco_categories_id_to_ontology_object_map) + 1
        # Let the category id start at 1, not 0. Segmentation masks that use COCO annotations often create a bit mask
        # with this category id. The bitmask must be above 0.
        self._coco_categories_id_to_ontology_object_map[id_] = object_
        self._feature_hash_to_coco_category_id_map[object_.feature_node_hash] = id_
        return id_

    def get_category_name(self, object_: Object) -> str:
        return object_.name

    def get_images(self) -> list:
        """All the data is in the specific label_row"""
        images = []
        for labels in self._labels_list:
            for data_unit in labels["data_units"].values():
                data_type = data_unit["data_type"]
                if "application/dicom" in data_type:
                    images.extend(self.get_dicom(data_unit))
                elif "video" not in data_type:
                    images.append(self.get_image(data_unit))
                else:
                    images.extend(self.get_video_images(data_unit))
        return images

    def get_dicom(self, data_unit: dict) -> list:
        # NOTE: could give an option whether to include dicoms, but this is inferred by which labels we request.

        data_hash = data_unit["data_hash"]

        images = []

        height = data_unit["height"]
        width = data_unit["width"]

        for frame_num in data_unit["labels"].keys():
            dicom_image = self.get_dicom_image(data_hash, height, width, int(frame_num))
            images.append(dicom_image)

        return images

    def get_image(self, data_unit: dict) -> dict:
        # TODO: we probably want a map of this image id to image hash in our DB, including the image_group hash.

        """
        TODO: next up: here we need to branch off and create the videos
        * coco_url, height, width will be the same
        * id will be continuous
        * file_name will be also continuous according to all the images that are being extracted from the video.

        Do all the frames, and the ones without annotations will just have no corresponding annotations. We can
        still later have an option to exclude them and delete the produced images.
        """
        image_id = len(self._data_hash_to_image_id_map)
        data_hash = data_unit["data_hash"]
        self._data_hash_to_image_id_map[(data_hash, 0)] = image_id
        return {
            "coco_url": data_unit["data_link"],
            "id": image_id,
            "image_title": data_unit["data_title"],
            "file_name": self.get_file_name_and_download_image(data_unit),
            "height": data_unit["height"],
            "width": data_unit["width"],
        }

    def get_file_name_and_download_image(self, data_unit: dict) -> str:
        data_title = data_unit["data_title"]
        data_hash = data_unit["data_hash"]
        file_name = data_hash + "." + data_title.split(".")[-1]
        local_path = Path("images").joinpath(Path(file_name))

        if self._download_files:
            url = data_unit["data_link"]
            destination_path = self._download_file_path.joinpath(local_path)
            self.download_image(url, destination_path)

        return str(local_path)

    def get_video_images(self, data_unit: dict) -> List[dict]:
        if not self._include_videos:
            return []

            # raise RuntimeError("If you want to include videos, you also need to enable downloading (for now).")

        video_title = data_unit["data_title"]
        url = data_unit["data_link"]
        data_hash = data_unit["data_hash"]

        if self._download_files:
            self.download_video_images(url, data_hash)

        images = []
        coco_url = data_unit["data_link"]
        height = data_unit["height"]
        width = data_unit["width"]

        path_to_video_dir = self._download_file_path.joinpath(Path("videos"), Path(data_hash))
        if self._include_unannotated_videos and path_to_video_dir.is_dir():
            # TODO: log something for transparency?
            for frame_num in range(len(list(path_to_video_dir.iterdir()))):
                images.append(self.get_video_image(data_hash, video_title, coco_url, height, width, int(frame_num)))
        else:
            for frame_num in data_unit["labels"].keys():
                images.append(self.get_video_image(data_hash, video_title, coco_url, height, width, int(frame_num)))

        return images

    # def get_frame_numbers(self, data_unit: dict) -> Iterator:  # TODO: use this to remove the above if/else.

    def get_dicom_image(self, data_hash: str, height: int, width: int, frame_num: int) -> dict:
        image_id = len(self._data_hash_to_image_id_map)
        self._data_hash_to_image_id_map[(data_hash, frame_num)] = image_id

        return {
            # DICOM does not have a one to one mapping between a frame and a DICOM series file.
            "coco_url": "",
            "id": image_id,
            "file_name": self.get_dicom_file_path(data_hash, frame_num),
            "height": height,
            "width": width,
        }

    def get_video_image(self, data_hash: str, video_title: str, coco_url: str, height: int, width: int, frame_num: int):
        image_id = len(self._data_hash_to_image_id_map)
        self._data_hash_to_image_id_map[(data_hash, frame_num)] = image_id

        return {
            "coco_url": coco_url,
            "id": image_id,
            "video_title": video_title,
            "file_name": self.get_video_file_path(data_hash, frame_num),
            "height": height,
            "width": width,
        }

    def get_dicom_file_path(self, data_hash: str, frame_num: int) -> str:
        path = Path("dicom") / data_hash / str(frame_num)
        return str(path)

    def get_video_file_path(self, data_hash: str, frame_num: int) -> str:
        frame_file_name = Path(f"{frame_num}.jpg")
        video_file_path = Path("videos").joinpath(Path(data_hash), frame_file_name)
        return str(video_file_path)

    def download_video_images(self, url: str, data_hash: str) -> None:
        with tempfile.TemporaryDirectory(str(Path("."))) as temporary_directory:
            video_location = Path(temporary_directory).joinpath(Path(data_hash))
            download_file(
                url,
                video_location,
            )
            destination_location = self._download_file_path.joinpath(Path("videos"), Path(data_hash))
            extract_frames(video_location, destination_location)

    def get_annotations(self):
        annotations = []

        # TODO: need to make sure at least one image
        for labels in self._labels_list:
            object_answers = labels["object_answers"]
            object_actions = labels["object_actions"]

            for data_unit in labels["data_units"].values():
                data_hash = data_unit["data_hash"]

                if "video" in data_unit["data_type"]:
                    if not self._include_videos:
                        continue
                    for frame_num, frame_item in data_unit["labels"].items():
                        image_id = self.get_image_id(data_hash, int(frame_num))
                        objects = frame_item["objects"]
                        annotations.extend(self.get_annotation(objects, image_id, object_answers, object_actions))

                elif "application/dicom" in data_unit["data_type"]:
                    # copy pasta:
                    for frame_num, frame_item in data_unit["labels"].items():
                        image_id = self.get_image_id(data_hash, int(frame_num))
                        objects = frame_item["objects"]
                        annotations.extend(self.get_annotation(objects, image_id, object_answers, object_actions))

                else:
                    image_id = self.get_image_id(data_hash)
                    objects = data_unit["labels"]["objects"]
                    annotations.extend(self.get_annotation(objects, image_id, object_answers, object_actions))

        return annotations

    # TODO: naming with plural/singular
    def get_annotation(
        self, objects: List[dict], image_id: int, object_answers: dict, object_actions: dict
    ) -> List[dict]:
        annotations = []
        for object_ in objects:
            shape = object_["shape"]

            # TODO: abstract this
            for image_data in self._coco_json["images"]:
                if image_data["id"] == image_id:
                    size = Size(width=image_data["width"], height=image_data["height"])

            # TODO: would be nice if this shape was an enum => with the Json support.
            if shape == Shape.BOUNDING_BOX.value:
                # TODO: how can I make sure this can be extended properly? At what point do I transform this to a JSON?
                # maybe I can have an `asdict` if this is a dataclass, else just keep the json and have the return type
                # be a union?!
                annotations.append(
                    as_dict_custom(self.get_bounding_box(object_, image_id, size, object_answers, object_actions))
                )
            if shape == Shape.ROTATABLE_BOUNDING_BOX.value:
                annotations.append(
                    as_dict_custom(
                        self.get_rotatable_bounding_box(object_, image_id, size, object_answers, object_actions)
                    )
                )
            elif shape == Shape.POLYGON.value:
                annotations.append(as_dict_custom(self.get_polygon(object_, image_id, size)))
            elif shape == Shape.POLYLINE.value:
                annotations.append(as_dict_custom(self.get_polyline(object_, image_id, size)))
            elif shape == Shape.POINT.value:
                annotations.append(as_dict_custom(self.get_point(object_, image_id, size)))
            elif shape == Shape.SKELETON.value:
                annotations.append(as_dict_custom(self.get_skeleton(object_, image_id, size)))

        return annotations

    def get_bounding_box(
        self, object_: dict, image_id: int, size: Size, object_answers: dict, object_actions: dict
    ) -> Union[CocoAnnotation, SuperClass]:
        x, y = (
            object_["boundingBox"]["x"] * size.width,
            object_["boundingBox"]["y"] * size.height,
        )
        w, h = (
            object_["boundingBox"]["w"] * size.width,
            object_["boundingBox"]["h"] * size.height,
        )
        area = w * h
        segmentation = [[x, y, x + w, y, x + w, y + h, x, y + h]]
        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id_, iscrowd, track_id, encord_track_uuid = self.get_coco_annotation_default_fields(object_)

        if self._include_flat_classifications:
            classifications: Optional[dict] = self.get_flat_classifications(
                object_, image_id, object_answers, object_actions
            )
        else:
            classifications = None

        return CocoAnnotation(
            area,
            bbox,
            category_id,
            id_,
            image_id,
            iscrowd,
            segmentation,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            classifications=classifications,
        )

    def get_rotatable_bounding_box(
        self, object_: dict, image_id: int, size: Size, object_answers: dict, object_actions: dict
    ) -> Union[CocoAnnotation, SuperClass]:
        x, y = (
            object_["rotatableBoundingBox"]["x"] * size.width,
            object_["rotatableBoundingBox"]["y"] * size.height,
        )
        w, h = (
            object_["rotatableBoundingBox"]["w"] * size.width,
            object_["rotatableBoundingBox"]["h"] * size.height,
        )
        area = w * h
        segmentation = [[x, y, x + w, y, x + w, y + h, x, y + h]]
        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id_, iscrowd, track_id, encord_track_uuid = self.get_coco_annotation_default_fields(object_)
        if self._include_bounding_box_rotation:
            rotation = object_["rotatableBoundingBox"]["theta"]
        else:
            rotation = None

        if self._include_flat_classifications:
            classifications: Optional[dict] = self.get_flat_classifications(
                object_, image_id, object_answers, object_actions
            )
        else:
            classifications = None

        return CocoAnnotation(
            area,
            bbox,
            category_id,
            id_,
            image_id,
            iscrowd,
            segmentation,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=rotation,
            classifications=classifications,
        )

    def get_flat_classifications(
        self, object_: dict, image_id: int, object_answers: dict, object_actions: dict
    ) -> dict:
        object_hash = object_["objectHash"]

        feature_hash_to_attribute_map: Dict[str, Attribute] = self.feature_hash_to_flat_object_attribute_map()
        id_and_object_hash_to_answers_map = self.get_id_and_object_hash_to_answers_map(
            object_actions, feature_hash_to_attribute_map
        )
        # DENIS: ^ these should happen only once outside of the individual paths.

        # DENIS: make sure that I use the object_answers etc. to get the flat attributes.
        classifications = self.get_flat_static_classifications(
            object_hash, object_answers, feature_hash_to_attribute_map
        )
        dynamic_classifications = self.get_flat_dynamic_classifications(
            object_hash, image_id, id_and_object_hash_to_answers_map
        )
        classifications.update(dynamic_classifications)
        # ^ deliberately possibly overwriting static classifications and thus giving dynamic classifications a
        # priority. However, an overwrite should technically not be possible if the label structure is set up correctly.

        return classifications

    def feature_hash_to_flat_object_attribute_map(self) -> Dict[str, Attribute]:
        res: Dict[str, Attribute] = {}

        for object_ in self._ontology.objects:
            for attribute in object_.attributes:
                res[attribute.feature_node_hash] = attribute

        return res

    def get_flat_static_classifications(
        self, object_hash: str, object_answers: dict, feature_hash_to_attribute_map: Dict[str, Attribute]
    ) -> dict:
        res = {}
        classifications = object_answers[object_hash]["classifications"]
        for classification in classifications:
            feature_hash = classification["featureHash"]
            if feature_hash not in feature_hash_to_attribute_map:
                # This will be a deeply nested attribute
                continue

            attribute = feature_hash_to_attribute_map[feature_hash]
            answers = classification["answers"]

            if attribute.get_property_type() == PropertyType.TEXT:
                res.update(self.get_text_answer(attribute, answers))
            elif attribute.get_property_type() == PropertyType.RADIO:
                res.update(self.get_radio_answer(attribute, answers))
            elif attribute.get_property_type() == PropertyType.CHECKLIST:
                res.update(self.get_checklist_answer(attribute, answers))

        return res

    def get_id_and_object_hash_to_answers_map(
        self, object_actions: dict, feature_hash_to_attribute_map: Dict[str, Attribute]
    ) -> Dict[Tuple[int, str], dict]:
        res = defaultdict(dict)
        # DENIS: seems like this is only getting the first???
        for object_hash, payload in object_actions.items():
            for action in payload["actions"]:
                feature_hash = action["featureHash"]
                if feature_hash not in feature_hash_to_attribute_map:
                    # This will be a deeply nested attribute
                    continue

                attribute = feature_hash_to_attribute_map[feature_hash]
                answers = action["answers"]
                answers_dict = {}
                if attribute.get_property_type() == PropertyType.TEXT:
                    answers_dict.update(self.get_text_answer(attribute, answers))
                elif attribute.get_property_type() == PropertyType.RADIO:
                    answers_dict.update(self.get_radio_answer(attribute, answers))
                elif attribute.get_property_type() == PropertyType.CHECKLIST:
                    answers_dict.update(self.get_checklist_answer(attribute, answers))

                for sub_range in action["range"]:
                    for i in range(sub_range[0], sub_range[1] + 1):
                        res[(i, object_hash)].update(answers_dict)

        return res

    def get_flat_dynamic_classifications(
        self, object_hash: str, image_id: int, id_and_object_hash_to_answers_map: Dict[Tuple[int, str], dict]
    ) -> dict:
        id_and_object_hash = (image_id, object_hash)
        if id_and_object_hash in id_and_object_hash_to_answers_map:
            return id_and_object_hash_to_answers_map[(image_id, object_hash)]
        else:
            return {}

    def get_radio_answer(self, attribute: Attribute, answers: dict) -> dict:
        answer = answers[0]  # radios only have one answer by definition
        return {attribute.name: answer["name"]}

    def get_checklist_answer(self, attribute: Attribute, answers: dict) -> dict:
        # DENIS: I think this will require the ontology to see what is "False"
        #  consider the flattening out of the attributes coming from CVAT. Think what would be good for Elbit but also
        #  other clients.
        res = {}
        found_checklist_answers = set()
        for answer in answers:
            found_checklist_answers.add(answer["name"])

        for option in attribute.options:
            label = option.label
            res[label] = label in found_checklist_answers

        return res

    def get_text_answer(self, attribute: Attribute, answers: str) -> dict:
        return {attribute.name: answers}

    def get_polygon(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        polygon = get_polygon_from_dict(object_["polygon"], size.width, size.height)
        segmentation = [list(chain(*polygon))]
        polygon = Polygon(polygon)
        area = polygon.area
        x, y, x_max, y_max = polygon.bounds
        w, h = x_max - x, y_max - y

        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id_, iscrowd, track_id, encord_track_uuid = self.get_coco_annotation_default_fields(object_)

        return CocoAnnotation(
            area,
            bbox,
            category_id,
            id_,
            image_id,
            iscrowd,
            segmentation,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
        )

    def get_polyline(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        """Polylines are technically not supported in COCO, but here we use a trick to allow a representation."""
        polygon = get_polygon_from_dict(object_["polyline"], size.width, size.height)
        polyline_coordinate = self.join_polyline_from_polygon(list(chain(*polygon)))
        segmentation = [polyline_coordinate]
        area = 0
        bbox = self.get_bbox_for_polyline(polygon)
        category_id = self.get_category_id(object_)
        id_, iscrowd, track_id, encord_track_uuid = self.get_coco_annotation_default_fields(object_)

        return CocoAnnotation(
            area,
            bbox,
            category_id,
            id_,
            image_id,
            iscrowd,
            segmentation,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
        )

    def get_bbox_for_polyline(self, polygon: list):
        if len(polygon) == 2:
            # We have the edge case of a single edge polygon.
            first_point = polygon[0]
            second_point = polygon[1]
            x = min(first_point[0], second_point[0])
            y = min(first_point[1], second_point[1])
            w = abs(first_point[0] - second_point[0])
            h = abs(first_point[1] - second_point[1])
            return [x, y, w, h]
        else:
            polygon = Polygon(polygon)
            x, y, x_max, y_max = polygon.bounds
            w, h = x_max - x, y_max - y

            return [x, y, w, h]

    @staticmethod
    def join_polyline_from_polygon(polygon: List[float]) -> List[float]:
        """
        Essentially a trick to represent a polyline in coco. We pretend for this to be a polygon and join every
        coordinate from the end back to the beginning, so it will essentially be an area-less polygon.
        This function technically changes the input polygon in place.
        """
        if len(polygon) % 2 != 0:
            raise RuntimeError("The polygon has an unaccepted shape.")

        idx = len(polygon) - 2
        while idx >= 0:
            y_coordinate = polygon[idx]
            x_coordinate = polygon[idx + 1]
            polygon.append(y_coordinate)
            polygon.append(x_coordinate)
            idx -= 2

        return polygon

    def get_point(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        x, y = (
            object_["point"]["0"]["x"] * size.width,
            object_["point"]["0"]["y"] * size.height,
        )
        w, h = 0, 0
        area = 0
        segmentation = [[x, y]]
        keypoints = [x, y, 2]
        num_keypoints = 1

        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id_, iscrowd, track_id, encord_track_uuid = self.get_coco_annotation_default_fields(object_)

        return CocoAnnotation(
            area,
            bbox,
            category_id,
            id_,
            image_id,
            iscrowd,
            segmentation,
            keypoints,
            num_keypoints,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
        )

    def get_skeleton(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        # TODO: next up: check how this is visualised.
        area = 0
        segmentation = []
        keypoints = []
        for point in object_["skeleton"].values():
            keypoints += [
                point["x"] * size.width,
                point["y"] * size.height,
                2,
            ]
        num_keypoints = len(keypoints) // 3
        xs, ys = (
            keypoints[::3],
            keypoints[1::3],
        )
        x, y, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
        w, h = x_max - x, y_max - y

        # TODO: think if the next two lines should be in `get_coco_annotation_default_fields`
        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id_, iscrowd, track_id, encord_track_uuid = self.get_coco_annotation_default_fields(object_)

        return CocoAnnotation(
            area,
            bbox,
            category_id,
            id_,
            image_id,
            iscrowd,
            segmentation,
            keypoints,
            num_keypoints,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
        )

    def get_category_id(self, object_: dict) -> int:
        feature_hash = object_["featureHash"]
        try:
            return self._feature_hash_to_coco_category_id_map[feature_hash]
        except KeyError:
            raise EncodingError(
                f"The feature_hash `{feature_hash}` was not found in the provided ontology. Please "
                f"ensure that the ontology matches the labels provided."
            )

    def get_coco_annotation_default_fields(self, object_: dict) -> Tuple[int, int, Optional[str], Optional[str]]:
        id_ = self.next_annotation_id()
        iscrowd = 0
        if self._include_track_id:
            track_id = self.get_and_set_track_id(object_hash=object_["objectHash"])
            encord_track_uuid = object_["objectHash"]
        else:
            track_id = None
            encord_track_uuid = None

        return id_, iscrowd, track_id, encord_track_uuid

    def next_annotation_id(self) -> int:
        next_ = self._current_annotation_id
        self._current_annotation_id += 1
        return next_

    def get_and_set_track_id(self, object_hash: str) -> int:
        if object_hash in self._object_hash_to_track_id_map:
            return self._object_hash_to_track_id_map[object_hash]
        else:
            next_track_id = len(self._object_hash_to_track_id_map)
            self._object_hash_to_track_id_map[object_hash] = next_track_id
            return next_track_id

    def download_image(self, url: str, path: Path):
        """Check if directory exists, create the directory if needed, download the file, store it into the path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        download_file(url, path)

    def get_image_id(self, data_hash: str, frame_num: int = 0) -> int:
        return self._data_hash_to_image_id_map[(data_hash, frame_num)]


def download_file(
    url: str,
    destination: Path,
    byte_size=1024,
    progress=tqdm,
):
    iterations = int(int(requests.head(url).headers["Content-Length"]) / byte_size) + 1
    r = requests.get(url, stream=True)

    if progress is None:

        def nop(it, *a, **k):
            return it

        progress = nop

    with open(destination, "wb") as f:
        for chunk in progress(r.iter_content(chunk_size=1024), total=iterations, desc="Downloading "):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return destination


#
def extract_frames(video_file_name: Path, img_dir: Path):
    logger.info(f"Extracting frames from video: {video_file_name}")

    # TODO: for the rest to work, I will need to throw if the current directory exists and give a nice user warning.
    img_dir.mkdir(parents=True, exist_ok=True)
    command = f"ffmpeg -i {video_file_name} -start_number 0 {img_dir}/%d.jpg -hide_banner"
    if subprocess.run(command, shell=True, capture_output=True, stdout=None, check=True).returncode != 0:
        raise RuntimeError(
            "Splitting videos into multiple image files failed. Please ensure that you have FFMPEG "
            f"installed on your machine: https://ffmpeg.org/download.html The comamand that failed was `{command}`."
        )


#
#
# def get_data_unit_image(
#     data_unit: DataUnit, cache_dir: Path, download: bool = False, force: bool = False
# ) -> Optional[Path]:
#     """
#     Fetches image either from cache dir or by downloading and caching image. By default, only the image path will
#     be returned as a Path object.
#     Args:
#         data_unit: The data unit that specifies what image to fetch.
#         cache_dir: The directory to fetch cached results from, and to cache results to.
#         download: If download is true, download image. Otherwise, return None
#         force: Force refresh of cached content.
#
#     Returns: The image as a Path, numpy array, or PIL Image or None if image doesn't exist and `download == False`.
#     """
#     is_video = "video" in data_unit.data_type
#     if is_video:
#         video_hash, frame_idx = data_unit.data_hash.split("_")
#         video_dir = cache_dir / "videos"
#         video_file = f"{video_hash}.{data_unit.extension}"
#         img_dir = video_dir / video_hash
#         img_file = f"{frame_idx}.jpg"
#
#         os.makedirs(video_dir, exist_ok=True)
#     else:
#         img_dir = cache_dir / "images"
#         img_file = f"{data_unit.data_hash}.{data_unit.extension}"
#
#     full_img_pth = img_dir / img_file
#     torch_file = (img_dir / img_file).with_suffix(".pt")
#     if not (download or force) and not (full_img_pth.exists() or torch_file.exists()):
#         return None
#
#     if force or (download and not (full_img_pth.exists() or torch_file.exists())):
#         check_data_link(data_unit)
#         if is_video:
#             # Extract frames images
#             if not os.path.exists(video_dir / video_file):
#                 logger.info(f"Downloading video {video_file}")
#                 download_file(data_unit.data_link, video_dir, fname=video_file, progress=None)
#             extract_frames(video_dir / video_file, img_dir)
#             convert_frames_from_jpg_to_tensors(img_dir)
#         else:
#             logger.debug(f"Downloading image {full_img_pth}")
#             download_file(data_unit.data_link, img_dir, fname=img_file, progress=None)
#             replace_img_with_tensor(full_img_pth)
#
#     if torch_file.exists():
#         return torch_file
#     return full_img_pth
