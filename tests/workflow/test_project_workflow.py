from encord.workflow import Workflow


def test_project_workflow_get_stage(workflow: Workflow) -> None:
    stage_name_to_uuid = {stage.title: stage.uuid for stage in workflow.stages}
    review_stage_uuid = stage_name_to_uuid["Review 1"]

    assert workflow.get_stage(uuid=review_stage_uuid).title == "Review 1"
    assert workflow.get_stage(uuid=str(review_stage_uuid)).title == "Review 1"
    assert workflow.get_stage(name="Review 1").uuid == review_stage_uuid
