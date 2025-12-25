from datetime import datetime
from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import LabelRowV2, Object
from encord.objects.coordinates import HtmlCoordinates
from encord.objects.html_node import HtmlNode, HtmlRange
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.all_modalities import (
    DATA_GROUP_METADATA,
    DATA_GROUP_NO_LABELS,
)

# Use the existing text object for HTML space tests (HTML uses text shape)
html_obj_ontology_item = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)


def test_place_object_on_html_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")

    # Act
    new_object_instance = html_obj_ontology_item.create_instance()
    html_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=html_range,
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 1

    objects_on_space = html_space_1.get_object_instances()
    object_on_space = objects_on_space[0]
    assert len(objects_on_space) == 1
    assert object_on_space._spaces == {html_space_1.space_id: html_space_1}

    annotations = html_space_1.get_object_instance_annotations()
    assert len(annotations) == 1

    first_annotation = annotations[0]
    assert first_annotation.frame == 0  # Frame is here for backwards compatibility
    assert first_annotation.coordinates == HtmlCoordinates(range=[html_range])
    assert first_annotation.object_hash == new_object_instance.object_hash


def test_place_object_with_multiple_ranges(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")

    # Act
    new_object_instance = html_obj_ontology_item.create_instance()
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
    annotations = html_space_1.get_object_instance_annotations()
    assert len(annotations) == 1
    assert annotations[0].coordinates == HtmlCoordinates(range=html_ranges)


def test_put_objects_with_error_overlapping_strategy(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    new_object_instance = html_obj_ontology_item.create_instance()
    html_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=html_range,
    )

    # Act
    with pytest.raises(LabelRowError) as e:
        html_space_1.put_object_instance(
            object_instance=new_object_instance,
            ranges=html_range,
        )

    assert "already exists" in e.value.message
    assert "on_overlap" in e.value.message


def test_put_objects_with_replace_overlapping_strategy(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    new_object_instance = html_obj_ontology_item.create_instance()
    original_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=original_range,
    )

    # Act
    new_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[2]", offset=5),
        end=HtmlNode(xpath="/html/body/p[2]", offset=15),
    )
    html_space_1.put_object_instance(
        object_instance=new_object_instance,
        ranges=new_range,
        on_overlap="replace",
    )

    # Assert
    object_annotations = html_space_1.get_object_instance_annotations()
    assert len(object_annotations) == 1
    assert object_annotations[0].coordinates == HtmlCoordinates(range=[new_range])


