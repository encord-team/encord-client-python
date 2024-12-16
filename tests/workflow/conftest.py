import uuid
from unittest.mock import MagicMock

from pytest import fixture

from encord.orm.workflow import Workflow as WorkflowDTO
from encord.orm.workflow import WorkflowNode, WorkflowStageType
from encord.workflow import Workflow

WORKFLOW_ANNOTATION_UUID = uuid.uuid4()
WORKFLOW_REVIEW_UUID = uuid.uuid4()
WORKFLOW_COMPLETE_UUID = uuid.uuid4()

workflow_dto = WorkflowDTO(
    stages=[
        WorkflowNode(uuid=WORKFLOW_ANNOTATION_UUID, stage_type=WorkflowStageType.ANNOTATION, title="Annotation 1"),
        WorkflowNode(uuid=WORKFLOW_REVIEW_UUID, stage_type=WorkflowStageType.REVIEW, title="Review 1"),
        WorkflowNode(uuid=WORKFLOW_COMPLETE_UUID, stage_type=WorkflowStageType.DONE, title="Complete"),
    ]
)


@fixture
def workflow() -> Workflow:
    return Workflow(MagicMock(), uuid.uuid4(), workflow_dto)
