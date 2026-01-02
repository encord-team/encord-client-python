from datetime import datetime
from unittest.mock import Mock

import pytest
from deepdiff import DeepDiff

from encord.common.time_parser import format_datetime_to_long_string
from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import HtmlCoordinates
from encord.objects.html_node import HtmlNode, HtmlRange
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.two_html import (
    DATA_GROUP_METADATA,
    DATA_GROUP_TWO_HTML_NO_LABELS,
)

html_text_obj_ontology_item = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)
html_text_obj_definition_attribute_ontology_item = html_text_obj_ontology_item.get_child_by_hash(
    "definitionFeatureHash", type_=Attribute
)


def test_put_object_on_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")

    # Act
    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    new_object_instance = html_text_obj_ontology_item.create_instance()
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=range_1,
    )

    # Assert
    object_instances = label_row._get_object_instances(include_spaces=True)
    assert len(object_instances) == 1

    objects_on_space = html_space_1.get_object_instances()
    object_on_space = objects_on_space[0]
    assert len(objects_on_space) == 1
    assert object_on_space._spaces == {html_space_1.space_id: html_space_1}

    annotations = list(html_space_1.get_object_instance_annotations())
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.frame == 0  # Frame is here for backwards compatibility
    assert first_annotation.coordinates == HtmlCoordinates(
        range=[range_1]
    )  # Coordinates are here for backwards compatibility
    assert first_annotation.object_hash == new_object_instance.object_hash


def test_put_object_with_multiple_ranges(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")

    # Act
    new_object_instance = html_text_obj_ontology_item.create_instance()
    html_ranges = [
        HtmlRange(
            start=HtmlNode(xpath="/html/body/p[1]", offset=0),
            end=HtmlNode(xpath="/html/body/p[1]", offset=10),
        ),
        HtmlRange(
            start=HtmlNode(xpath="/html/body/p[2]", offset=5),
            end=HtmlNode(xpath="/html/body/p[2]", offset=20),
        ),
    ]
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=html_ranges,
    )

    # Assert
    annotations = list(html_space_1.get_object_instance_annotations())
    first_annotation = annotations[0]
    assert len(annotations) == 1
    assert first_annotation.coordinates == HtmlCoordinates(range=html_ranges)
    assert first_annotation.ranges == html_ranges


def test_put_objects_with_error_overlapping_strategy(ontology):
    # Arrange
    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    new_object_instance = html_text_obj_ontology_item.create_instance()
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=range_1,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        html_space_1.put_object_instance(
            object_instance=new_object_instance,
            ranges=range_2,
        )

    assert e.value.message == (
        f"Annotation for object instance {new_object_instance.object_hash} already exists. Set 'on_overlap' to 'replace' to overwrite existing annotations."
    )


def test_put_objects_with_replace_overlapping_strategy(ontology):
    # Arrange
    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    new_object_instance = html_text_obj_ontology_item.create_instance()
    html_space_1.put_object_instance(object_instance=new_object_instance, ranges=range_1)

    # Act
    html_space_1.put_object_instance(object_instance=new_object_instance, ranges=range_2, on_overlap="replace")

    # Assert
    object_annotations = list(html_space_1.get_object_instance_annotations())
    assert len(object_annotations) == 1
    assert object_annotations[0].coordinates == HtmlCoordinates(range=[range_2])
    assert object_annotations[0].ranges == [range_2]


def test_remove_object_from_html_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    new_object_instance = html_text_obj_ontology_item.create_instance()

    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    html_space_1.put_object_instance(object_instance=new_object_instance, ranges=range_1)

    # Act
    html_space_1.remove_object_instance(
        object_hash=new_object_instance.object_hash,
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 0

    objects_on_space = html_space_1.get_object_instances()
    assert len(objects_on_space) == 0

    annotations_on_space = list(html_space_1.get_object_instance_annotations())
    assert len(annotations_on_space) == 0

    annotations_on_object = list(new_object_instance.get_annotations())
    assert len(annotations_on_object) == 0


def test_add_object_to_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    html_space_2 = label_row._get_space(id="html-2-uuid", type_="html")

    new_object_instance = html_text_obj_ontology_item.create_instance()
    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    # Act
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=range_1,
    )
    html_space_2.put_object_instance(
        object_instance=new_object_instance,
        ranges=range_2,
    )

    # Assert
    objects = html_space_1.get_object_instances()
    assert len(objects) == 1

    annotations_on_html_space_1 = list(html_space_1.get_object_instance_annotations())
    assert len(annotations_on_html_space_1) == 1

    first_annotation_on_html_space_1 = annotations_on_html_space_1[0]
    assert first_annotation_on_html_space_1.coordinates == HtmlCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_on_html_space_1.ranges == [range_1]

    annotations_on_html_space_2 = list(html_space_2.get_object_instance_annotations())
    first_annotation_on_html_space_2 = annotations_on_html_space_2[0]
    assert len(annotations_on_html_space_2) == 1
    assert first_annotation_on_html_space_2.coordinates == HtmlCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_on_html_space_2.ranges == [range_2]


