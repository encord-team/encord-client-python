import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.common import Shape
from encord.objects.coordinates import BoundingBoxCoordinates, PointCoordinate, PolygonCoordinates
from encord.objects.ontology_object import Object
from encord.utilities.coco.datastructure import (
    CategoryID,
    FrameIndex,
    ImageID,
)
from encord.utilities.coco.parsers import (
    parse_annotations,
)
from encord.utilities.coco.utils import crop_box_to_image_size

if TYPE_CHECKING:
    from encord import Project

logger = logging.getLogger()


class CocoImporter:
    def __init__(
        self,
        project: "Project",
        annotation_dict: Dict[str, Any],
        category_id_to_feature_hash: Dict[CategoryID, str],
        image_id_to_frame_index: Dict[ImageID, FrameIndex],
    ) -> None:
        self._project = project
        self._annotation_dict = annotation_dict
        self._category_id_to_feature_hash = category_id_to_feature_hash
        self._image_id_to_frame_index = image_id_to_frame_index

        self.populate_maps()

        self._annotations = parse_annotations(annotation_dict.get("annotations", []))

    def populate_maps(self) -> None:
        map_category_to_encord_object: Dict[CategoryID, Object] = {}
        for id, feature_hash in self._category_id_to_feature_hash.items():
            object: Object = self._project.ontology_structure.get_child_by_hash(feature_node_hash=feature_hash)
            map_category_to_encord_object[id] = object
        self.category_to_encord = map_category_to_encord_object

        data_hashes = list({frame_index.data_hash for frame_index in self._image_id_to_frame_index.values()})
        label_rows = self._project.list_label_rows_v2(data_hashes=data_hashes)
        with self._project.create_bundle() as bundle:
            for row in label_rows:
                row.initialise_labels(bundle=bundle)
        self._label_rows = label_rows

    def encode(self) -> None:
        for image_id, annotations in self._annotations.items():
            frame_index = self._image_id_to_frame_index[image_id]
            rows = [row for row in self._label_rows if row.data_hash == frame_index.data_hash]
            if not len(rows) == 1:
                raise ValueError(f"Data hash {frame_index.data_hash} not found in project")
            label_row = rows[0]
            frame_view = label_row.get_frame_view(self._image_id_to_frame_index[image_id].frame)
            img_h, img_w = frame_view.height, frame_view.width
            for annotation in annotations:
                encord_object = self.category_to_encord[annotation.category_id]
                if annotation.segmentation is not None and encord_object.shape in [Shape.POLYGON, Shape.BITMASK]:
                    if encord_object.shape == Shape.POLYGON:
                        polygon = annotation.segmentation
                        points = [
                            PointCoordinate(x=polygon[i] / img_w, y=polygon[i + 1] / img_h)
                            for i in range(0, len(polygon), 2)
                        ]
                        coordinates = PolygonCoordinates(values=points)
                    elif encord_object.shape == Shape.BITMASK:
                        mask = annotation.segmentation
                        coordinates = BitmaskCoordinates(mask.astype(bool))
                    object_instance = encord_object.create_instance()
                    object_instance.set_for_frames(coordinates, frames=frame_index.frame)
                    label_row.add_object_instance(object_instance)
                elif encord_object.shape == Shape.BOUNDING_BOX:
                    try:
                        x, y, w, h = crop_box_to_image_size(*annotation.bbox, img_w=img_w, img_h=img_h)
                    except ValueError as e:
                        logger.warning(f"<magenta>Skipping annotation with id {annotation.id_}</magenta> {str(e)}")
                        continue
                    bounding_box = BoundingBoxCoordinates(
                        height=h / img_h, width=w / img_w, top_left_x=x / img_w, top_left_y=y / img_h
                    )
                    object_instance = encord_object.create_instance()
                    object_instance.set_for_frames(bounding_box, frames=frame_index.frame)
                    label_row.add_object_instance(object_instance)
            label_row.save()
