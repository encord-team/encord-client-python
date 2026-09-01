from datetime import datetime
from unittest.mock import Mock

from encord.constants.enums import DataType, SpaceType
from encord.objects import LabelRowV2, Object, OntologyStructure, Shape
from encord.objects.constants import ROOT_SPACE_ID
from encord.objects.coordinates import TimeRangeCoordinates
from encord.objects.frames import Range
from encord.objects.spaces.range_space.time_series_space import TimeSeriesSpace
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus
from tests.objects.data.all_types_ontology_structure import GLOBAL_CLASSIFICATION, RADIO_CLASSIFICATION


def _time_series_label_row() -> LabelRowV2:
    time_range_object = Object(
        uid=1,
        name="time range object",
        color="#A4FF00",
        shape=Shape.TIME_RANGE,
        feature_node_hash="timeRangeFeatureHash",
    )
    ontology = Mock(structure=OntologyStructure(objects=[time_range_object]))
    space_info = {
        "space_type": SpaceType.TIME_SERIES,
        "child_info": {
            "layout_key": "timeseries_signal",
            "file_name": "time-series.csv",
            "data_link": "cord-timeseries-dev/test-org/time-series.csv",
        },
        "labels": {},
    }
    metadata = LabelRowMetadata(
        label_hash="time-series-label-hash",
        branch_name="main",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        data_hash="time-series-data-hash",
        dataset_hash="dataset-hash",
        dataset_title="Dataset",
        data_title="time-series.csv",
        data_type=DataType.TIME_SERIES,
        data_link="cord-timeseries-dev/test-org/time-series.csv",
        label_status=LabelStatus.LABEL_IN_PROGRESS,
        annotation_task_status=AnnotationTaskStatus.QUEUED,
        workflow_graph_node=None,
        is_shadow_data=False,
        frames_per_second=1000,
        number_of_frames=5 * 60 * 1000,
        duration=5 * 60,
        height=None,
        width=None,
        audio_codec=None,
        audio_bit_depth=None,
        audio_num_channels=None,
        audio_sample_rate=None,
        spaces={"time-series-space-uuid": space_info},
        file_type="text/csv",
    )
    labels = {
        "label_hash": "time-series-label-hash",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "time-series-data-hash",
        "dataset_hash": "dataset-hash",
        "dataset_title": "Dataset",
        "data_title": "time-series.csv",
        "data_type": DataType.TIME_SERIES,
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "object_answers": {},
        "classification_answers": {},
        "object_actions": {},
        "label_status": "LABEL_IN_PROGRESS",
        "spaces": {"time-series-space-uuid": space_info},
        "data_units": {
            "time-series-data-hash": {
                "data_hash": "time-series-data-hash",
                "data_sequence": 0,
                "data_title": "time-series.csv",
                "data_type": "text/csv",
                "data_link": "cord-timeseries-dev/test-org/time-series.csv",
                "labels": {},
            }
        },
    }

    label_row = LabelRowV2(metadata, Mock(), ontology)
    label_row.from_labels_dict(labels)
    return label_row


def _standalone_time_series_label_row() -> LabelRowV2:
    time_range_object = Object(
        uid=1,
        name="time range object",
        color="#A4FF00",
        shape=Shape.TIME_RANGE,
        feature_node_hash="timeRangeFeatureHash",
    )
    ontology = Mock(structure=OntologyStructure(objects=[time_range_object]))
    metadata = LabelRowMetadata(
        label_hash="time-series-label-hash",
        branch_name="main",
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
        data_hash="time-series-data-hash",
        dataset_hash="dataset-hash",
        dataset_title="Dataset",
        data_title="time-series.csv",
        data_type=DataType.TIME_SERIES,
        data_link="cord-timeseries-dev/test-org/time-series.csv",
        label_status=LabelStatus.LABEL_IN_PROGRESS,
        annotation_task_status=AnnotationTaskStatus.QUEUED,
        workflow_graph_node=None,
        is_shadow_data=False,
        frames_per_second=None,
        number_of_frames=None,
        duration=None,
        height=None,
        width=None,
        audio_codec=None,
        audio_bit_depth=None,
        audio_num_channels=None,
        audio_sample_rate=None,
        spaces={},
        file_type="text/csv",
    )
    labels = {
        "label_hash": "time-series-label-hash",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "time-series-data-hash",
        "dataset_hash": "dataset-hash",
        "dataset_title": "Dataset",
        "data_title": "time-series.csv",
        "data_type": "time_series",
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "object_answers": {
            "time-series-object-hash": {
                "objectHash": "time-series-object-hash",
                "classifications": [],
                "range": [[1133, 2065]],
                "featureHash": "timeRangeFeatureHash",
                "manualAnnotation": True,
                "createdAt": "Thu, 09 Feb 2023 14:12:03 UTC",
                "createdBy": "user@example.com",
                "lastEditedAt": "Thu, 09 Feb 2023 14:12:03 UTC",
                "lastEditedBy": "user@example.com",
            }
        },
        "classification_answers": {},
        "object_actions": {},
        "label_status": "LABEL_IN_PROGRESS",
        "spaces": {},
        "data_units": {
            "time-series-data-hash": {
                "data_hash": "time-series-data-hash",
                "data_sequence": 0,
                "data_title": "time-series.csv",
                "data_type": "text/csv",
                "data_link": "cord-timeseries-dev/test-org/time-series.csv",
                "labels": {},
            }
        },
    }

    label_row = LabelRowV2(metadata, Mock(), ontology)
    label_row.from_labels_dict(labels)
    return label_row


