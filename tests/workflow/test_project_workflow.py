from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from encord.orm.workflow import WorkflowAgentNode, WorkflowDTO
from encord.workflow import Workflow
from encord.workflow.stages.agent import AgentStage, AgentTask, AgentTaskStatus
from encord.workflow.stages.review import ReviewStage

raw_agent_workflow: Dict[str, Any] = {
    "stages": [
        {
            "stageType": "AGENT",
            "uuid": "9d6edee0-ba3e-423c-8c96-0140b07c93ed",
            "title": "Pre-labeler",
            "pathways": [
                {
                    "uuid": "ae956722-561f-4586-b6d6-145e2f64b18a",
                    "title": "Pre-labelling",
                    "destinationUuid": "1252fdb8-93cb-41a2-b341-b83ab97b5277",
                }
            ],
        },
        {"stageType": "ANNOTATION", "uuid": "1252fdb8-93cb-41a2-b341-b83ab97b5277", "title": "Annotate"},
        {"stageType": "REVIEW", "uuid": "8cac6636-2ef1-4bbe-848a-b5ffee158c34", "title": "Review"},
        {"stageType": "DONE", "uuid": "7e7598de-612c-40c4-ba08-5dfec8c3ae8f", "title": "Complete"},
    ]
}


def test_project_workflow_get_stage(workflow: Workflow) -> None:
    stage_name_to_uuid = {stage.title: stage.uuid for stage in workflow.stages}
    review_stage_uuid = stage_name_to_uuid["Review 1"]

    assert workflow.get_stage(uuid=review_stage_uuid).title == "Review 1"
    assert workflow.get_stage(uuid=str(review_stage_uuid)).title == "Review 1"
    assert workflow.get_stage(name="Review 1").uuid == review_stage_uuid
    assert isinstance(workflow.get_stage(name="Review 1"), ReviewStage)
    with pytest.raises(ValueError):
        workflow.get_stage(name="NAME NOT FOUND")
    with pytest.raises(ValueError):
        workflow.get_stage(uuid=uuid4())


def test_agent_project_with_pathway_serialisation_deserialisation() -> None:
    workflow_dto = WorkflowDTO.from_dict(raw_agent_workflow)
    assert workflow_dto.stages
    agent_stage = workflow_dto.stages[0]
    assert isinstance(agent_stage, WorkflowAgentNode)
    assert agent_stage.pathways
    workflow_obj = Workflow(MagicMock(), uuid4(), workflow_orm=workflow_dto)
    agent_stage = workflow_obj.get_stage(name="Pre-labeler")
    assert isinstance(agent_stage, AgentStage)
    assert agent_stage.pathways


def test_agent_stage_get_tasks_no_http_requests() -> None:
    """Verify that iterating through agent tasks and accessing issues property doesn't make HTTP requests."""
    workflow_dto = WorkflowDTO.from_dict(raw_agent_workflow)
    workflow_client = MagicMock()
    api_client = MagicMock()
    workflow_client.api_client = api_client
    workflow_obj = Workflow(workflow_client, uuid4(), workflow_orm=workflow_dto)
    agent_stage = workflow_obj.get_stage(name="Pre-labeler")

    # Mock get_tasks to return some tasks
    mock_tasks = [
        AgentTask(
            uuid=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            data_hash=uuid4(),
            data_title=f"data unit {i}",
            label_branch_name="main",
            assignee=None,
            last_actioned_by=None,
            status=AgentTaskStatus.NEW,
        )
        for i in range(3)
    ]
    workflow_client.get_tasks.return_value = iter(mock_tasks)

    # Iterate through tasks and access issues property
    for task in agent_stage.get_tasks():
        # Just accessing the issues property should not trigger HTTP calls
        assert task.issues is not None

    # Verify no HTTP requests were made during iteration
    # Check all common HTTP methods on the api_client
    api_client.get.assert_not_called()
    api_client.post.assert_not_called()
    api_client.put.assert_not_called()
    api_client.patch.assert_not_called()
    api_client.delete.assert_not_called()
