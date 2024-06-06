from typing import Dict, List

from encord.utilities.coco.datastructure import CocoAnnotation, ImageID
from encord.utilities.coco.utils import annToMask, mask_to_polygon, parse_annotation


def parse_annotations(annotations: List[Dict]) -> Dict[ImageID, List[CocoAnnotation]]:
    annot_dict: Dict[int, List[CocoAnnotation]] = {}
    for annotation in annotations:
        if annotation["iscrowd"] == 1:
            continue

        segmentations = annotation.get("segmentation", [])

        if not segmentations:
            segmentations = [[]]
        elif isinstance(segmentations, list) and not isinstance(segmentations[0], list):
            segmentations = [segmentations]
        elif isinstance(segmentations, dict):
            h, w = segmentations["size"]
            segment = parse_annotation(annotation, h,w)
            segmentations = [segment]

        img_id = annotation["image_id"]
        annot_dict.setdefault(img_id, [])

        for segment in segmentations:
            annot_dict[img_id].append(
                CocoAnnotation(
                    area=annotation["area"],
                    bbox=annotation["bbox"],
                    category_id=annotation["category_id"],
                    id_=annotation["id"],
                    image_id=annotation["image_id"],
                    iscrowd=annotation["iscrowd"],
                    segmentation=segment,
                    rotation=annotation.get("attributes", {}).get("rotation"),
                )
            )

    return annot_dict
