"""DENIS: think properly about the structure, the transcoders and how we want to subclass or extend this so people
can plug into the different parts easily.

ideas
* a class where the individual parts can be overwritten
* a class where the individual transformers can be re-assigned
*
DENIS: how are we going to document this in Sphinx if this class is independent?

DENIS:
* parallel downloads with a specific flag
* saving the annotation file with a specific flag
* labels class for better type support.
"""
import logging
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from itertools import chain
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

import requests
from shapely.geometry import Polygon
from tqdm import tqdm

from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure
from encord.transformers.coco.coco_datastructure import (
    CocoAnnotation,
    SuperClass,
    as_dict_custom,
)

logger = logging.getLogger(__name__)


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
    # DENIS: this belongs in a utils folder.
    return Size(1, 2)  # A stub for now


def get_polygon_from_dict(polygon_dict, W, H):
    return [(polygon_dict[str(i)]["x"] * W, polygon_dict[str(i)]["y"] * H) for i in range(len(polygon_dict))]


# DENIS: TODO: focus on doing the parser for now for segmentations for images as it was intended. Seems like
#   for other formats I can still add stuff or have the clients extend what we have.

# DENIS: should these labels be the data structure that I've invented for them instead of the encord dict?
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
        self._coco_categories_id_to_ontology_object_map = dict()  # DENIS: do we need this?
        self._feature_hash_to_coco_category_id_map = dict()
        self._data_hash_to_image_id_map = dict()
        """Map of (data_hash, frame_offset) to the image id"""

        # self._data_location_to_image_id_map = dict()

        self._download_files = False
        self._download_file_path = Path(".")
        self._include_videos = True
        self._include_unannotated_videos = False

    # DENIS: think about the argument names now with "include videos"
    def encode(
        self,
        download_files: bool = False,
        download_file_path: Path = Path("."),
        include_videos: bool = True,
        include_unannotated_videos: bool = False,
    ) -> dict:
        """
        Args:
            download_files: If set to true, the images are downloaded into a local directory and the `coco_url` of the
                images will point to the location of the local directory. DENIS: can also maybe have a Path obj here.
            download_file_path:
                Root path to where the images and videos are downloaded or where downloaded images are looked up from.
                For example, if `include_unannotated_videos = True` then this is the root path of the
                `videos/<data_hash>` directory.
            include_unannotated_videos:
                This will be ignored if the files are not downloaded (whether they are being downloaded now or they
                were already there) in which case it will default to False. The code will assume that the video is
                downloaded and expanded correctly in the same way that would happen if the video was downloaded via
                the `download_files = True` argument.
        """
        self._download_files = download_files
        self._download_file_path = download_file_path
        self._include_videos = include_videos
        self._include_unannotated_videos = include_unannotated_videos

        self._coco_json["info"] = self.get_info()
        self._coco_json["categories"] = self.get_categories()
        self._coco_json["images"] = self.get_images()
        self._coco_json["annotations"] = self.get_annotations()

        return self._coco_json

    def get_info(self) -> dict:
        return {
            "description": self.get_description(),
            "contributor": None,  # TODO: these fields also need a response
            "date_created": None,  # DENIS: there is something in the labels, alternatively can start to return more from the SDK
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
        id_ = len(self._coco_categories_id_to_ontology_object_map)
        self._coco_categories_id_to_ontology_object_map[id_] = object_
        self._feature_hash_to_coco_category_id_map[object_.feature_node_hash] = id_
        return id_

    def get_category_name(self, object_: Object) -> str:
        return object_.name

    # DENIS: check how to do this with videos. => maybe return an additional map of id to frame number?!
    # DENIS: TODO: definitely branch off with videos with a NotImplementedError.
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
        # DENIS: we probably want a map of this image id to image hash in our DB, including the image_group hash.

        """
        DENIS: next up: here we need to branch off and create the videos
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
            # DENIS: log something for transparency?
            for frame_num in range(len(list(path_to_video_dir.iterdir()))):
                images.append(self.get_video_image(data_hash, video_title, coco_url, height, width, int(frame_num)))
        else:
            for frame_num in data_unit["labels"].keys():
                images.append(self.get_video_image(data_hash, video_title, coco_url, height, width, int(frame_num)))

        return images

    # def get_frame_numbers(self, data_unit: dict) -> Iterator:  # DENIS: use this to remove the above if/else.

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

        # DENIS: need to make sure at least one image
        for labels in self._labels_list:
            for data_unit in labels["data_units"].values():
                data_hash = data_unit["data_hash"]

                if "video" in data_unit["data_type"]:
                    if not self._include_videos:
                        continue
                    for frame_num, frame_item in data_unit["labels"].items():
                        image_id = self.get_image_id(data_hash, int(frame_num))
                        objects = frame_item["objects"]
                        annotations.extend(self.get_annotation(objects, image_id))

                elif "application/dicom" in data_unit["data_type"]:
                    # copy pasta:
                    for frame_num, frame_item in data_unit["labels"].items():
                        image_id = self.get_image_id(data_hash, int(frame_num))
                        objects = frame_item["objects"]
                        annotations.extend(self.get_annotation(objects, image_id))

                else:
                    image_id = self.get_image_id(data_hash)
                    objects = data_unit["labels"]["objects"]
                    annotations.extend(self.get_annotation(objects, image_id))

        return annotations

    # DENIS: naming with plural/singular
    def get_annotation(self, objects: List[dict], image_id: int) -> List[dict]:
        annotations = []
        for object_ in objects:
            shape = object_["shape"]

            # DENIS: abstract this
            for image_data in self._coco_json["images"]:
                if image_data["id"] == image_id:
                    size = Size(width=image_data["width"], height=image_data["height"])

            # DENIS: would be nice if this shape was an enum => with the Json support.
            if shape == "bounding_box":
                # DENIS: how can I make sure this can be extended properly? At what point do I transform this to a JSON?
                # maybe I can have an `asdict` if this is a dataclass, else just keep the json and have the return type
                # be a union?!
                annotations.append(as_dict_custom(self.get_bounding_box(object_, image_id, size)))
            elif shape == "polygon":
                annotations.append(as_dict_custom(self.get_polygon(object_, image_id, size)))
            elif shape == "polyline":
                annotations.append(as_dict_custom(self.get_polyline(object_, image_id, size)))
            elif shape == "point":
                annotations.append(as_dict_custom(self.get_point(object_, image_id, size)))
            elif shape == "skeleton":
                annotations.append(as_dict_custom(self.get_skeleton(object_, image_id, size)))

        return annotations

    def get_bounding_box(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
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
        id, iscrowd = self.get_coco_annotation_default_fields()

        return CocoAnnotation(area, bbox, category_id, id, image_id, iscrowd, segmentation)

    def get_polygon(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        polygon = get_polygon_from_dict(object_["polygon"], size.width, size.height)
        segmentation = [list(chain(*polygon))]
        polygon = Polygon(polygon)
        area = polygon.area
        x, y, x_max, y_max = polygon.bounds
        w, h = x_max - x, y_max - y

        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id, iscrowd = self.get_coco_annotation_default_fields()

        return CocoAnnotation(area, bbox, category_id, id, image_id, iscrowd, segmentation)

    def get_polyline(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        """Polylines are technically not supported in COCO, but here we use a trick to allow a representation."""
        polygon = get_polygon_from_dict(object_["polyline"], size.width, size.height)
        polyline_coordinate = self.join_polyline_from_polygon(list(chain(*polygon)))
        segmentation = [polyline_coordinate]
        area = 0
        bbox = self.get_bbox_for_polyline(polygon)
        category_id = self.get_category_id(object_)
        id, iscrowd = self.get_coco_annotation_default_fields()

        return CocoAnnotation(area, bbox, category_id, id, image_id, iscrowd, segmentation)

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
        id, iscrowd = self.get_coco_annotation_default_fields()

        return CocoAnnotation(area, bbox, category_id, id, image_id, iscrowd, segmentation, keypoints, num_keypoints)

    def get_skeleton(self, object_: dict, image_id: int, size: Size) -> Union[CocoAnnotation, SuperClass]:
        # DENIS: next up: check how this is visualised.
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

        # DENIS: think if the next two lines should be in `get_coco_annotation_default_fields`
        bbox = [x, y, w, h]
        category_id = self.get_category_id(object_)
        id, iscrowd = self.get_coco_annotation_default_fields()

        return CocoAnnotation(area, bbox, category_id, id, image_id, iscrowd, segmentation, keypoints, num_keypoints)

    def get_category_id(self, object_: dict) -> int:
        feature_hash = object_["featureHash"]
        try:
            return self._feature_hash_to_coco_category_id_map[feature_hash]
        except KeyError:
            raise EncodingError(
                f"The feature_hash `{feature_hash}` was not found in the provided ontology. Please "
                f"ensure that the ontology matches the labels provided."
            )

    def get_coco_annotation_default_fields(self) -> Tuple[int, int]:
        id = self.next_annotation_id()
        iscrowd = 0
        return id, iscrowd

    def next_annotation_id(self) -> int:
        next_ = self._current_annotation_id
        self._current_annotation_id += 1
        return next_

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

    # DENIS: for the rest to work, I will need to throw if the current directory exists and give a nice user warning.
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
