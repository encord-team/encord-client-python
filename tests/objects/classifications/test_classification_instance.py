from datetime import datetime

from encord.objects import ClassificationInstance
from tests.objects.test_label_structure import checklist_classification, text_classification


def test_classification_instance_data_api() -> None:
    """Test that ClassificationInstance properties match annotation properties for video, audio, and text."""
    now = datetime.now()
    test_confidence = 0.75
    test_created_by = "test_user@example.com"
    test_edited_by = "editor@example.com"

    # Test for video (geometric data type)
    video_classification_instance = ClassificationInstance(text_classification)
    video_classification_instance.set_for_frames(
        frames=0,
        created_at=now,
        created_by=test_created_by,
        confidence=test_confidence,
        last_edited_at=now,
        last_edited_by=test_edited_by,
    )

    video_frame_annotation = video_classification_instance.get_annotation(0)

    assert video_classification_instance.created_at == video_frame_annotation.created_at == now
    assert video_classification_instance.created_by == video_frame_annotation.created_by == test_created_by
    assert video_classification_instance.confidence == video_frame_annotation.confidence == test_confidence
    assert video_classification_instance.last_edited_at == video_frame_annotation.last_edited_at == now
    assert video_classification_instance.last_edited_by == video_frame_annotation.last_edited_by == test_edited_by

    # Test for audio (non-geometric data type with range_only=True)
    audio_classification_instance = ClassificationInstance(text_classification, range_only=True)
    audio_classification_instance.set_for_frames(
        created_at=now,
        created_by=test_created_by,
        confidence=test_confidence,
        last_edited_at=now,
        last_edited_by=test_edited_by,
    )

    mock_audio_frame_annotation = audio_classification_instance.get_annotation(0)

    assert audio_classification_instance.created_at == mock_audio_frame_annotation.created_at
    assert audio_classification_instance.created_by == mock_audio_frame_annotation.created_by
    assert audio_classification_instance.confidence == mock_audio_frame_annotation.confidence
    assert audio_classification_instance.last_edited_at == mock_audio_frame_annotation.last_edited_at
    assert audio_classification_instance.last_edited_by == mock_audio_frame_annotation.last_edited_by

    # Test for plain text (non-geometric data type with range_only=True)
    text_classification_instance = ClassificationInstance(checklist_classification, range_only=True)
    text_classification_instance.set_for_frames(
        created_at=now,
        created_by=test_created_by,
        confidence=test_confidence,
        last_edited_at=now,
        last_edited_by=test_edited_by,
    )

    mock_text_frame_annotation = text_classification_instance.get_annotation(0)

    assert text_classification_instance.created_at == mock_text_frame_annotation.created_at
    assert text_classification_instance.created_by == mock_text_frame_annotation.created_by
    assert text_classification_instance.confidence == mock_text_frame_annotation.confidence
    assert text_classification_instance.last_edited_at == mock_text_frame_annotation.last_edited_at
    assert text_classification_instance.last_edited_by == mock_text_frame_annotation.last_edited_by
