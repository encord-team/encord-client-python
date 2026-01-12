from unittest.mock import Mock

import pytest

from encord.exceptions import LabelRowError
from encord.objects import Classification, LabelRowV2, Object
from encord.objects.attributes import Attribute
from encord.objects.coordinates import BoundingBoxCoordinates
from encord.objects.frames import Range
from encord.objects.html_node import HtmlNode, HtmlRange
from encord.objects.ontology_labels_impl import LABELLING_NOT_INITIALISED_ERROR_MESSAGE
from encord.objects.spaces.multiframe_space.video_space import VideoSpace
from tests.objects.data.all_types_ontology_structure import all_types_structure
from tests.objects.data.data_group.all_modalities import DATA_GROUP_METADATA as ALL_MODALITIES_DATA_GROUP

# Ontology items used across tests
box_ontology_item = all_types_structure.get_child_by_hash("MjI2NzEy", Object)
box_with_attributes_ontology_item = all_types_structure.get_child_by_hash("MTA2MjAx", Object)
box_text_attribute_ontology_item = box_with_attributes_ontology_item.get_child_by_hash("OTkxMjU1", type_=Attribute)
audio_obj_ontology_item = all_types_structure.get_child_by_hash("KVfzNkFy", Object)
text_obj_ontology_item = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)
html_obj_ontology_item = all_types_structure.get_child_by_hash("textFeatureNodeHash", Object)


# Space fixtures
@pytest.fixture
def uninitialised_image_space(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)
    return label_row._get_space(id="image-uuid", type_="image")


@pytest.fixture
def uninitialised_video_space(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)
    return label_row._get_space(id="video-uuid", type_="video")


@pytest.fixture
def uninitialised_audio_space(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)
    return label_row._get_space(id="audio-uuid", type_="audio")


@pytest.fixture
def uninitialised_text_space(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)
    return label_row._get_space(id="text-uuid", type_="text")


@pytest.fixture
def uninitialised_html_space(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)
    return label_row._get_space(id="html-uuid", type_="html")


def test_get_object_instances_requires_initialisation(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)

    for space in label_row._space_map.values():
        with pytest.raises(LabelRowError) as exc_info:
            space.get_object_instances()

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_get_classification_instances_requires_initialisation(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)

    for space in label_row._space_map.values():
        with pytest.raises(LabelRowError) as exc_info:
            space.get_classification_instances()

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_object_instance_requires_initialisation(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)

    for space in label_row._space_map.values():
        with pytest.raises(LabelRowError) as exc_info:
            space.remove_object_instance(object_hash="random")

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


def test_remove_classification_instance_requires_initialisation(ontology):
    label_row = LabelRowV2(ALL_MODALITIES_DATA_GROUP, Mock(), ontology)

    for space in label_row._space_map.values():
        with pytest.raises(LabelRowError) as exc_info:
            space.remove_classification_instance(classification_hash="random")

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


