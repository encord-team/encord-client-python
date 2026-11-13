from copy import deepcopy
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from encord.beta.workflow_v3 import ExternalStage, UnknownStage
from encord.client import EncordClientProject
from encord.exceptions import EncordException, WrongProjectTypeError
from encord.http.v2.api_client import ApiClient
from encord.orm.project import ProjectDTO
from encord.orm.workflow import WorkflowDTO
from encord.project import Project
from encord.user_client import EncordUserClient
from encord.workflow.stages.agent import AgentStage


def _project_from_payload(payload: Dict[str, Any]) -> Project:
    return Project(MagicMock(), ProjectDTO.from_dict(payload), MagicMock(), MagicMock())


@pytest.mark.parametrize("include_legacy,include_native", [(False, False), (True, False), (False, True), (True, True)])
def test_workflow_availability_checks_each_returned_contract_independently_without_network_access(
    tms3_project_payload: Dict[str, Any], include_legacy: bool, include_native: bool
) -> None:
    tms3_project_payload["workflow"] = {"stages": []} if include_legacy else None
    tms3_project_payload["workflowV3"] = (
        {"id": str(UUID(int=1000)), "stages": [], "pathways": []} if include_native else None
    )
    project = _project_from_payload(tms3_project_payload)

    has_workflow = project.has_workflow
    has_workflow_v3 = project.has_workflow_v3

    assert has_workflow is include_legacy
    assert has_workflow_v3 is include_native
    assert project._client.mock_calls == []
    assert project._api_client.mock_calls == []


@pytest.mark.parametrize("engine_version", [None, "TMS1", "TMS2", "TMS3", "TMS4"])
def test_project_exposes_workflow_v3_when_returned_regardless_of_engine_version(
    tms3_project_payload: Dict[str, Any], engine_version: Optional[str]
) -> None:
    if engine_version is None:
        tms3_project_payload.pop("tmsVersion", None)
    else:
        tms3_project_payload["tmsVersion"] = engine_version

    project = _project_from_payload(tms3_project_payload)

    external = project.workflow_v3.get_stage(name="EXTERNAL", type_=ExternalStage)
    assert external.id == UUID(int=4)
    assert external._client.api_client is project._api_client
    assert external._client.project_id == UUID(project.project_hash)
    with pytest.raises(WrongProjectTypeError, match="workflow_v3"):
        _ = project.workflow


def test_tms3_project_serialization_retains_string_keyed_router_mapping_and_project_datetimes(
    tms3_project_payload: Dict[str, Any],
) -> None:
    response = ProjectDTO.from_dict(tms3_project_payload)

    serialized = response.to_dict()
    restored = ProjectDTO.from_dict(serialized)

    assert serialized["workflowV3"]["stages"][7]["settings"]["pathwayToPercentageMapping"] == {
        str(UUID(int=105)): 0.4,
        str(UUID(int=106)): 0.6,
    }
    assert restored.created_at == response.created_at
    assert restored.last_edited_at == response.last_edited_at
    assert restored.workflow_v3 is not None
    assert restored.workflow_v3.stages == response.workflow_v3.stages
    assert "workflow" not in serialized
    assert "tmsVersion" not in serialized


def test_project_loads_with_an_unfamiliar_stage_without_losing_known_stage_types(
    tms3_project_payload: Dict[str, Any],
) -> None:
    tms3_project_payload["tmsVersion"] = "TMS4"
    tms3_project_payload["workflowV3"]["stages"][0]["stageType"] = "FUTURE_START"

    project = _project_from_payload(tms3_project_payload)

    assert project.workflow_v3.get_stage(id=UUID(int=1), type_=UnknownStage).raw_stage_type == "FUTURE_START"
    assert project.workflow_v3.get_stage(name="EXTERNAL", type_=ExternalStage).id == UUID(int=4)


