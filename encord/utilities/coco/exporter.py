try:
    import cv2
    import pycocotools
    import shapely
except ImportError as e:
    raise ImportError(
        "The 'opencv-python', 'pycocotools' and 'shapely' packages are required for the COCO export. "
        "Install them with: `pip install encord[coco]`"
    ) from e

import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from pycocotools import mask as cocomask
from pydantic import BaseModel
from shapely.geometry import MultiPolygon, Polygon

from encord.exceptions import EncordException
from encord.objects.attributes import Attribute
from encord.objects.common import PropertyType, Shape
from encord.objects.ontology_object import Object
from encord.objects.ontology_structure import OntologyStructure

logger = logging.getLogger(__name__)

ShapelyPolygonRing = Tuple[Tuple[float, float], ...]
ShapelyPolygonHoles = List[ShapelyPolygonRing]
ShapelyPolygon = Union[Tuple[ShapelyPolygonRing,], Tuple[ShapelyPolygonRing, ShapelyPolygonHoles]]

PDF_MIME_TYPES = ["application/pdf"]
TEXT_MIME_TYPES = ["application/json", "application/xml", "text/plain", "text/html", "text/xml"]
DICOM_MIME_TYPE = "application/dicom"
NIFTI1_MIME_TYPE = "application/nifti1"
NIFTI2_MIME_TYPE = "application/nifti2"
NIFTI_MIME_TYPES = {NIFTI1_MIME_TYPE, NIFTI2_MIME_TYPE}


@dataclass(frozen=True)
class DicomAnnotationData:
    dicom_instance_uid: str
    multiframe_frame_number: Optional[int]  # only present for multi-frame DICOMs
    file_uri: str
    width: int
    height: int


# See https://cocodataset.org/#format-data, section 2. Keypoint Detection
class KeyPointVisibility(Enum):
    NOT_LABELED = 0
    NOT_VISIBLE = 1
    VISIBLE = 2


class CocoAnnotation(BaseModel):
    area: float
    bbox: Tuple[float, float, float, float]
    category_id: int
    id_: int
    image_id: int
    is_crowd: int
    segmentation: Union[List[List[float]], Dict[str, Any]]
    keypoints: Optional[List[float]] = None
    num_keypoints: Optional[int] = None
    track_id: Optional[int] = None
    encord_track_uuid: Optional[str] = None
    rotation: Optional[float] = None
    classifications: Optional[Dict[str, Any]] = None
    manual_annotation: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "area": self.area,
            "bbox": list(self.bbox),
            "category_id": self.category_id,
            "image_id": self.image_id,
            "iscrowd": self.is_crowd,
            "segmentation": self.segmentation,
            "keypoints": self.keypoints,
            "num_keypoints": self.num_keypoints,
            "id": self.id_,
            "attributes": {
                k: v
                for k, v in {
                    "track_id": self.track_id,
                    "encord_track_uuid": self.encord_track_uuid,
                    "rotation": self.rotation,
                    "classifications": self.classifications,
                    "manual_annotation": self.manual_annotation,
                }.items()
                if v is not None
            },
        }


@dataclass
class Size:
    width: int
    height: int