class TestUninitialisedImageSpace:
    def test_put_object_instance_requires_initialisation(self, uninitialised_image_space):
        new_object_instance = box_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_image_space.put_object_instance(
                object_instance=new_object_instance,
                coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0),
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_put_classification_instance_requires_initialisation(self, uninitialised_image_space):
        text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
        classification_instance = text_classification.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_image_space.put_classification_instance(
                classification_instance=classification_instance,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


class TestUninitialisedVideoSpace:
    def test_put_object_instance_requires_initialisation(self, uninitialised_video_space):
        new_object_instance = box_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.put_object_instance(
                object_instance=new_object_instance,
                frames=[1],
                coordinates=BoundingBoxCoordinates(height=1.0, width=1.0, top_left_x=1.0, top_left_y=1.0),
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_remove_object_instance_from_frames_requires_initialisation(self, uninitialised_video_space):
        new_object_instance = box_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.remove_object_instance_from_frames(
                object_instance=new_object_instance,
                frames=[1],
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_set_answer_on_frames_requires_initialisation(self, uninitialised_video_space):
        new_object_instance = box_with_attributes_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.set_answer_on_frames(
                object_instance=new_object_instance,
                frames=[1],
                answer="test answer",
                attribute=box_text_attribute_ontology_item,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_remove_answer_from_frame_requires_initialisation(self, uninitialised_video_space):
        new_object_instance = box_with_attributes_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.remove_answer_from_frame(
                object_instance=new_object_instance,
                attribute=box_text_attribute_ontology_item,
                frame=1,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_get_answer_on_frames_requires_initialisation(self, uninitialised_video_space):
        new_object_instance = box_with_attributes_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.get_answer_on_frames(
                object_instance=new_object_instance,
                frames=[1],
                attribute=box_text_attribute_ontology_item,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_put_classification_instance_requires_initialisation(self, uninitialised_video_space):
        text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
        classification_instance = text_classification.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.put_classification_instance(
                classification_instance=classification_instance,
                frames=[1],
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_remove_classification_instance_from_frames_requires_initialisation(self, uninitialised_video_space):
        text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
        classification_instance = text_classification.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.remove_classification_instance_from_frames(
                classification_instance=classification_instance,
                frames=[1],
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_get_object_instance_annotations_requires_initialisation(self, uninitialised_video_space: VideoSpace):
        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.get_annotations(type_="object")

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_get_object_instance_annotations_by_frame_requires_initialisation(
        self, uninitialised_video_space: VideoSpace
    ):
        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.get_annotations_by_frame(type_="object")

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_get_classification_instance_annotations_requires_initialisation(
        self, uninitialised_video_space: VideoSpace
    ):
        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_video_space.get_annotations(type_="classification")

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


class TestUninitialisedAudioSpace:
    def test_put_object_instance_requires_initialisation(self, uninitialised_audio_space):
        new_object_instance = audio_obj_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_audio_space.put_object_instance(
                object_instance=new_object_instance,
                ranges=Range(start=0, end=100),
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_remove_object_instance_from_range_requires_initialisation(self, uninitialised_audio_space):
        new_object_instance = audio_obj_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_audio_space.remove_object_instance_from_range(
                object_instance=new_object_instance,
                ranges=Range(start=0, end=100),
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_put_classification_instance_requires_initialisation(self, uninitialised_audio_space):
        text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
        classification_instance = text_classification.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_audio_space.put_classification_instance(
                classification_instance=classification_instance,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


class TestUninitialisedTextSpace:
    def test_put_object_instance_requires_initialisation(self, uninitialised_text_space):
        new_object_instance = text_obj_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_text_space.put_object_instance(
                object_instance=new_object_instance,
                ranges=Range(start=0, end=100),
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_remove_object_instance_from_range_requires_initialisation(self, uninitialised_text_space):
        new_object_instance = text_obj_ontology_item.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_text_space.remove_object_instance_from_range(
                object_instance=new_object_instance,
                ranges=Range(start=0, end=100),
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_put_classification_instance_requires_initialisation(self, uninitialised_text_space):
        text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
        classification_instance = text_classification.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_text_space.put_classification_instance(
                classification_instance=classification_instance,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE


class TestUninitialisedHtmlSpace:
    def test_put_object_instance_requires_initialisation(self, uninitialised_html_space):
        new_object_instance = html_obj_ontology_item.create_instance()
        html_range = HtmlRange(
            start=HtmlNode(xpath="/html/body/p[1]", offset=0),
            end=HtmlNode(xpath="/html/body/p[1]", offset=10),
        )

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_html_space.put_object_instance(
                object_instance=new_object_instance,
                ranges=html_range,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE

    def test_put_classification_instance_requires_initialisation(self, uninitialised_html_space):
        text_classification = all_types_structure.get_child_by_hash("jPOcEsbw", Classification)
        classification_instance = text_classification.create_instance()

        with pytest.raises(LabelRowError) as exc_info:
            uninitialised_html_space.put_classification_instance(
                classification_instance=classification_instance,
            )

        assert exc_info.value.message == LABELLING_NOT_INITIALISED_ERROR_MESSAGE