@pytest.mark.parametrize("by_alias", [False, True])
def test_project_responses_round_trip_unfamiliar_settings_versions_without_losing_raw_configuration(
    tms3_project_payload: Dict[str, Any], by_alias: bool
) -> None:
    raw_settings = {"version": 2, "futureOption": {"values": [1, None]}}
    tms3_project_payload["workflowV3"]["stages"][3]["settings"] = deepcopy(raw_settings)
    response = ProjectDTO.from_dict(tms3_project_payload)

    serialized = response.to_dict(by_alias=by_alias, exclude_none=False)
    restored = ProjectDTO.from_dict(serialized)

    assert restored == response
    project = _project_from_payload(serialized)
    external = project.workflow_v3.get_stage(name="EXTERNAL", type_=ExternalStage)
    assert external.settings.to_dict() == raw_settings


@pytest.mark.parametrize("engine_version", [None, "TMS2", "TMS3", "TMS4"])
def test_project_preserves_legacy_agent_and_final_discovery_regardless_of_engine_version(
    tms3_project_payload: Dict[str, Any], engine_version: Optional[str]
) -> None:
    tms3_project_payload.pop("workflowV3")
    tms3_project_payload["workflowManagerUuid"] = str(UUID(int=2000))
    tms3_project_payload["workflow"] = {
        "stages": [
            {"uuid": str(UUID(int=3)), "title": "Agent", "stageType": "AGENT", "pathways": []},
            {"uuid": str(UUID(int=4)), "title": "Complete", "stageType": "DONE"},
        ]
    }
    if engine_version is None:
        tms3_project_payload.pop("tmsVersion", None)
    else:
        tms3_project_payload["tmsVersion"] = engine_version

    project = _project_from_payload(tms3_project_payload)

    assert isinstance(project.workflow.get_stage(name="Agent"), AgentStage)
    assert project.workflow.get_stage(name="Complete").title == "Complete"
    with pytest.raises(EncordException, match="did not return the workflow_v3 contract"):
        _ = project.workflow_v3


def test_old_manual_qa_response_loads_metadata_without_either_workflow_contract(
    tms3_project_payload: Dict[str, Any],
) -> None:
    tms3_project_payload.pop("workflowV3")
    tms3_project_payload.pop("tmsVersion", None)
    tms3_project_payload["projectType"] = "manual_qa"

    project = _project_from_payload(tms3_project_payload)

    assert project.title == tms3_project_payload["title"]
    with pytest.raises(EncordException, match="did not return the workflow_v3 contract"):
        _ = project.workflow_v3
    with pytest.raises(WrongProjectTypeError, match="did not return the legacy workflow"):
        _ = project.workflow


@pytest.mark.parametrize("engine_version", [None, "TMS3", "TMS4"])
def test_project_without_workflow_v3_loads_metadata_and_reports_the_missing_contract(
    tms3_project_payload: Dict[str, Any], engine_version: Optional[str]
) -> None:
    tms3_project_payload["workflowV3"] = None
    if engine_version is None:
        tms3_project_payload.pop("tmsVersion", None)
    else:
        tms3_project_payload["tmsVersion"] = engine_version

    project = _project_from_payload(tms3_project_payload)

    assert project.title == tms3_project_payload["title"]
    assert not project.has_workflow_v3
    with pytest.raises(EncordException, match=f"workflow_v3 contract for project '{project.project_hash}'"):
        _ = project.workflow_v3


def test_project_can_expose_both_workflow_contracts(tms3_project_payload: Dict[str, Any]) -> None:
    tms3_project_payload["tmsVersion"] = "TMS4"
    tms3_project_payload["workflow"] = {
        "stages": [{"uuid": str(UUID(int=4)), "title": "Agent", "stageType": "AGENT", "pathways": []}]
    }

    project = _project_from_payload(tms3_project_payload)

    legacy_stage = project.workflow.get_stage(name="Agent", type_=AgentStage)
    native_stage = project.workflow_v3.get_stage(name="EXTERNAL", type_=ExternalStage)
    assert project.has_workflow
    assert project.has_workflow_v3
    assert legacy_stage.uuid == native_stage.id == UUID(int=4)


