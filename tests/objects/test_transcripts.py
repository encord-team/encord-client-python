from copy import deepcopy
from dataclasses import asdict
from unittest.mock import Mock

from encord.objects import (
    LabelRowV2,
    ObjectInstance,
    TranscriptSegment,
)
from encord.objects.attributes import ChecklistAttribute, TextAttribute
from encord.objects.ontology_object import Object
from encord.objects.options import Option
from encord.objects.utils import _lower_snake_case
from encord.orm.label_row import LabelRowMetadata
from tests.objects.common import BASE_LABEL_ROW_METADATA
from tests.objects.data.all_types_ontology_structure import AUDIO_TRANSCRIPT_OBJECT, all_types_structure
from tests.objects.objects_test_utils import validate_label_row_serialisation

audio_transcript_object: Object = all_types_structure.get_child_by_hash(
    AUDIO_TRANSCRIPT_OBJECT.feature_node_hash, type_=Object
)
caption_attr: TextAttribute = all_types_structure.get_child_by_hash("captionTranscriptHash", type_=TextAttribute)
speaker_attr: TextAttribute = all_types_structure.get_child_by_hash("speakerTranscriptHash", type_=TextAttribute)
mood_attr: ChecklistAttribute = all_types_structure.get_child_by_hash(
    "audioMoodChecklistHash", type_=ChecklistAttribute
)
mood_happy: Option = all_types_structure.get_child_by_hash("audioMoodHappy", type_=Option)


OBJECT_HASH = "TrAnSc1234"


def _action(feature_hash: str, name: str, text: str, ranges):
    """Construct a raw object_action dict mimicking what the backend serves."""
    return {
        "name": name,
        "value": _lower_snake_case(name),
        "answers": text,
        "featureHash": feature_hash,
        "manualAnnotation": True,
        "dynamic": True,
        "range": [list(r) for r in ranges],
        "shouldPropagate": False,
        "trackHash": f"track-{text}",
    }


def _audio_label_dict_with_actions(actions, joined_classifications=None):
    """Build an audio label_row dict carrying transcript actions for a single object."""
    classifications = list(joined_classifications) if joined_classifications else []
    return {
        "label_hash": "0aea5ac7-cbc0-4451-a242-e22445d2c9fa",
        "branch_name": "main",
        "created_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "last_edited_at": "Thu, 09 Feb 2023 14:12:03 UTC",
        "data_hash": "aaa6bc82-9f89-4545-adbb-f271bf28cf99",
        "dataset_hash": "b02ba3d9-883b-4c5e-ba09-751072ccfc57",
        "dataset_title": "Audio Dataset",
        "data_title": "sample-audio.mp3",
        "data_type": "audio",
        "annotation_task_status": "QUEUED",
        "is_shadow_data": False,
        "object_answers": {
            OBJECT_HASH: {
                "classifications": classifications,
                "objectHash": OBJECT_HASH,
                "range": [[0, 300]],
                "createdBy": "user1",
                "createdAt": "Thu, 05 Dec 2024 15:24:19 UTC",
                "lastEditedBy": "user1",
                "lastEditedAt": "Thu, 05 Dec 2024 15:24:44 UTC",
                "manualAnnotation": True,
                "featureHash": audio_transcript_object.feature_node_hash,
                "name": audio_transcript_object.name,
                "color": audio_transcript_object.color,
                "shape": "audio",
                "value": _lower_snake_case(audio_transcript_object.name),
            }
        },
        "classification_answers": {},
        "object_actions": {
            OBJECT_HASH: {
                "actions": list(actions),
                "objectHash": OBJECT_HASH,
            }
        },
        "label_status": "LABELLED",
        "spaces": {},
        "data_units": {
            "cd53f484-c9ab-4fd1-9c14-5b34d4e42ba2": {
                "data_hash": "cd53f484-c9ab-4fd1-9c14-5b34d4e42ba2",
                "data_title": "sample-audio.mp3",
                "data_link": "audio-link",
                "data_type": "audio/mpeg",
                "data_sequence": 0,
                "audio_codec": "mp3",
                "audio_sample_rate": 44100,
                "audio_bit_depth": 8,
                "audio_num_channels": 2,
                "labels": {},
                "data_duration": 100,
            }
        },
    }


def _audio_label_row(all_types_ontology) -> LabelRowV2:
    metadata = asdict(BASE_LABEL_ROW_METADATA)
    metadata["frames_per_second"] = 1000
    metadata["data_type"] = "AUDIO"
    metadata["number_of_frames"] = metadata["duration"] * metadata["frames_per_second"]
    return LabelRowV2(LabelRowMetadata(**metadata), Mock(), all_types_ontology)


def _get_obj(label_row: LabelRowV2) -> ObjectInstance:
    objects = label_row.get_object_instances()
    assert len(objects) == 1
    return objects[0]


def test_get_answer_returns_joined_transcript_from_actions(all_types_ontology):
    """Even when classifications is empty, get_answer joins the per-segment actions."""
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "How are you", [(51, 100)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "Goodbye", [(200, 250)]),
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    assert obj.get_answer(caption_attr) == "Hello world\nHow are you\nGoodbye"


def test_get_answer_is_not_overwritten_by_last_action(all_types_ontology):
    """Actions delivered in any order yield the same playback-ordered joined string."""
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Goodbye", [(200, 250)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "How are you", [(51, 100)]),
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    assert obj.get_answer(caption_attr) == "Hello world\nHow are you\nGoodbye"