def test_put_object_on_time_series_space():
    label_row = _time_series_label_row()
    time_series_space = label_row.get_space(id="time-series-space-uuid", type_="time_series")
    time_range_object = label_row._ontology.structure.objects[0]

    object_instance = time_range_object.create_instance()
    time_series_space.put_object_instance(object_instance=object_instance, ranges=Range(start=0, end=100))

    assert isinstance(time_series_space, TimeSeriesSpace)
    assert time_series_space.get_object_ranges(object_instance) == [Range(start=0, end=100)]

    encord_dict = label_row.to_encord_dict()
    object_answer = next(iter(encord_dict["object_answers"].values()))
    assert encord_dict["data_type"] == "time_series"
    assert encord_dict["spaces"]["time-series-space-uuid"]["space_type"] == SpaceType.TIME_SERIES
    assert object_answer["shape"] == "time_range"
    assert object_answer["spaces"] == {"time-series-space-uuid": {"range": [[0, 100]], "type": "frame"}}


def test_standalone_time_series_uses_regular_label_row_api():
    label_row = _standalone_time_series_label_row()

    assert label_row.data_type == DataType.TIME_SERIES
    assert label_row.get_spaces() == []

    object_instance = label_row.get_object_instances()[0]
    assert object_instance.range_list == [Range(start=1133, end=2065)]

    encord_dict = label_row.to_encord_dict()
    object_answer = encord_dict["object_answers"]["time-series-object-hash"]
    assert encord_dict["data_type"] == "time_series"
    assert encord_dict["spaces"] == {}
    assert object_answer["shape"] == "time_range"
    assert object_answer["range"] == [[1133, 2065]]
    assert "spaces" not in object_answer

    label_row.from_labels_dict(encord_dict)
    assert label_row.get_spaces() == []
    assert label_row.get_object_instances()[0].range_list == [Range(start=1133, end=2065)]


def test_add_time_range_object_on_standalone_time_series_root():
    label_row = _standalone_time_series_label_row()
    time_range_object = label_row._ontology.structure.objects[0]
    object_instance = time_range_object.create_instance()
    object_instance.set_for_frames(coordinates=TimeRangeCoordinates(range=[Range(start=0, end=100)]))

    label_row.add_object_instance(object_instance=object_instance)

    encord_dict = label_row.to_encord_dict()
    object_answer = encord_dict["object_answers"][object_instance.object_hash]
    assert object_answer["shape"] == "time_range"
    assert object_answer["range"] == [[0, 100]]
    assert "spaces" not in object_answer


def test_root_time_series_classifications_serialize_as_root_ranges():
    space = TimeSeriesSpace(
        space_id=ROOT_SPACE_ID,
        label_row=Mock(),
        space_info={
            "space_type": SpaceType.TIME_SERIES,
            "root_info": {"file_name": "time-series.csv"},
            "labels": {},
        },
    )

    global_classification = GLOBAL_CLASSIFICATION.create_instance()
    space.put_classification_instance(
        global_classification,
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
    )

    classification = RADIO_CLASSIFICATION.create_instance()
    classification.set_answer("cl_1_option_1")
    space.put_classification_instance(
        classification,
        created_at=datetime.now(),
        last_edited_at=datetime.now(),
    )

    answers = space._to_classification_answers({})
    assert len(answers) == 2
    for answer in answers.values():
        assert answer["range"] == []
        assert answer["spaces"] == {}