def test_tms3_project_refresh_replaces_graph_and_leaves_previous_stage_objects_as_snapshots(
    tms3_project_payload: Dict[str, Any],
) -> None:
    project = _project_from_payload(tms3_project_payload)
    original_workflow = project.workflow_v3
    original_external = original_workflow.get_stage(name="EXTERNAL")
    original_client = original_external._client
    updated_payload = deepcopy(tms3_project_payload)
    updated_payload["workflowV3"]["stages"][3]["name"] = "Updated external"
    project._client.get_project_v2 = MagicMock(return_value=ProjectDTO.from_dict(updated_payload))

    project.refetch_data()

    assert project.workflow_v3 is not original_workflow
    assert project.workflow_v3.get_stage(name="Updated external").id == original_external.id
    assert original_external.name == "EXTERNAL"
    assert original_workflow.get_stage(name="EXTERNAL") is original_external
    assert original_external._client is original_client
    updated_external = project.workflow_v3.get_stage(name="Updated external")
    assert updated_external._client.api_client is project._api_client
    assert updated_external._client.project_id == UUID(project.project_hash)


def test_project_refresh_exposes_newly_returned_contracts_and_removes_omitted_contracts(
    tms3_project_payload: Dict[str, Any],
) -> None:
    project = _project_from_payload(tms3_project_payload)
    original_workflow = project.workflow_v3
    legacy_payload = deepcopy(tms3_project_payload)
    legacy_payload.pop("workflowV3")
    legacy_payload["workflow"] = {
        "stages": [{"uuid": str(UUID(int=4)), "title": "Agent", "stageType": "AGENT", "pathways": []}]
    }
    project._client.get_project_v2 = MagicMock(
        side_effect=[ProjectDTO.from_dict(legacy_payload), ProjectDTO.from_dict(tms3_project_payload)]
    )

    project.refetch_data()

    assert project.has_workflow
    assert not project.has_workflow_v3
    assert isinstance(project.workflow.get_stage(name="Agent"), AgentStage)
    with pytest.raises(EncordException, match="did not return the workflow_v3 contract"):
        _ = project.workflow_v3
    assert original_workflow.get_stage(name="EXTERNAL").id == UUID(int=4)

    project.refetch_data()

    assert not project.has_workflow
    assert project.has_workflow_v3
    assert project.workflow_v3.get_stage(name="EXTERNAL").id == UUID(int=4)
    with pytest.raises(WrongProjectTypeError, match="did not return the legacy workflow"):
        _ = project.workflow


@patch.object(EncordClientProject, "get_project_v2")
@patch.object(EncordUserClient, "get_ontology")
def test_user_client_get_project_constructs_tms3_graph(
    get_ontology: MagicMock,
    get_project_v2: MagicMock,
    user_client: EncordUserClient,
    tms3_project_payload: Dict[str, Any],
) -> None:
    get_project_v2.return_value = ProjectDTO.from_dict(tms3_project_payload)

    project = user_client.get_project(UUID(int=10000))

    assert project.workflow_v3.get_stage(name="EXTERNAL", type_=ExternalStage).id == UUID(int=4)
    get_ontology.assert_called_once_with(str(UUID(int=10001)))


@patch.object(ApiClient, "get_paged_iterator")
def test_user_client_list_projects_constructs_native_and_legacy_workflows_from_the_same_page(
    get_paged_iterator: MagicMock, user_client: EncordUserClient, tms3_project_payload: Dict[str, Any]
) -> None:
    tms3_project_payload["tmsVersion"] = "TMS4"
    tms3 = ProjectDTO.from_dict(tms3_project_payload)
    tms2_payload = deepcopy(tms3_project_payload)
    tms2_payload.pop("workflowV3")
    tms2_payload["tmsVersion"] = "TMS2"
    tms2 = ProjectDTO.from_dict(tms2_payload)
    tms2.workflow = WorkflowDTO.from_dict(
        {"stages": [{"uuid": str(UUID(int=2)), "stageType": "DONE", "title": "Final"}]}
    )
    get_paged_iterator.return_value = iter([tms3, tms2])

    tms3_project, tms2_project = list(user_client.list_projects())

    assert tms3_project.has_workflow_v3
    assert not tms3_project.has_workflow
    assert tms2_project.has_workflow
    assert not tms2_project.has_workflow_v3
    assert tms3_project.workflow_v3.get_stage(name="EXTERNAL").id == UUID(int=4)
    assert tms2_project.workflow.get_stage(name="Final").uuid == UUID(int=2)
    get_paged_iterator.assert_called_once()