class CocoExporter:
    """This class is intentionally designed in a modular fashion to facilitate extensibility.
    You are encouraged to subclass this exporter and modify any of the custom functions.
    While return types are provided for convenience, they can also be subclassed to suit your specific requirements.
    All functions that could be static are intentionally not made static, allowing you the option to access the `self`
    object at any time.
    """

    def __init__(
        self,
        labels_list: List[Dict[str, Any]],
        ontology: OntologyStructure,
        include_videos: bool = True,
    ) -> None:
        self._labels_list = labels_list
        self._ontology = ontology
        self._coco_json: Dict[str, Any] = {}
        self._current_annotation_id = 0
        self._object_hash_to_track_id_map: Dict[str, int] = {}
        self._coco_categories_id_to_ontology_object_map: Dict = {}  # TODO: do we need this?
        self._feature_hash_to_coco_category_id_map: Dict[str, int] = {}
        self._data_hash_to_image_id_map: Dict[Tuple[str, int], int] = {}
        """Map of (data_hash, frame_offset) to the image id"""

        self._feature_hash_to_attribute_map: Optional[Dict[str, Attribute]] = None
        self._id_and_object_hash_to_answers_map: Optional[Dict[Tuple[int, str], Dict]] = None
        self._include_videos = include_videos

    def export(self) -> Dict[str, Any]:
        self._coco_json["info"] = self.get_info()
        self._coco_json["categories"] = self.get_categories()
        self._coco_json["images"] = self.get_images()
        self._coco_json["annotations"] = [x.to_dict() for x in self.get_all_annotations()]

        return self._coco_json

    def get_info(self) -> Dict[str, Optional[str]]:
        return {
            "description": self.get_description(),
            "contributor": None,  # TODO: these fields also need a response
            "date_created": None,
            # TODO: there is something in the labels, alternatively can start to return more from the SDK
            "url": None,
            "version": None,
            "year": None,
        }

    def get_description(self) -> Optional[str]:
        if len(self._labels_list) == 0:
            res: Optional[str] = None
        else:
            res = str(self._labels_list[0]["data_title"])

        return res

    def get_categories(self) -> List[Dict[str, Any]]:
        """This does not translate classifications as they are not part of the Coco spec."""
        categories = []
        for object_ in self._ontology.objects:
            # skip special object types
            if object_.shape in (Shape.AUDIO, Shape.TEXT):
                continue
            categories.append(self.get_category(object_))

        return categories

    def get_category(self, object_: Object) -> Dict[str, Any]:
        super_category = self.get_super_category(object_)
        ret: Dict[str, Any] = {
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
        # Let the category id start at 1, not 0. Segmentation masks that use COCO annotations often create a bitmask
        # with this category id. The bitmask must be above 0. See this link:
        # https://cocodataset.org/#stuff-eval
        self._coco_categories_id_to_ontology_object_map[id_] = object_
        self._feature_hash_to_coco_category_id_map[object_.feature_node_hash] = id_

        return id_

    def get_category_name(self, object_: Object) -> str:
        return object_.name

    def get_images(self) -> List[Dict[str, Any]]:
        """All the data is in the specific label_row"""
        images = []

        for labels in self._labels_list:
            cord_data_type = labels["data_type"]  # This is set to FileType Enum
            for data_unit in labels["data_units"].values():
                data_type = data_unit["data_type"]
                if "application/dicom" in data_type:
                    images.extend(self.get_dicom(data_unit))
                elif data_type in NIFTI_MIME_TYPES:
                    images.extend(self.get_nifti(data_unit))
                elif data_type in PDF_MIME_TYPES:
                    continue
                elif data_type in TEXT_MIME_TYPES:
                    continue
                elif cord_data_type.upper() == "AUDIO":
                    continue
                elif "video" not in data_type:
                    images.append(self.get_image(data_unit))
                else:
                    images.extend(self.get_video_images(data_unit))

        return images

    def get_dicom(self, data_unit: Dict) -> List:
        return [
            self._dicom_label_to_coco_image(
                int(key), data_unit["data_hash"], data_unit["width"], data_unit["height"], label
            )
            for key, label in data_unit["labels"].items()
        ]

    def get_nifti(self, data_unit: dict) -> List:
        return [
            self._nifti_label_to_coco_image(
                data_unit["data_hash"],
                data_unit["data_link"],
                data_unit["height"],
                data_unit["width"],
                int(key),
            )
            for key in data_unit["labels"].keys()
        ]

    def get_image(self, data_unit: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: we probably want a map of this image id to image hash in our DB, including the image_group hash.
        image_id = len(self._data_hash_to_image_id_map)
        data_hash = data_unit["data_hash"]
        self._data_hash_to_image_id_map[(data_hash, 0)] = image_id

        return {
            "coco_url": data_unit["data_link"],
            "id": image_id,
            "image_title": data_unit["data_title"],
            "file_name": f'images/{data_unit["data_hash"]}.{data_unit["data_title"].split(".")[-1]}',
            "height": data_unit["height"],
            "width": data_unit["width"],
        }

    def get_video_images(self, data_unit: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self._include_videos:
            return []

        video_title = data_unit["data_title"]
        data_hash = data_unit["data_hash"]

        images = []
        coco_url = data_unit["data_link"]
        height = data_unit["height"]
        width = data_unit["width"]

        for frame_num in data_unit["labels"].keys():
            images.append(
                self.get_video_image(
                    data_hash,
                    video_title,
                    coco_url,
                    height,
                    width,
                    int(frame_num),
                )
            )

        return images

    def _dicom_label_to_coco_image(
        self, frame: int, data_hash: str, series_width: int, series_height: int, dicom_label: Dict
    ) -> Dict[str, Any]:
        image_id = len(self._data_hash_to_image_id_map)
        # ideally this should be verify_arg, but currently we can't be sure that the metadata is on every frame
        metadata = DicomAnnotationData(**dicom_label["metadata"]) if "metadata" in dicom_label else None
        self._data_hash_to_image_id_map[(data_hash, frame)] = image_id
        if metadata:
            file_name = f"dicom/{data_hash}/{metadata.dicom_instance_uid}"
            if metadata.multiframe_frame_number is not None:
                file_name += f"/{metadata.multiframe_frame_number}"

            return {
                "coco_url": metadata.file_uri,
                "id": image_id,
                "file_name": file_name,
                "height": metadata.height,
                "width": metadata.width,
            }
        else:
            return {
                "coco_url": "",
                "id": image_id,
                "file_name": f"dicom/{data_hash}/{frame}",
                "height": series_height,
                "width": series_width,
            }

    def _nifti_label_to_coco_image(
        self,
        data_hash: str,
        coco_url: str,
        height: int,
        width: int,
        frame_num: int,
    ) -> Dict[str, Any]:
        image_id = len(self._data_hash_to_image_id_map)
        self._data_hash_to_image_id_map[(data_hash, frame_num)] = image_id

        return {
            "coco_url": coco_url,
            "id": image_id,
            "file_name": f"nifti/{data_hash}/{frame_num}",
            "height": height,
            "width": width,
        }

    def get_pdf_coco_image(self, data_hash: str, coco_url: str, frame_num: int) -> Dict[str, Any]:
        page_id = len(self._data_hash_to_image_id_map)
        self._data_hash_to_image_id_map[(data_hash, frame_num)] = page_id

        return {
            "coco_url": coco_url,
            "id": page_id,
            "file_name": f"pdfs/{data_hash}/{frame_num}",
            "height": 0,
            "width": 0,
        }

    def get_video_image(
        self,
        data_hash: str,
        video_title: str,
        coco_url: str,
        height: int,
        width: int,
        frame_num: int,
    ) -> Dict[str, Any]:
        image_id = len(self._data_hash_to_image_id_map)
        self._data_hash_to_image_id_map[(data_hash, frame_num)] = image_id

        return {
            "coco_url": coco_url,
            "id": image_id,
            "video_title": video_title,
            "file_name": f"videos/{data_hash}/{frame_num}.jpg",
            "height": height,
            "width": width,
        }

    def get_all_annotations(self) -> List[CocoAnnotation]:
        annotations = []

        # TODO: need to make sure at least one image
        for labels in self._labels_list:
            object_answers = labels["object_answers"]
            object_actions = labels["object_actions"]
            cord_data_type = labels["data_type"]  # This is set to FileType Enum

            for data_unit in labels["data_units"].values():
                data_hash = data_unit["data_hash"]
                data_type = data_unit["data_type"]

                is_video = "video" in data_type
                if is_video and not self._include_videos:
                    continue

                if is_video or data_type == DICOM_MIME_TYPE or data_type in NIFTI_MIME_TYPES:
                    for frame_num, frame_item in data_unit["labels"].items():
                        image_id = self.get_image_id(data_hash, int(frame_num))
                        objects = frame_item["objects"]
                        annotations.extend(
                            self.get_annotations(
                                objects,
                                image_id,
                                object_answers,
                                object_actions,
                            )
                        )
                elif data_type in PDF_MIME_TYPES:
                    continue
                elif data_type in TEXT_MIME_TYPES:
                    continue
                elif cord_data_type.upper() == "AUDIO":
                    continue
                else:
                    image_id = self.get_image_id(data_hash)
                    objects = data_unit["labels"].get("objects") or []
                    annotations.extend(
                        self.get_annotations(
                            objects,
                            image_id,
                            object_answers,
                            object_actions,
                        )
                    )

        return annotations

    def get_annotations(
        self,
        objects: List[Dict],
        image_id: int,
        object_answers: Dict,
        object_actions: Dict,
    ) -> List[CocoAnnotation]:
        annotations = []

        for object_ in objects:
            shape = object_["shape"]

            for image_data in self._coco_json["images"]:
                if image_data["id"] == image_id:
                    # Ensure a size of 1 for non-geometric data types
                    size = Size(
                        width=max(1, image_data["width"]),
                        height=max(1, image_data["height"]),
                    )

            if shape == Shape.BOUNDING_BOX.value:
                annotations.append(
                    self.get_bounding_box(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )
            elif shape == Shape.ROTATABLE_BOUNDING_BOX.value:
                annotations.append(
                    self.get_rotatable_bounding_box(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )
            elif shape == Shape.POLYGON.value:
                annotations.append(
                    self.get_polygon(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )
            elif shape == Shape.POLYLINE.value:
                annotations.append(
                    self.get_polyline(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )
            elif shape == Shape.BITMASK.value:
                annotations.append(
                    self.get_bitmask(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )
            elif shape == Shape.POINT.value:
                annotations.append(
                    self.get_point(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )
            elif shape == Shape.SKELETON.value:
                annotations.append(
                    self.get_skeleton(
                        object_,
                        image_id,
                        size,
                        object_answers,
                        object_actions,
                    )
                )

        return annotations

    def get_bounding_box(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
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
        bbox = (x, y, w, h)
        category_id = self.get_category_id(object_)
        id_, is_crowd, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)

        classifications = self.get_flat_classifications(object_, image_id, object_answers, object_actions)

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=None,
            num_keypoints=None,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=None,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_rotatable_bounding_box(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
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
        bbox = (x, y, w, h)
        category_id = self.get_category_id(object_)
        id_, is_crowd, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)

        rotation = object_["rotatableBoundingBox"]["theta"]

        classifications = self.get_flat_classifications(object_, image_id, object_answers, object_actions)

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=None,
            num_keypoints=None,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=rotation,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_polygon(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
        category_id = self.get_category_id(object_)
        id_, is_crowd, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)

        is_multipolygon = (
            # Check if the object contains the new [complex] 'polygons' field
            object_.get("polygons")
            and (
                # A multipolygon is either:
                # - More than one polygon present
                len(object_["polygons"]) > 1
                or
                # - A single polygon that contains holes (more than one contour)
                len(object_["polygons"][0]) > 1
            )
        )
        # Since COCO format doesn't support multipolygons, we must RLE encode complex polygons.
        if is_multipolygon:
            is_crowd = 1
            multipolygon = MultiPolygon(
                self.get_multipolygon_from_polygons(object_["polygons"], size.width, size.height)
            )
            segmentation = self.get_rle_segmentation_from_multipolygon(multipolygon, size.width, size.height)
            bbox = tuple(cocomask.toBbox(segmentation))
            area = float(cocomask.area(segmentation))
        else:
            polygon = self.get_polygon_from_dict_or_list(object_["polygon"], size.width, size.height)
            _polygon = Polygon(polygon)
            segmentation = [list(chain(*polygon))]
            area = _polygon.area
            x, y, x_max, y_max = _polygon.bounds
            w, h = x_max - x, y_max - y
            bbox = (x, y, w, h)

        classifications = self.get_flat_classifications(
            object_,
            image_id,
            object_answers,
            object_actions,
        )

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=None,
            num_keypoints=None,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=None,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_polygon_from_dict_or_list(
        self,
        polygon_dict: Union[Dict[str, Any], List],
        w: int,
        h: int,
    ) -> List[Tuple[float, float]]:
        if isinstance(polygon_dict, list):
            return [(point["x"] * w, point["y"] * h) for point in polygon_dict]
        else:
            return [
                (
                    polygon_dict[str(i)]["x"] * w,
                    polygon_dict[str(i)]["y"] * h,
                )
                for i in range(len(polygon_dict))
            ]

    def convert_point_list_to_tuples(
        self,
        points_list: List[float],
        w: int,
        h: int,
    ) -> ShapelyPolygonRing:
        it = iter(points_list)

        return tuple([(t[0] * w, t[1] * h) for t in zip(it, it)])

    def convert_polygon_points_list_to_polygon(
        self,
        polygon_points_list: List[List[float]],
        w: int,
        h: int,
    ) -> ShapelyPolygon:
        [ring, *holes] = polygon_points_list

        polygon_ring = self.convert_point_list_to_tuples(ring, w, h)

        if len(holes) > 0:
            return (polygon_ring, [self.convert_point_list_to_tuples(hole, w, h) for hole in holes])
        else:
            return (polygon_ring,)

    def get_rle_segmentation_from_multipolygon(self, multipolygon: MultiPolygon, w: int, h: int):  # type: ignore[no-untyped-def]
        mask = np.zeros((h, w), dtype=np.uint8)
        for polygon in sorted(multipolygon.geoms, key=lambda p: p.area, reverse=True):
            # mypy being silly -- List item 0 has incompatible type "ndarray[Any, dtype[signedinteger[_32Bit]]]"; expected "Mat"
            exterior = np.array(polygon.exterior.coords, dtype=np.int32)
            cv2.fillPoly(mask, [exterior], color=(255, 255, 255))  # type: ignore[list-item]
            for interior in polygon.interiors:
                cv2.fillPoly(mask, [np.array(interior.coords, dtype=np.int32)], color=(0, 0, 0))  # type: ignore[list-item]

        # Obtain the COCO compatible RLE string (convert from row-major to column-major order)
        segmentation = cocomask.encode(np.asfortranarray(mask))
        # Convert RLE string from bytes (which is not a JSON serializable type) to a string format
        segmentation["counts"] = segmentation["counts"].decode("ascii")

        return segmentation

    def get_multipolygon_from_polygons(
        self,
        polygons: List[List[List[float]]],
        w: int,
        h: int,
    ) -> List[ShapelyPolygon]:
        return [self.convert_polygon_points_list_to_polygon(polygon, w, h) for polygon in polygons]

    def get_polyline(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
        """Polylines are technically not supported in COCO, but here we use a trick to allow a representation."""
        polygon = self.get_polygon_from_dict_or_list(object_["polyline"], size.width, size.height)
        polyline_coordinate = self.join_polyline_from_polygon(list(chain(*polygon)))
        segmentation = [polyline_coordinate]
        area = 0
        bbox = self.get_bbox_for_polyline(polygon)
        category_id = self.get_category_id(object_)
        id_, is_crowd, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)

        classifications = self.get_flat_classifications(object_, image_id, object_answers, object_actions)

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=None,
            num_keypoints=None,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=None,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_bbox_for_polyline(
        self,
        polygon: List[Tuple[float, float]],
    ) -> Tuple[float, float, float, float]:
        if len(polygon) == 2:
            # We have the edge case of a single edge polygon.
            first_point = polygon[0]
            second_point = polygon[1]
            x = float(min(first_point[0], second_point[0]))
            y = float(min(first_point[1], second_point[1]))
            w = float(abs(first_point[0] - second_point[0]))
            h = float(abs(first_point[1] - second_point[1]))
            return x, y, w, h
        else:
            shapely_polygon = Polygon(polygon)
            x, y, x_max, y_max = shapely_polygon.bounds  # type: ignore[attr-defined]
            w, h = x_max - x, y_max - y

            return x, y, w, h

    @staticmethod
    def join_polyline_from_polygon(
        polygon: List[float],
    ) -> List[float]:
        """Essentially a trick to represent a polyline in coco. We pretend for this to be a polygon and join every
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

    def get_bitmask(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
        bitmask = object_["bitmask"]
        # Note: It's essential to transpose the input and output coordinates when using pycocotools' functions,
        # in order to address the distinction between treating masks as C-contiguous (row-major order, Encord's
        # implementation) versus pycocotools' expectation of Fortran-contiguous (column-major order, COCO's API
        # implementation) data.

        # Obtain the COCO compatible RLE string (convert from row-major to column-major order)
        transposed_segmentation = dict(counts=bitmask["rleString"], size=[bitmask["width"], bitmask["height"]])
        mask = np.asfortranarray(cocomask.decode(transposed_segmentation).T)
        segmentation = cocomask.encode(mask)
        bbox = tuple(cocomask.toBbox(segmentation))
        area = float(cocomask.area(segmentation))
        # Convert RLE string from bytes (which is not a JSON serializable type) to a string format
        segmentation["counts"] = segmentation["counts"].decode("ascii")

        category_id = self.get_category_id(object_)
        id_, _, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)
        is_crowd = 1

        classifications: Optional[Dict] = self.get_flat_classifications(
            object_, image_id, object_answers, object_actions
        )

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=None,
            num_keypoints=None,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=None,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_point(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
        x, y = (
            object_["point"]["0"]["x"] * size.width,
            object_["point"]["0"]["y"] * size.height,
        )
        w, h = 0, 0
        area = 0
        segmentation = [[x, y]]
        keypoints = [x, y, KeyPointVisibility.VISIBLE.value]
        num_keypoints = 1

        bbox = (x, y, w, h)
        category_id = self.get_category_id(object_)
        id_, is_crowd, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)

        classifications: Optional[Dict] = self.get_flat_classifications(
            object_, image_id, object_answers, object_actions
        )

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=keypoints,
            num_keypoints=num_keypoints,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=None,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_skeleton(
        self,
        object_: Dict,
        image_id: int,
        size: Size,
        object_answers: Dict,
        object_actions: Dict,
    ) -> CocoAnnotation:
        area = 0
        segmentation: List = []
        keypoints = []

        for point in object_["skeleton"].values():
            keypoints += [
                point["x"] * size.width,
                point["y"] * size.height,
                self.get_skeleton_point_visibility(point).value,
            ]

        num_keypoints = len(keypoints) // 3
        xs, ys = (
            keypoints[::3],
            keypoints[1::3],
        )
        x, y, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
        w, h = x_max - x, y_max - y

        bbox = (x, y, w, h)
        category_id = self.get_category_id(object_)
        id_, is_crowd, track_id, encord_track_uuid, manual_annotation = self.get_coco_annotation_default_fields(object_)

        classifications: Optional[Dict] = self.get_flat_classifications(
            object_, image_id, object_answers, object_actions
        )

        return CocoAnnotation(
            area=area,
            bbox=bbox,
            category_id=category_id,
            id_=id_,
            image_id=image_id,
            is_crowd=is_crowd,
            segmentation=segmentation,
            keypoints=keypoints,
            num_keypoints=num_keypoints,
            track_id=track_id,
            encord_track_uuid=encord_track_uuid,
            rotation=None,
            classifications=classifications,
            manual_annotation=manual_annotation,
        )

    def get_skeleton_point_visibility(self, point: dict) -> KeyPointVisibility:
        if point.get("invisible") is True:
            return KeyPointVisibility.NOT_LABELED
        elif point.get("occluded") is True:
            return KeyPointVisibility.NOT_VISIBLE
        else:
            return KeyPointVisibility.VISIBLE

    def get_flat_classifications(
        self, object_: Dict, image_id: int, object_answers: Dict, object_actions: Dict
    ) -> Dict[str, Any]:
        object_hash = object_["objectHash"]
        feature_hash = object_["featureHash"]

        feature_hash_to_attribute_map: Dict[str, Attribute] = self.get_feature_hash_to_flat_object_attribute_map()
        id_and_object_hash_to_answers_map = self.get_id_and_object_hash_to_answers_map(object_actions)

        classifications = self.get_flat_static_classifications(
            object_hash, feature_hash, object_answers, feature_hash_to_attribute_map
        )
        dynamic_classifications = self.get_flat_dynamic_classifications(
            object_hash,
            feature_hash,
            image_id,
            id_and_object_hash_to_answers_map,
        )
        classifications.update(dynamic_classifications)

        return classifications

    def get_feature_hash_to_flat_object_attribute_map(self) -> Dict[str, Attribute]:
        if self._feature_hash_to_attribute_map is not None:
            return self._feature_hash_to_attribute_map

        ret: Dict[str, Attribute] = {}

        for object_ in self._ontology.objects:
            for attribute in object_.attributes:
                ret[attribute.feature_node_hash] = attribute

        self._feature_hash_to_attribute_map = ret

        return ret

    def get_flat_static_classifications(
        self,
        object_hash: str,
        object_feature_hash: str,
        object_answers: Dict[str, Any],
        feature_hash_to_attribute_map: Dict[str, Attribute],
    ) -> Dict[str, Any]:
        ret = {}
        classifications = object_answers[object_hash]["classifications"]
        for classification in classifications:
            feature_hash = classification["featureHash"]
            if feature_hash not in feature_hash_to_attribute_map:
                # This will be a deeply nested attribute
                continue

            attribute = feature_hash_to_attribute_map[feature_hash]
            answers = classification["answers"]

            if attribute.get_property_type() == PropertyType.TEXT:
                ret.update(self.get_text_answer(attribute, answers))
            elif attribute.get_property_type() == PropertyType.RADIO:
                ret.update(self.get_radio_answer(attribute, answers))
            elif attribute.get_property_type() == PropertyType.CHECKLIST:
                ret.update(self.get_checklist_answer(attribute, answers))

        self.add_unselected_attributes(object_feature_hash, ret, match_dynamic_attributes=False)

        return ret

    def get_id_and_object_hash_to_answers_map(
        self,
        object_actions: Dict[str, Any],
    ) -> Dict[Tuple[int, str], Dict]:
        if self._id_and_object_hash_to_answers_map is not None:
            return self._id_and_object_hash_to_answers_map

        ret: Dict[Tuple[int, str], Dict[str, Any]] = defaultdict(dict)
        feature_hash_to_attribute_map = self.get_feature_hash_to_flat_object_attribute_map()
        for object_hash, payload in object_actions.items():
            for action in payload["actions"]:
                feature_hash = action["featureHash"]
                if feature_hash not in feature_hash_to_attribute_map:
                    # This will be a deeply nested attribute
                    continue

                attribute = feature_hash_to_attribute_map[feature_hash]
                answers = action["answers"]
                answers_dict: Dict[str, Any] = {}

                if attribute.get_property_type() == PropertyType.TEXT:
                    answers_dict.update(self.get_text_answer(attribute, answers))
                elif attribute.get_property_type() == PropertyType.RADIO:
                    answers_dict.update(self.get_radio_answer(attribute, answers))
                elif attribute.get_property_type() == PropertyType.CHECKLIST:
                    answers_dict.update(self.get_checklist_answer(attribute, answers))

                for sub_range in action["range"]:
                    for i in range(sub_range[0], sub_range[1] + 1):
                        ret[(i, object_hash)].update(answers_dict)

        self._id_and_object_hash_to_answers_map = ret

        return ret

    def get_flat_dynamic_classifications(
        self,
        object_hash: str,
        feature_hash: str,
        image_id: int,
        id_and_object_hash_to_answers_map: Dict[Tuple[int, str], Dict[str, Any]],
    ) -> Dict[str, Any]:
        ret = {}
        id_and_object_hash = (image_id, object_hash)

        if id_and_object_hash in id_and_object_hash_to_answers_map:
            ret = id_and_object_hash_to_answers_map[(image_id, object_hash)]

        self.add_unselected_attributes(feature_hash, ret, match_dynamic_attributes=True)

        return ret

    def add_unselected_attributes(
        self, feature_hash: str, attributes_dict: Dict[str, Optional[bool]], match_dynamic_attributes: bool
    ) -> None:
        """Attributes which have never been selected will not show up in the actions map. They will need to be
        added separately. NOTE: this assumes uniqueness of features. Quite an edge case but if it ever comes
        up it needs to be solved somewhere here.
        """
        # TODO: This could be improved
        all_attributes = self.get_attributes_for_feature_hash(feature_hash)
        for attribute in all_attributes:
            is_matching_attribute = attribute.dynamic == match_dynamic_attributes
            if is_matching_attribute:
                if attribute.get_property_type() == PropertyType.CHECKLIST:
                    for option in attribute.options:  # type: ignore[union-attr]
                        if option.label not in attributes_dict:
                            # We need to add the default of False.
                            attributes_dict[option.label] = False
                else:
                    if attribute.name not in attributes_dict:
                        attributes_dict[attribute.name] = None

    def get_attributes_for_feature_hash(self, feature_hash: str) -> List[Attribute]:
        ret = []

        for object_ in self._ontology.objects:
            if object_.feature_node_hash == feature_hash:
                for attribute in object_.attributes:
                    ret.append(attribute)
                break

        return ret

    def get_radio_answer(self, attribute: Attribute, answers: List[Dict[str, str]]) -> Dict[str, str]:
        answer = answers[0]  # radios only have one answer by definition
        return {attribute.name: answer["name"]}

    def get_checklist_answer(self, attribute: Attribute, answers: List[Dict[str, Any]]) -> Dict[str, bool]:
        ret: Dict[str, bool] = {}
        found_checklist_answers: Set[str] = set()

        for answer in answers:
            found_checklist_answers.add(answer["name"])

        for option in attribute.options:  # type: ignore[union-attr]
            label = option.label
            ret[label] = label in found_checklist_answers

        return ret

    def get_text_answer(self, attribute: Attribute, answers: str) -> Dict[str, Any]:
        return {attribute.name: answers}

    def get_category_id(self, object_: Dict[str, Any]) -> int:
        feature_hash = object_["featureHash"]
        try:
            return self._feature_hash_to_coco_category_id_map[feature_hash]
        except KeyError:
            raise EncordException(
                f"The feature_hash `{feature_hash}` was not found in the provided ontology. Please "
                f"ensure that the ontology matches the labels provided."
            ) from None

    def get_coco_annotation_default_fields(
        self, object_: Dict[str, Any]
    ) -> Tuple[
        int,
        int,
        Optional[int],
        Optional[str],
        Optional[bool],
    ]:
        id_ = self.next_annotation_id()
        is_crowd = 0

        track_id = self.get_and_set_track_id(object_hash=object_["objectHash"])
        encord_track_uuid = object_["objectHash"]
        manual_annotation = object_["manualAnnotation"]

        return id_, is_crowd, track_id, encord_track_uuid, manual_annotation

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

    def get_image_id(self, data_hash: str, frame_num: int = 0) -> int:
        return self._data_hash_to_image_id_map[(data_hash, frame_num)]