def test_get_answer_ignores_backend_joined_classification(all_types_ontology):
    """The classifications mirror is informational; actions are the source of truth."""
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "Goodbye", [(200, 250)]),
        ],
        joined_classifications=[
            {
                "name": caption_attr.name,
                "value": _lower_snake_case(caption_attr.name),
                # Deliberately wrong / stale joined value so we catch any code path
                # that reads from classifications instead of from actions.
                "answers": "this should be ignored",
                "featureHash": caption_attr.feature_node_hash,
                "manualAnnotation": True,
            }
        ],
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    assert obj.get_answer(caption_attr) == "Hello world\nGoodbye"


def test_get_transcripts_returns_segments_in_playback_order(all_types_ontology):
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Goodbye", [(200, 250)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "How are you", [(51, 100)]),
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    segments = obj.get_transcripts()
    assert [s.text for s in segments] == ["Hello world", "How are you", "Goodbye"]
    assert [s.range for s in segments] == [(0, 50), (51, 100), (200, 250)]
    assert all(isinstance(s, TranscriptSegment) for s in segments)
    assert all(s.feature_hash == caption_attr.feature_node_hash for s in segments)
    assert all(s.attribute_name == caption_attr.name for s in segments)


def test_get_transcripts_filters_by_attribute(all_types_ontology):
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
            _action(speaker_attr.feature_node_hash, speaker_attr.name, "Alice", [(0, 50)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "How are you", [(51, 100)]),
            _action(speaker_attr.feature_node_hash, speaker_attr.name, "Bob", [(51, 100)]),
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    captions = obj.get_transcripts(caption_attr)
    speakers = obj.get_transcripts(speaker_attr)
    assert [s.text for s in captions] == ["Hello world", "How are you"]
    assert [s.text for s in speakers] == ["Alice", "Bob"]

    # No filter returns all segments across both attributes.
    all_segments = obj.get_transcripts()
    assert len(all_segments) == 4

    # And per-attribute get_answer joins are independent.
    assert obj.get_answer(caption_attr) == "Hello world\nHow are you"
    assert obj.get_answer(speaker_attr) == "Alice\nBob"


def test_get_transcripts_returns_empty_when_no_actions(all_types_ontology):
    label_dict = _audio_label_dict_with_actions(actions=[])
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    assert obj.get_transcripts() == []
    assert obj.get_answer(caption_attr) is None


def test_get_transcripts_unrolls_multi_sub_range_action(all_types_ontology):
    """One action with two sub-ranges produces two TranscriptSegment entries with the same text."""
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "repeated", [(0, 50), (100, 150)]),
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    segments = obj.get_transcripts()
    assert len(segments) == 2
    assert [s.range for s in segments] == [(0, 50), (100, 150)]
    assert all(s.text == "repeated" for s in segments)


def test_non_transcript_dynamic_attributes_still_work_on_transcript_object(all_types_ontology):
    """A non-transcript dynamic attribute on the same object should be unaffected by the partition."""
    mood_action = {
        "name": mood_attr.name,
        "value": _lower_snake_case(mood_attr.name),
        "answers": [
            {
                "name": mood_happy.label,
                "value": mood_happy.value,
                "featureHash": mood_happy.feature_node_hash,
            }
        ],
        "featureHash": mood_attr.feature_node_hash,
        "manualAnnotation": True,
        "dynamic": True,
        "range": [[0, 100]],
        "shouldPropagate": False,
        "trackHash": "mood-track",
    }
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello", [(0, 100)]),
            mood_action,
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    obj = _get_obj(label_row)
    assert obj.get_answer(caption_attr) == "Hello"

    mood_answers = obj.get_answer(mood_attr)
    # Dynamic checklist returns AnswersForFrames; check the one we set.
    assert len(mood_answers) == 1
    assert mood_answers[0].answer == [mood_happy]


def test_round_trip_preserves_transcript_actions(all_types_ontology):
    original_actions = [
        _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
        _action(caption_attr.feature_node_hash, caption_attr.name, "How are you", [(51, 100)]),
        _action(speaker_attr.feature_node_hash, speaker_attr.name, "Alice", [(0, 50)]),
    ]
    label_dict = _audio_label_dict_with_actions(actions=deepcopy(original_actions))
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    serialised = label_row.to_encord_dict()
    out_actions = serialised["object_actions"][OBJECT_HASH]["actions"]

    # Order is not guaranteed (we append in stash order), so compare as sorted by text+range.
    def key(a):
        return (a["featureHash"], a["answers"], tuple(tuple(r) for r in a["range"]))

    assert sorted(out_actions, key=key) == sorted(original_actions, key=key)


def test_full_serialisation_roundtrip_with_transcripts(all_types_ontology):
    """End-to-end: load → save → reload → save again gives identical output."""
    label_dict = _audio_label_dict_with_actions(
        actions=[
            _action(caption_attr.feature_node_hash, caption_attr.name, "Hello world", [(0, 50)]),
            _action(caption_attr.feature_node_hash, caption_attr.name, "Goodbye", [(200, 250)]),
            _action(speaker_attr.feature_node_hash, speaker_attr.name, "Alice", [(0, 250)]),
        ]
    )
    label_row = _audio_label_row(all_types_ontology)
    label_row.from_labels_dict(label_dict)

    validate_label_row_serialisation(label_row)