def test_update_attribute_for_object_which_exist_on_two_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    html_space_2 = label_row._get_space(id="html-2-uuid", type_="html")

    new_object_instance = html_text_obj_ontology_item.create_instance()
    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    html_space_1.put_object_instance(object_instance=new_object_instance, ranges=range_1)
    html_space_2.put_object_instance(object_instance=new_object_instance, ranges=range_2)

    object_answer = new_object_instance.get_answer(attribute=html_text_obj_definition_attribute_ontology_item)
    assert object_answer is None

    # Act
    new_answer = "Hello!"
    new_object_instance.set_answer(attribute=html_text_obj_definition_attribute_ontology_item, answer=new_answer)

    # Assert
    object_answer = new_object_instance.get_answer(attribute=html_text_obj_definition_attribute_ontology_item)
    assert object_answer == new_answer

    object_on_html_space_1 = html_space_1.get_object_instances()[0]
    assert object_on_html_space_1.get_answer(html_text_obj_definition_attribute_ontology_item) == new_answer

    object_on_html_space_2 = html_space_2.get_object_instances()[0]
    assert object_on_html_space_2.get_answer(html_text_obj_definition_attribute_ontology_item) == new_answer

    object_answer_dict = label_row.to_encord_dict()["object_answers"]

    EXPECTED_DICT = {
        new_object_instance.object_hash: {
            "classifications": [
                {
                    "name": "Definition",
                    "value": "definition",
                    "answers": "Hello!",
                    "featureHash": "definitionFeatureHash",
                    "manualAnnotation": True,
                }
            ],
            "featureHash": "textFeatureNodeHash",
            "objectHash": new_object_instance.object_hash,
            "createdBy": None,
            "lastEditedBy": None,
            "manualAnnotation": True,
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "shape": "text",
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "start", "offset": 0}, {"xpath": "end", "offset": 1}]],
                    "type": "html",
                },
                "html-2-uuid": {
                    "range": [[{"xpath": "new_start", "offset": 6}, {"xpath": "new_end", "offset": 7}]],
                    "type": "html",
                },
            },
            "range": [],
        }
    }

    assert not DeepDiff(
        object_answer_dict, EXPECTED_DICT, exclude_regex_paths=[r".*\['lastEditedAt'\]", r".*\['createdAt'\]"]
    )


