import uuid
from datetime import datetime
from unittest.mock import MagicMock

from encord.http.bundle import Bundle
from encord.workflow import AnnotationStage, AnnotationTask, Workflow


def test_bulk_assign_annotations(workflow: Workflow) -> None:
    annotation_stage = workflow.get_stage(name="Annotation 1", type_=AnnotationStage)

    annotation_stage._workflow_client.api_client.get_paged_iterator.return_value = iter(
        [
            AnnotationTask(
                uuid=uuid.uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                data_hash=uuid.uuid4(),
                data_title=f"data unit {x}",
                label_branch_name="main",
                assignee=None,
            )
            for x in range(0, 3)
        ]
    )

    action_resource = MagicMock()
    annotation_stage._workflow_client.api_client.post = action_resource

    bundle = Bundle()
    for task in annotation_stage.get_tasks():
        task.assign("test-user@encord.com", bundle=bundle)

    assert not action_resource.called

    bundle.execute()

    assert action_resource.called
    assert isinstance(action_resource.call_args[1]["payload"], list)
    assert len(action_resource.call_args[1]["payload"]) == 3
