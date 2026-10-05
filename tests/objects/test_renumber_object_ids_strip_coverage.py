"""`renumber_object_ids=True` scrubs `objectId` from the whole exported dict via a single recursive
strip (`_strip_object_ids`) applied once the dict is fully built.
"""

from unittest.mock import Mock

import pytest

from encord.objects import LabelRowV2, Object
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.frames import Range
from encord.objects.html_node import HtmlNode, HtmlRange
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_html import (
    DATA_GROUP_METADATA as HTML_METADATA,
)
from tests.objects.data.data_group.two_html import (
    DATA_GROUP_TWO_HTML_NO_LABELS,
)
from tests.objects.data.data_group.two_images import (
    DATA_GROUP_METADATA as IMAGE_METADATA,
)
from tests.objects.data.data_group.two_images import (
    DATA_GROUP_TWO_IMAGES_NO_LABELS,
)
from tests.objects.data.data_group.two_text import (
    DATA_GROUP_METADATA as TEXT_METADATA,
)
from tests.objects.data.data_group.two_text import (
    DATA_GROUP_TWO_TEXT_NO_LABELS,
)
from tests.objects.data.data_group.two_videos import (
    DATA_GROUP_TWO_VIDEOS_NO_LABELS,
    DATA_GROUP_WITH_TWO_VIDEOS_METADATA,
)
from tests.objects.spaces.test_mcap_point_cloud_spaces import KEY_3, SEG_FEATURE, _scene_row, mcap_labels

box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
text_obj_ontology_item = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)

EXPLICIT_OBJECT_ID = 42


def _find_object_id_paths(node, path="$"):
    """Recursively collect every path to a dict key case-insensitively equal to `objectid`."""
    hits = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and key.lower() == "objectid":
                hits.append(child_path)
            hits.extend(_find_object_id_paths(value, child_path))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            hits.extend(_find_object_id_paths(item, f"{path}[{index}]"))
    return hits


def _build_image_space_row(ontology):
    label_row = LabelRowV2(IMAGE_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_IMAGES_NO_LABELS)
    image_space = label_row.get_space(id="image-1-uuid", type_="image")
    instance = box_ontology_item.create_instance(object_id=EXPLICIT_OBJECT_ID)
    image_space.put_object_instance(
        object_instance=instance,
        coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0),
    )
    return label_row


def _build_video_space_row(ontology):
    label_row = LabelRowV2(DATA_GROUP_WITH_TWO_VIDEOS_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_VIDEOS_NO_LABELS)
    video_space = label_row.get_space(id="video-1-uuid", type_="video")
    instance = box_ontology_item.create_instance(object_id=EXPLICIT_OBJECT_ID)
    video_space.put_object_instance(
        object_instance=instance,
        frames=[1],
        coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0),
    )
    return label_row


def _build_html_space_row(ontology):
    label_row = LabelRowV2(HTML_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space = label_row.get_space(id="html-1-uuid", type_="html")
    instance = text_obj_ontology_item.create_instance(object_id=EXPLICIT_OBJECT_ID)
    html_range = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    html_space.put_object_instance(object_instance=instance, ranges=html_range)
    return label_row


def _build_text_space_row(ontology):
    label_row = LabelRowV2(TEXT_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_TEXT_NO_LABELS)
    text_space = label_row.get_space(id="text-1-uuid", type_="text")
    instance = text_obj_ontology_item.create_instance(object_id=EXPLICIT_OBJECT_ID)
    text_space.put_object_instance(object_instance=instance, ranges=Range(start=0, end=100))
    return label_row


def _build_point_cloud_space_row(all_types_ontology):
    label_row = _scene_row(all_types_ontology, mcap_labels())
    point_cloud_space = label_row.get_space(id=KEY_3, type_="point_cloud")
    segmentation_ontology_item = all_types_structure.get_child_by_hash(SEG_FEATURE, type_=Object)
    instance = segmentation_ontology_item.create_instance(object_id=EXPLICIT_OBJECT_ID)
    point_cloud_space.put_object_instance(instance, ranges=[Range(20, 25)])
    return label_row


@pytest.mark.parametrize("space_kind", ["image", "video", "html", "text", "point_cloud"])
def test_renumber_object_ids_true_scrubs_object_id_everywhere_in_export(space_kind, ontology, all_types_ontology):
    builders = {
        "image": lambda: _build_image_space_row(ontology),
        "video": lambda: _build_video_space_row(ontology),
        "html": lambda: _build_html_space_row(ontology),
        "text": lambda: _build_text_space_row(ontology),
        "point_cloud": lambda: _build_point_cloud_space_row(all_types_ontology),
    }
    label_row = builders[space_kind]()

    exported = label_row.to_encord_dict(renumber_object_ids=True)

    assert _find_object_id_paths(exported) == []