def test_remove_object_from_html_space(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    new_object_instance = html_obj_ontology_item.create_instance()

    html_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    html_space_1.put_object_instance(object_instance=new_object_instance, ranges=html_range)

    # Act
    html_space_1.remove_object_instance(
        object_hash=new_object_instance.object_hash,
    )

    # Assert
    object_instances = label_row.get_object_instances()
    assert len(object_instances) == 0

    objects_on_space = html_space_1.get_object_instances()
    assert len(objects_on_space) == 0

    annotations_on_space = html_space_1.get_object_instance_annotations()
    assert len(annotations_on_space) == 0

    annotations_on_object = new_object_instance.get_annotations()
    assert len(annotations_on_object) == 0


def test_get_object_annotations(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    object_instance_1 = html_obj_ontology_item.create_instance()
    object_instance_2 = html_obj_ontology_item.create_instance()

    range_1 = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    range_2 = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[2]", offset=5),
        end=HtmlNode(xpath="/html/body/p[2]", offset=15),
    )

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
    object_annotations = html_space_1.get_object_instance_annotations()
    first_annotation = object_annotations[0]
    second_annotation = object_annotations[1]

    # Assert
    assert len(object_annotations) == 2

    assert first_annotation.space.space_id == "html-uuid"
    assert first_annotation.frame == 0  # Frame here for backwards compatibility
    assert first_annotation.object_hash == object_instance_1.object_hash
    assert first_annotation.coordinates == HtmlCoordinates(range=[range_1])
    assert first_annotation.last_edited_by == name_1
    assert first_annotation.last_edited_at == date1

    assert second_annotation.space.space_id == "html-uuid"
    assert second_annotation.frame == 0  # Frame here for backwards compatibility
    assert second_annotation.object_hash == object_instance_2.object_hash
    assert second_annotation.coordinates == HtmlCoordinates(range=[range_2])
    assert second_annotation.last_edited_by == name_2
    assert second_annotation.last_edited_at == date2


def test_get_object_annotations_with_filter_objects(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    object_instance_1 = html_obj_ontology_item.create_instance()
    object_instance_2 = html_obj_ontology_item.create_instance()

    range_1 = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    range_2 = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[2]", offset=5),
        end=HtmlNode(xpath="/html/body/p[2]", offset=15),
    )

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
    object_annotations_for_object_1 = html_space_1.get_object_instance_annotations(
        filter_object_instances=[object_instance_1.object_hash]
    )
    first_annotation_for_object_1 = object_annotations_for_object_1[0]

    object_annotations_for_object_2 = html_space_1.get_object_instance_annotations(
        filter_object_instances=[object_instance_2.object_hash]
    )
    first_annotation_for_object_2 = object_annotations_for_object_2[0]

    # Assert
    assert len(object_annotations_for_object_1) == 1
    assert first_annotation_for_object_1.space.space_id == "html-uuid"
    assert first_annotation_for_object_1.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.coordinates == HtmlCoordinates(range=[range_1])
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "html-uuid"
    assert first_annotation_for_object_2.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.coordinates == HtmlCoordinates(range=[range_2])
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_get_object_annotations_from_object_instance(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    object_instance_1 = html_obj_ontology_item.create_instance()
    object_instance_2 = html_obj_ontology_item.create_instance()

    range_1 = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    range_2 = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[2]", offset=5),
        end=HtmlNode(xpath="/html/body/p[2]", offset=15),
    )

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
    assert first_annotation_for_object_1.space.space_id == "html-uuid"
    assert first_annotation_for_object_1.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_1.object_hash == object_instance_1.object_hash
    assert first_annotation_for_object_1.coordinates == HtmlCoordinates(range=[range_1])
    assert first_annotation_for_object_1.last_edited_by == name_1
    assert first_annotation_for_object_1.last_edited_at == date1

    assert len(object_annotations_for_object_2) == 1
    assert first_annotation_for_object_2.space.space_id == "html-uuid"
    assert first_annotation_for_object_2.frame == 0  # Frame here for backwards compatibility
    assert first_annotation_for_object_2.object_hash == object_instance_2.object_hash
    assert first_annotation_for_object_2.coordinates == HtmlCoordinates(range=[range_2])
    assert first_annotation_for_object_2.last_edited_by == name_2
    assert first_annotation_for_object_2.last_edited_at == date2


def test_update_annotation_from_object_annotation_using_coordinates(ontology):
    # Arrange
    label_row = LabelRowV2(DATA_GROUP_METADATA, Mock(), ontology)
    label_row.from_labels_dict(DATA_GROUP_NO_LABELS)
    html_space_1 = label_row._get_space(id="html-uuid", type_="html")
    object_instance = html_obj_ontology_item.create_instance()

    current_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[1]", offset=0),
        end=HtmlNode(xpath="/html/body/p[1]", offset=10),
    )
    new_range = HtmlRange(
        start=HtmlNode(xpath="/html/body/p[2]", offset=5),
        end=HtmlNode(xpath="/html/body/p[2]", offset=15),
    )

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

    # Act
    object_annotations = html_space_1.get_object_instance_annotations()
    object_annotation = object_annotations[0]

    object_annotation.created_by = new_name
    object_annotation.created_at = new_date
    object_annotation.last_edited_by = new_name
    object_annotation.last_edited_at = new_date
    object_annotation.coordinates = HtmlCoordinates(range=[new_range])

    # Assert
    updated_annotations = html_space_1.get_object_instance_annotations()
    assert len(updated_annotations) == 1
    assert updated_annotations[0].coordinates == HtmlCoordinates(range=[new_range])
    assert updated_annotations[0].created_by == new_name
    assert updated_annotations[0].last_edited_by == new_name