def test_get_object_annotations(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    object_instance_1 = html_text_obj_ontology_item.create_instance()
    object_instance_2 = html_text_obj_ontology_item.create_instance()

    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    html_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    html_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations = list(html_space_1.get_object_instance_annotations())
    first_annotation = object_annotations[0]
    second_annotation = object_annotations[1]

    # Assert
    assert len(object_annotations) == 2

    assert first_annotation.space.space_id == "html-1-uuid"
    assert first_annotation.frame == 0  # Frame here for backwards compatibility
    assert first_annotation.object_hash == object_instance_1.object_hash
    assert first_annotation.coordinates == HtmlCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation.last_edited_by == name_1
    assert first_annotation.last_edited_at == date1

    assert second_annotation.space.space_id == "html-1-uuid"
    assert second_annotation.frame == 0  # Frame here for backwards compatibility
    assert second_annotation.object_hash == object_instance_2.object_hash
    assert second_annotation.coordinates == HtmlCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert second_annotation.last_edited_by == name_2
    assert second_annotation.last_edited_at == date2


def test_get_object_annotations_with_filter_objects(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    object_instance_1 = html_text_obj_ontology_item.create_instance()
    object_instance_2 = html_text_obj_ontology_item.create_instance()

    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    html_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    html_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations_for_object_1 = list(
        html_space_1.get_object_instance_annotations(filter_object_instances=[object_instance_1.object_hash])
    )
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = list(
        html_space_1.get_object_instance_annotations(filter_object_instances=[object_instance_2.object_hash])
    )
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "html-1-uuid"
    assert first_annotation_for_object_1.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.ranges == [range_1]
    assert first_annotation_for_object_1.coordinates == HtmlCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "html-1-uuid"
    assert first_annotation_for_object_2.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.ranges == [range_2]
    assert first_annotation_for_object_2.coordinates == HtmlCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_get_object_annotations_from_object_instance(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    object_instance_1 = html_text_obj_ontology_item.create_instance()
    object_instance_2 = html_text_obj_ontology_item.create_instance()

    range_1 = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    range_2 = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    name_1 = "james"
    name_2 = "timmy"

    date1 = datetime(2020, 1, 1)
    date2 = datetime(2020, 5, 5)

    html_space_1.put_object_instance(
        object_instance=object_instance_1,
        ranges=range_1,
        last_edited_by=name_1,
        last_edited_at=date1,
    )

    html_space_1.put_object_instance(
        object_instance=object_instance_2,
        ranges=range_2,
        last_edited_by=name_2,
        last_edited_at=date2,
    )

    # Act
    object_annotations_for_object_1 = object_instance_1.get_annotations()
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = object_instance_2.get_annotations()
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "html-1-uuid"
    assert first_annotation_for_object_1.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.ranges == [range_1]
    assert first_annotation_for_object_1.coordinates == HtmlCoordinates(
        range=[range_1]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "html-1-uuid"
    assert first_annotation_for_object_2.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.ranges == [range_2]
    assert first_annotation_for_object_2.coordinates == HtmlCoordinates(
        range=[range_2]
    )  # Coordinates here for backwards compatibility
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_update_annotation_from_object_annotation_using_coordinates(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    object_instance = html_text_obj_ontology_item.create_instance()

    current_range = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    new_range = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    html_space_1.put_object_instance(
        object_instance=object_instance,
        ranges=current_range,
        last_edited_by=name,
        last_edited_at=date,
        created_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_object_answers_dict = current_label_row_dict["object_answers"]

    EXPECTED_CURRENT_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "createdBy": None,
            "createdAt": format_datetime_to_long_string(date),
            "lastEditedAt": format_datetime_to_long_string(date),
            "lastEditedBy": name,
            "manualAnnotation": True,
            "shape": "text",
            "classifications": [],
            "range": [],
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "start", "offset": 0}, {"xpath": "end", "offset": 1}]],
                    "type": "html",
                }
            },
        },
    }

    assert not DeepDiff(current_object_answers_dict, EXPECTED_CURRENT_OBJECT_ANSWERS_DICT)

    # Act
    object_annotations = list(html_space_1.get_object_instance_annotations())
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.coordinates = HtmlCoordinates(
        range=[new_range]
    )  # This is a backwards compatible flow. Should change it via object_annotation.ranges

    # Assert
    updated_annotations = list(html_space_1.get_object_instance_annotations())
    assert len(updated_annotations) == 1
    assert updated_annotations[0].coordinates == HtmlCoordinates(range=[new_range])
    assert updated_annotations[0].created_by == new_name
    assert updated_annotations[0].last_edited_by == new_name

    new_label_row_dict = label_row.to_encord_dict()
    new_object_answers_dict = new_label_row_dict["object_answers"]

    EXPECTED_NEW_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "createdBy": new_name,
            "createdAt": format_datetime_to_long_string(new_date),
            "lastEditedAt": format_datetime_to_long_string(new_date),
            "lastEditedBy": new_name,
            "manualAnnotation": True,
            "shape": "text",
            "classifications": [],
            "range": [],
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "new_start", "offset": 6}, {"xpath": "new_end", "offset": 7}]],
                    "type": "html",
                }
            },
        },
    }
    assert not DeepDiff(new_object_answers_dict, EXPECTED_NEW_OBJECT_ANSWERS_DICT)


def test_update_annotation_from_object_annotation(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    object_instance = html_text_obj_ontology_item.create_instance()

    current_range = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    new_range = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    html_space_1.put_object_instance(
        object_instance=object_instance,
        ranges=current_range,
        last_edited_by=name,
        last_edited_at=date,
        created_at=date,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_object_answers_dict = current_label_row_dict["object_answers"]

    EXPECTED_CURRENT_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "createdBy": None,
            "createdAt": format_datetime_to_long_string(date),
            "lastEditedAt": format_datetime_to_long_string(date),
            "lastEditedBy": name,
            "manualAnnotation": True,
            "shape": "text",
            "classifications": [],
            "range": [],
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "start", "offset": 0}, {"xpath": "end", "offset": 1}]],
                    "type": "html",
                }
            },
        },
    }

    assert not DeepDiff(current_object_answers_dict, EXPECTED_CURRENT_OBJECT_ANSWERS_DICT)

    # Act
    object_annotations = list(html_space_1.get_object_instance_annotations())
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.ranges = new_range

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_object_answers_dict = new_label_row_dict["object_answers"]

    EXPECTED_NEW_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "createdBy": new_name,
            "createdAt": format_datetime_to_long_string(new_date),
            "lastEditedAt": format_datetime_to_long_string(new_date),
            "lastEditedBy": new_name,
            "manualAnnotation": True,
            "shape": "text",
            "classifications": [],
            "range": [],
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "new_start", "offset": 6}, {"xpath": "new_end", "offset": 7}]],
                    "type": "html",
                }
            },
        },
    }
    assert not DeepDiff(new_object_answers_dict, EXPECTED_NEW_OBJECT_ANSWERS_DICT)


