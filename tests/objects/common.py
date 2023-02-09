import datetime

from encord.objects.constants import LabelStatus
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata

FAKE_LABEL_ROW_METADATA = LabelRowMetadata(
    label_hash="",
    created_at=datetime.datetime.now(),
    last_edited_at=datetime.datetime.now(),
    data_hash="",
    dataset_hash="",
    data_title="",
    data_type="IMG_GROUP",
    label_status=LabelStatus.NOT_LABELLED,
    annotation_task_status=AnnotationTaskStatus.QUEUED,
    is_shadow_data=False,
    duration=100,
    frames_per_second=25,
    number_of_frames=100 * 25,
)
