import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    ValuesView,
)

from encord.objects.common import Shape
from encord.objects.ontology_labels_impl import LabelRowV2
from encord.objects.ontology_object import Object
from encord.project import Project
from encord.utilities.coco.datastructure import (
    CategoryID,
    CocoPolygon,
    CocoRLE,
    CocoRootModel,
    FrameIndex,
    ImageID,
)

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
    project: Project, image_id_to_frame_index: Dict[ImageID, FrameIndex]
) -> Dict[str, LabelRowV2]:
    data_hashes = list({frame_index.data_hash for frame_index in image_id_to_frame_index.values()})
    label_rows = project.list_label_rows_v2(data_hashes=data_hashes)
    with project.create_bundle() as bundle:
        for lr in label_rows:
            lr.initialise_labels(bundle=bundle)
    return {lr.data_hash: lr for lr in label_rows}


def import_coco_labels(
    project: Project,
    coco: CocoRootModel,
    category_id_to_feature_hash: Dict[CategoryID, str],
    image_id_to_frame_index: Dict[ImageID, FrameIndex],
) -> None:
    label_rows = initialise_label_rows(project, image_id_to_frame_index)
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

        segmentation = annotation.segmentation
        width, height = coco_image.width, coco_image.height
        ins = ont_obj.create_instance()
        if ont_obj.shape == Shape.BOUNDING_BOX:
            ins.set_for_frames(
                coordinates=annotation.bbox.to_encord(img_w=width, img_h=height),
                frames=frame_idx.frame,
            )
            label_row.add_object_instance(ins)
        elif ont_obj.shape == Shape.BITMASK:
            if not isinstance(segmentation, CocoRLE):
                raise ValueError(
                    f"A mismatch between the format in the `labels_dict` and the expected shape in the ontology object with feature node hash {ont_obj.feature_node_hash} was detected for annotation id {annotation.id}. Expected format was an RLE."
                )
            ins.set_for_frames(coordinates=segmentation.to_encord(), frames=frame_idx.frame)
            label_row.add_object_instance(ins)
        elif ont_obj.shape == Shape.POLYGON:
            if not isinstance(segmentation, CocoPolygon) or (
                isinstance(segmentation, list) and isinstance(segmentation[0], CocoPolygon)
            ):
                raise ValueError(
                    f"A mismatch between the format in the `labels_dict` and the expected shape in the ontology object with feature node hash {ont_obj.feature_node_hash} was detected for annotation id {annotation.id}. Expected format was a polygon or a list of polygons. {segmentation}"
                )
            if isinstance(segmentation, CocoPolygon):
                segmentation = [segmentation]

            for poly in segmentation:
                ins.set_for_frames(
                    coordinates=poly.to_encord(img_w=width, img_h=height),
                    frames=frame_idx.frame,
                )
                label_row.add_object_instance(ins)
                ins = ont_obj.create_instance()
        else:
            raise ValueError(f"Ontology objects of shape {ont_obj.shape} are not supported for coco import")

    with project.create_bundle() as bundle:
        for label_row in label_rows.values():
            label_row.save(bundle=bundle)