def test_update_annotation_for_object_reflected_on_different_spaces(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_TWO_HTML_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-1-uuid", type_="html")
    html_space_2 = label_row._get_space(id="html-2-uuid", type_="html")
    object_instance = html_text_obj_ontology_item.create_instance()

    current_range = HtmlRange(start=HtmlNode(xpath="start", offset=0), end=HtmlNode(xpath="end", offset=1))
    new_range = HtmlRange(start=HtmlNode(xpath="new_start", offset=6), end=HtmlNode(xpath="new_end", offset=7))

    name = "james@encord.com"
    new_name = "timmy@encord.com"

    date = datetime(2020, 1, 1)
    new_date = datetime(2020, 5, 5)

    html_space_1.put_object_instance(
        object_instance=object_instance,
        ranges=current_range,
        last_edited_by=name,
        last_edited_at=date,
        created_at=date,
    )

    html_space_2.put_object_instance(
        object_instance=object_instance,
        ranges=current_range,
    )

    current_label_row_dict = label_row.to_encord_dict()
    current_object_answers_dict = current_label_row_dict["object_answers"]

    EXPECTED_CURRENT_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "createdBy": None,
            "createdAt": format_datetime_to_long_string(date),
            "lastEditedAt": format_datetime_to_long_string(date),
            "lastEditedBy": name,
            "manualAnnotation": True,
            "shape": "text",
            "classifications": [],
            "range": [],
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "start", "offset": 0}, {"xpath": "end", "offset": 1}]],
                    "type": "html",
                },
                "html-2-uuid": {
                    "range": [[{"xpath": "start", "offset": 0}, {"xpath": "end", "offset": 1}]],
                    "type": "html",
                },
            },
        },
    }

    assert not DeepDiff(current_object_answers_dict, EXPECTED_CURRENT_OBJECT_ANSWERS_DICT)

    # Act
    object_annotations = list(html_space_1.get_object_instance_annotations())
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.ranges = new_range

    # Assert
    new_label_row_dict = label_row.to_encord_dict()
    new_object_answers_dict = new_label_row_dict["object_answers"]

    object_annotation_on_html_space_2 = list(html_space_2.get_object_instance_annotations())[0]

    # Metadata of object on space is updated (because its the same object)
    assert object_annotation_on_html_space_2.created_by == new_name
    assert object_annotation_on_html_space_2.created_at == new_date
    assert object_annotation_on_html_space_2.last_edited_by == new_name
    assert object_annotation_on_html_space_2.last_edited_at == new_date

    # But range is still the same
    assert object_annotation_on_html_space_2.ranges == [current_range]
    EXPECTED_NEW_OBJECT_ANSWERS_DICT = {
        object_instance.object_hash: {
            "objectHash": object_instance.object_hash,
            "featureHash": "textFeatureNodeHash",
            "name": "text object",
            "value": "text_object",
            "color": "#A4FF00",
            "createdBy": new_name,
            "createdAt": format_datetime_to_long_string(new_date),
            "lastEditedAt": format_datetime_to_long_string(new_date),
            "lastEditedBy": new_name,
            "manualAnnotation": True,
            "shape": "text",
            "classifications": [],
            "range": [],
            "spaces": {
                "html-1-uuid": {
                    "range": [[{"xpath": "new_start", "offset": 6}, {"xpath": "new_end", "offset": 7}]],
                    "type": "html",
                },
                "html-2-uuid": {
                    "range": [[{"xpath": "start", "offset": 0}, {"xpath": "end", "offset": 1}]],
                    "type": "html",
                },
            },
        },
    }
    assert not DeepDiff(new_object_answers_dict, EXPECTED_NEW_OBJECT_ANSWERS_DICT)
