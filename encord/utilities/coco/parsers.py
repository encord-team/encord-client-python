from typing import Dict, List

from encord.utilities.coco.datastructure import CocoAnnotation, ImageID
from encord.utilities.coco.utils import annToMask, mask_to_polygon


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
            mask = annToMask(annotation, h=h, w=w)
            poly, inferred_bbox = mask_to_polygon(mask)
            if poly is None or inferred_bbox != annotation["bbox"]:
                print(f"Annotation '{annotation['id']}', contains an invalid polygon. Skipping ...")
                continue
            segmentations = [poly]

        img_id = annotation["image_id"]
        annot_dict.setdefault(img_id, [])

        if segmentations:
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
        else:
            annot_dict[img_id].append(
                CocoAnnotation(
                    area=annotation["area"],
                    bbox=annotation["bbox"],
                    category_id=annotation["category_id"],
                    id_=annotation["id"],
                    image_id=annotation["image_id"],
                    iscrowd=annotation["iscrowd"],
                    segmentation=[],
                    rotation=annotation.get("attributes", {}).get("rotation"),
                )
            )

    return annot_dict
