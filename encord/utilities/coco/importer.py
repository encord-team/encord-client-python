import logging
from typing import (
    Dict,
    Optional,
    Union,
)

from encord.objects.bitmask import BitmaskCoordinates
from encord.objects.common import Shape
from encord.objects.coordinates import BoundingBoxCoordinates, PolygonCoordinates
from encord.objects.ontology_labels_impl import LabelRowV2
from encord.objects.ontology_object import Object
from encord.project import Project
from encord.utilities.coco.datastructure import (
    CategoryID,
    CocoAnnotationModel,
    CocoPolygon,
    CocoRLE,
    CocoRootModel,
    FrameIndex,
    ImageID,
)
from encord.utilities.coco.polygon_utils import rle_to_polygons_coordinates

logger = logging.getLogger()


def build_category_id_to_encord_ontology_object_map(
    project: Project,
    category_id_to_feature_hash: Dict[CategoryID, str],
) -> Dict[CategoryID, Object]:
    map_category_to_encord_object: Dict[CategoryID, Object] = {}
    for id, feature_hash in category_id_to_feature_hash.items():
        object_ = project.ontology_structure.get_child_by_hash(feature_node_hash=feature_hash, type_=Object)
        map_category_to_encord_object[id] = object_

    return map_category_to_encord_object


def initialise_label_rows(
    project: Project,
    image_id_to_frame_index: Dict[ImageID, FrameIndex],
    branch_name: Optional[str] = None,
) -> Dict[str, LabelRowV2]:
    data_hashes = list({frame_index.data_hash for frame_index in image_id_to_frame_index.values()})
    label_rows = project.list_label_rows_v2(data_hashes=data_hashes, branch_name=branch_name)
    with project.create_bundle() as bundle:
        for lr in label_rows:
            lr.initialise_labels(bundle=bundle)
    return {lr.data_hash: lr for lr in label_rows}


def import_coco_labels(
    project: Project,
    coco: CocoRootModel,
    category_id_to_feature_hash: Dict[CategoryID, str],
    image_id_to_frame_index: Dict[ImageID, FrameIndex],
    branch_name: Optional[str] = None,
    confidence_field_name: Optional[str] = None,
) -> None:
    label_rows = initialise_label_rows(project, image_id_to_frame_index, branch_name=branch_name)
    category_id_to_objects = build_category_id_to_encord_ontology_object_map(project, category_id_to_feature_hash)
    coco_image_lookup = {i.id: i for i in coco.images}

    for i, annotation in enumerate(coco.annotations):
        frame_idx = image_id_to_frame_index.get(annotation.image_id)
        if frame_idx is None:
            # TODO not clear how to propagate errors
            logger.warning(
                f'Image id `{annotation.image_id}` from `labels_dict["annotations"][{i}]` could not be matched with the provided `image_id_to_frame_index`. Skipping this annotation.'
            )
            continue

        label_row = label_rows.get(frame_idx.data_hash)
        if label_row is None:
            logger.warning(
                f"Data hash `{frame_idx.data_hash}` from `image_id_to_frame_index` could not be matched with a data hash in the provided `project`. Skipping annotation ad index {i}."
            )
            # TODO not clear how to propagate errors
            continue

        ont_obj = category_id_to_objects.get(annotation.category_id)
        if ont_obj is None:
            logger.warning(
                f'Category ID {annotation.category_id} from `labels_dict["annotations"][{i}]` could not be matched with the provided `category_id_to_feature_hash`. Skipping this annotation.'
            )
            # TODO not clear how to propagate errors
            continue

        coco_image = coco_image_lookup.get(annotation.image_id)
        if coco_image is None:
            raise ValueError(
                f"The provided coco annotation dictionary have annotations with `image_id`s that do not match any image ids in the provided `images` list. Couldn't find image id {annotation.image_id}."
            )

        confidence = annotation.get_extra(confidence_field_name) if confidence_field_name is not None else None
        coordinates = coco_annotation_to_encord_coordinates(
            coco_annotation=annotation,
            shape=ont_obj.shape,
            width=coco_image.width,
            height=coco_image.height,
        )
        obj_instance = ont_obj.create_instance()
        obj_instance.set_for_frames(coordinates=coordinates, frames=frame_idx.frame, confidence=confidence)
        label_row.add_object_instance(obj_instance)

    with project.create_bundle() as bundle:
        for label_row in label_rows.values():
            label_row.save(bundle=bundle)


def coco_annotation_to_encord_coordinates(
    coco_annotation: CocoAnnotationModel,
    shape: Shape,
    width: int,
    height: int,
) -> Union[PolygonCoordinates, BoundingBoxCoordinates, BitmaskCoordinates]:
    if shape == Shape.BOUNDING_BOX:
        return coco_annotation.bbox.to_encord(img_w=width, img_h=height)
    elif shape == Shape.BITMASK:
        if not isinstance(coco_annotation.segmentation, CocoRLE):
            raise ValueError(
                f"Mismatch in `labels_dict` for annotation id {coco_annotation.id}. Expected format was an RLE."
            )
        return coco_annotation.segmentation.to_bitmask()
    elif shape == Shape.POLYGON:
        if isinstance(coco_annotation.segmentation, CocoPolygon):
            return coco_annotation.segmentation.to_encord(img_w=width, img_h=height)
        elif isinstance(coco_annotation.segmentation, CocoRLE):
            return rle_to_polygons_coordinates(
                counts=coco_annotation.segmentation.counts,
                height=coco_annotation.segmentation.size.height,
                width=coco_annotation.segmentation.size.width,
            )
        else:
            raise ValueError(
                f"Mismatch in `labels_dict` for annotation id {coco_annotation.id}. Expected format was a list of polygons or RLE string."
            )
    else:
        raise ValueError(f"Ontology objects of shape {shape} are not supported for coco import")
