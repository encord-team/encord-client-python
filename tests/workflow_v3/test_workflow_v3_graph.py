from copy import deepcopy
from dataclasses import FrozenInstanceError
from typing import Any, Dict
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from encord.beta.workflow_v3 import (
    AnnotationStage,
    ArchiveStage,
    CollaboratorRouterStage,
    CompleteStage,
    ExternalStage,
    PathwayVerdict,
    PercentageRouterStage,
    ReviewStage,
    SkipStage,
    StageType,
    StartStage,
    UnknownStage,
    Workflow,
)
from encord.beta.workflow_v3.settings import PercentageRouterStageSettingsV1, UnknownStageSettings
from encord.exceptions import EncordException
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow_v3 import PercentageRouterStageDTO, WorkflowV3DTO


def _load_workflow(payload: Dict[str, Any]) -> Workflow:
    return Workflow(MagicMock(), UUID(int=10000), WorkflowV3DTO.from_dict(payload))


@pytest.mark.parametrize("stage_index", range(9))
def test_unfamiliar_settings_version_preserves_stage_type_identity_pathways_and_raw_configuration(
    workflow_v3_payload: Dict[str, Any], stage_index: int
) -> None:
    original = _load_workflow(workflow_v3_payload).stages[stage_index]
    raw_settings = {"version": 2, "futureOption": {"values": [1, 2]}}
    workflow_v3_payload["stages"][stage_index]["settings"] = raw_settings

    stage = _load_workflow(workflow_v3_payload).stages[stage_index]

    assert type(stage) is type(original)
    assert stage.id == original.id
    assert stage.pathways == original.pathways
    assert isinstance(stage.settings, UnknownStageSettings)
    assert stage.settings.version == 2
    assert stage.settings.to_dict() == raw_settings
    exported = stage.settings.to_dict()
    exported["futureOption"]["values"].append(3)
    assert stage.settings.to_dict() == raw_settings


@pytest.mark.parametrize("version", [None, 0, -1, "future"])
def test_missing_or_invalid_settings_version_is_rejected(workflow_v3_payload: Dict[str, Any], version: Any) -> None:
    raw_settings = {} if version is None else {"version": version}
    workflow_v3_payload["stages"][2]["settings"] = raw_settings

    with pytest.raises(EncordException):
        WorkflowV3DTO.from_dict(workflow_v3_payload)


@pytest.mark.parametrize("stage_index", range(9))
@pytest.mark.parametrize("by_alias", [False, True])
def test_unfamiliar_settings_versions_round_trip_without_wrapping_or_changing_their_raw_fields(
    workflow_v3_payload: Dict[str, Any], stage_index: int, by_alias: bool
) -> None:
    raw_settings = {"version": 2, "futureOption": {"values": [1, None]}, "values": {"version": 3}}
    workflow_v3_payload["stages"][stage_index]["settings"] = deepcopy(raw_settings)
    response = WorkflowV3DTO.from_dict(workflow_v3_payload)

    serialized = response.to_dict(by_alias=by_alias, exclude_none=False)
    restored = WorkflowV3DTO.from_dict(serialized)
    restored_json = WorkflowV3DTO.model_validate_json(response.model_dump_json(by_alias=by_alias))

    assert serialized["stages"][stage_index]["settings"] == raw_settings
    assert restored == response
    assert restored_json == response
    assert _load_workflow(serialized).stages[stage_index].settings.to_dict() == raw_settings


@pytest.mark.parametrize(
    "raw_settings",
    [
        {},
        {"ontologyScope": {"features": [{"schemaFeatureId": str(UUID(int=1)), "mode": "readOnly"}]}},
        {"reviewMode": {"mode": "PER_LABEL_AUTO_SUBMIT"}},
        {"autoSubmit": {"approvePathwayId": str(UUID(int=111)), "rejectPathwayId": None}},
        {"reviewMode": {"mode": "FUTURE_MODE"}, "ontologyScope": {"newOption": True}},
    ],
)
def test_manual_stages_ignore_unexposed_settings_and_do_not_require_them_for_graph_loading(
    workflow_v3_payload: Dict[str, Any], raw_settings: Dict[str, Any]
) -> None:
    workflow_v3_payload["stages"][1]["settings"] = {"version": 1, **deepcopy(raw_settings)}
    workflow_v3_payload["stages"][2]["settings"] = {"version": 1, **deepcopy(raw_settings)}

    response = WorkflowV3DTO.from_dict(workflow_v3_payload)
    workflow = Workflow(MagicMock(), UUID(int=10000), response)

    for name, stage_type in [("ANNOTATION", AnnotationStage), ("REVIEW", ReviewStage)]:
        stage = workflow.get_stage(name=name, type_=stage_type)
        assert stage.settings.to_dict() == {"version": 1}
        assert not isinstance(stage.settings, BaseDTO)
        assert not hasattr(stage.settings, "ontology_scope")
        assert not hasattr(stage.settings, "review_mode")
        assert not hasattr(stage.settings, "auto_submit")
    assert response.to_dict()["stages"][1]["settings"] == {"version": 1}
    assert response.to_dict()["stages"][2]["settings"] == {"version": 1}


def test_tms3_graph_constructs_all_stage_types_and_outgoing_pathways(workflow_v3_payload: Dict[str, Any]) -> None:
    workflow = _load_workflow(workflow_v3_payload)

    assert workflow.id == UUID(int=1000)
    assert tuple(type(stage) for stage in workflow.stages) == (
        StartStage,
        AnnotationStage,
        ReviewStage,
        ExternalStage,
        CompleteStage,
        ArchiveStage,
        SkipStage,
        PercentageRouterStage,
        CollaboratorRouterStage,
    )
    assert len(workflow.pathways) == 8
    external = workflow.get_stage(name="EXTERNAL", type_=ExternalStage)
    assert external.pathways[0].name == "next"
    assert external.pathways[0].source_stage_id == external.id
    assert external.pathways[0].destination_stage_id == UUID(int=5)
    assert external.pathways[0].verdict is PathwayVerdict.NEUTRAL
    assert workflow.get_stage(name="COMPLETE").pathways == ()


def test_tms3_graph_preserves_typed_empty_and_percentage_routing_settings(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow = _load_workflow(workflow_v3_payload)

    start = workflow.get_stage(name="START", type_=StartStage)
    annotation = workflow.get_stage(name="ANNOTATION", type_=AnnotationStage)
    percentage = workflow.get_stage(name="PERCENTAGE_ROUTER", type_=PercentageRouterStage)
    collaborator = workflow.get_stage(name="COLLABORATOR_ROUTER", type_=CollaboratorRouterStage)

    assert start.settings.to_dict() == {"version": 1}
    assert annotation.settings.to_dict() == {"version": 1}
    assert percentage.settings.pathway_probabilities == {UUID(int=105): 0.4, UUID(int=106): 0.6}
    assert collaborator.settings.to_dict() == {"version": 1}


def test_collaborator_router_exposes_outgoing_pathways_without_user_configuration(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow = _load_workflow(workflow_v3_payload)
    router = workflow.get_stage(name="COLLABORATOR_ROUTER", type_=CollaboratorRouterStage)

    assert {pathway.id for pathway in router.pathways} == {UUID(int=107), UUID(int=108)}
    assert {pathway.destination_stage_id for pathway in router.pathways} == {UUID(int=6), UUID(int=7)}
    assert router.settings.to_dict() == {"version": 1}


def test_tms3_settings_do_not_expose_engine_configuration_from_additional_response_fields(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow_v3_payload["stages"][0]["settings"] = {"version": 1, "paused": True, "inFlightCap": 4}
    workflow_v3_payload["stages"][1]["settings"]["queue"] = {"mode": "HOT", "claimN": 10}
    workflow_v3_payload["stages"][1]["settings"]["limitAllowedWorkers"] = {
        "userIds": ["worker-hash"],
        "groupIds": [str(UUID(int=7))],
    }
    workflow_v3_payload["stages"][8]["settings"] = {
        "version": 1,
        "routes": [{"pathwayUuid": str(UUID(int=107)), "userEmails": ["worker@example.com"], "groupUuids": []}],
        "defaultPathwayUuid": str(UUID(int=108)),
    }

    workflow = _load_workflow(workflow_v3_payload)
    start = workflow.get_stage(name="START", type_=StartStage)
    annotation = workflow.get_stage(name="ANNOTATION", type_=AnnotationStage)

    assert start.settings.to_dict() == {"version": 1}
    assert workflow.get_stage(name="COLLABORATOR_ROUTER", type_=CollaboratorRouterStage).settings.to_dict() == {
        "version": 1
    }
    assert not hasattr(start.settings, "paused")
    assert not hasattr(start.settings, "in_flight_cap")
    assert not hasattr(annotation.settings, "queue")
    assert not hasattr(annotation.settings, "limit_allowed_workers")
    assert annotation.settings.to_dict() == {"version": 1}


@pytest.mark.parametrize("selector", ["name", "id", "str_id"])
def test_tms3_stage_lookup_returns_the_loaded_stage_without_network_access(
    workflow_v3_payload: Dict[str, Any], selector: str
) -> None:
    workflow = _load_workflow(workflow_v3_payload)
    external = workflow.stages[3]
    args = (
        {"name": external.name} if selector == "name" else {"id": external.id if selector == "id" else str(external.id)}
    )

    result = workflow.get_stage(**args)

    assert result is external


@pytest.mark.parametrize("selectors", [{}, {"name": "EXTERNAL", "id": UUID(int=4)}])
def test_tms3_stage_lookup_requires_exactly_one_selector(
    workflow_v3_payload: Dict[str, Any], selectors: Dict[str, Any]
) -> None:
    workflow = _load_workflow(workflow_v3_payload)

    with pytest.raises(ValueError, match="exactly one"):
        workflow.get_stage(**selectors)


def test_tms3_stage_lookup_rejects_ambiguous_titles_even_with_type_hint(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow_v3_payload["stages"][4]["name"] = "EXTERNAL"
    workflow = _load_workflow(workflow_v3_payload)

    with pytest.raises(ValueError, match="Several stages"):
        workflow.get_stage(name="EXTERNAL", type_=ExternalStage)
    assert workflow.get_stage(id=UUID(int=4), type_=ExternalStage).id == UUID(int=4)


def test_tms3_stage_lookup_rejects_unmatched_title_id_and_wrong_type(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow = _load_workflow(workflow_v3_payload)

    with pytest.raises(ValueError, match="No matching stage"):
        workflow.get_stage(name="unknown")
    with pytest.raises(ValueError, match="No matching stage"):
        workflow.get_stage(id=uuid4())
    with pytest.raises(TypeError, match="Expected 'ReviewStage' but got 'ExternalStage'"):
        workflow.get_stage(name="EXTERNAL", type_=ReviewStage)


def test_tms3_stage_lookup_identifies_malformed_ids_and_ambiguous_stage_candidates(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow_v3_payload["stages"][4]["name"] = "EXTERNAL"
    workflow = _load_workflow(workflow_v3_payload)

    with pytest.raises(ValueError, match="Invalid stage ID: 'not-a-uuid'"):
        workflow.get_stage(id="not-a-uuid")
    with pytest.raises(ValueError) as error:
        workflow.get_stage(name="EXTERNAL")

    assert str(workflow.id) in str(error.value)
    assert str(UUID(int=4)) in str(error.value)
    assert str(UUID(int=5)) in str(error.value)


def test_router_probabilities_reject_mutation_and_remain_serializable(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow = _load_workflow(workflow_v3_payload)
    settings = workflow.get_stage(name="PERCENTAGE_ROUTER", type_=PercentageRouterStage).settings

    with pytest.raises(TypeError):
        settings.pathway_probabilities[UUID(int=105)] = 0.2
    with pytest.raises(TypeError):
        del settings.pathway_probabilities[UUID(int=105)]
    with pytest.raises(FrozenInstanceError):
        settings.pathway_probabilities = {}

    assert settings.pathway_probabilities == {UUID(int=105): 0.4, UUID(int=106): 0.6}
    assert settings.to_dict() == {
        "version": 1,
        "pathway_probabilities": {str(UUID(int=105)): 0.4, str(UUID(int=106)): 0.6},
    }


def test_router_probabilities_can_be_looked_up_by_each_outgoing_pathway_id(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    router = _load_workflow(workflow_v3_payload).get_stage(name="PERCENTAGE_ROUTER", type_=PercentageRouterStage)

    probabilities = [router.settings.pathway_probabilities[pathway.id] for pathway in router.pathways]

    assert probabilities == [0.4, 0.6]
    assert set(router.settings.pathway_probabilities) == {pathway.id for pathway in router.pathways}


def test_router_settings_own_their_mapping_and_can_be_deep_copied() -> None:
    values = {UUID(int=105): 0.4, UUID(int=106): 0.6}
    settings = PercentageRouterStageSettingsV1(values)

    copied = deepcopy(settings)
    values[UUID(int=105)] = 0.2

    assert settings.pathway_probabilities[UUID(int=105)] == 0.4
    assert copied.pathway_probabilities == settings.pathway_probabilities
    assert copied._probabilities is not settings._probabilities
    assert copied is not settings


def test_router_wire_settings_reject_invalid_pathway_ids(workflow_v3_payload: Dict[str, Any]) -> None:
    workflow_v3_payload["stages"][7]["settings"]["pathwayToPercentageMapping"] = {"not-a-uuid": 1.0}

    with pytest.raises(EncordException):
        WorkflowV3DTO.from_dict(workflow_v3_payload)


def test_tms3_graph_snapshot_fields_cannot_be_reassigned(workflow_v3_payload: Dict[str, Any]) -> None:
    workflow = _load_workflow(workflow_v3_payload)
    external = workflow.get_stage(name="EXTERNAL", type_=ExternalStage)

    with pytest.raises(FrozenInstanceError):
        external.name = "Changed"
    with pytest.raises(FrozenInstanceError):
        workflow.pathways[0].name = "Changed"
    with pytest.raises(FrozenInstanceError):
        workflow.get_stage(name="ANNOTATION", type_=AnnotationStage).settings = None


def test_tms3_graph_settings_do_not_share_mutable_configuration_with_the_response(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    response = WorkflowV3DTO.from_dict(workflow_v3_payload)
    workflow = Workflow(MagicMock(), UUID(int=10000), response)
    response_router = response.stages[7]
    assert isinstance(response_router, PercentageRouterStageDTO)

    workflow_v3_payload["stages"][7]["settings"]["pathwayToPercentageMapping"][str(UUID(int=105))] = 0.2
    response_router.settings.pathway_probabilities[UUID(int=105)] = 0.3

    router = workflow.get_stage(name="PERCENTAGE_ROUTER", type_=PercentageRouterStage)
    assert router.settings.pathway_probabilities[UUID(int=105)] == 0.4
    assert response_router.settings.pathway_probabilities[UUID(int=105)] == 0.3


def test_public_stages_are_constructed_with_shared_client_and_project_context(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    api_client = MagicMock()
    project_id = uuid4()
    response = WorkflowV3DTO.from_dict(workflow_v3_payload)

    workflow = Workflow(api_client, project_id, response)

    for stage in workflow.stages:
        assert stage._client is workflow._client
        assert stage._client.api_client is api_client
        assert stage._client.project_id == project_id
        assert not isinstance(stage, BaseDTO)
    assert all(isinstance(stage, BaseDTO) for stage in response.stages)
    api_client.get.assert_not_called()
    api_client.get_paged_iterator.assert_not_called()


def test_public_stage_representation_omits_transport_and_nested_configuration(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow = _load_workflow(workflow_v3_payload)
    stage = workflow.get_stage(name="ANNOTATION", type_=AnnotationStage)

    assert repr(stage) == f"AnnotationStage(id='{stage.id}', name='ANNOTATION')"


@pytest.mark.parametrize("field", ["stageType", "settings"])
def test_tms3_graph_rejects_a_stage_type_with_another_stage_settings(
    workflow_v3_payload: Dict[str, Any], field: str
) -> None:
    if field == "stageType":
        workflow_v3_payload["stages"][3]["stageType"] = "PERCENTAGE_ROUTER"
    else:
        workflow_v3_payload["stages"][7]["settings"] = {"version": 1, "unsupportedSetting": True}

    with pytest.raises(EncordException):
        WorkflowV3DTO.from_dict(workflow_v3_payload)


def test_unfamiliar_stages_remain_discoverable_with_identity_pathways_and_detached_settings(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow_v3_payload["stages"][3]["stageType"] = "SMART_REVIEW_ROUTER"
    workflow_v3_payload["stages"][3]["settings"] = {"newMode": {"values": [1, 2]}}

    response = WorkflowV3DTO.from_dict(workflow_v3_payload)
    workflow = Workflow(MagicMock(), UUID(int=10000), response)
    stage = workflow.get_stage(id=UUID(int=4), type_=UnknownStage)
    inspected_settings = stage.settings.to_dict()
    inspected_settings["newMode"]["values"].append(3)
    workflow_v3_payload["stages"][3]["settings"]["newMode"]["values"].append(4)

    assert stage is workflow.get_stage(name="EXTERNAL")
    assert stage.stage_type is StageType.UNKNOWN
    assert stage.raw_stage_type == "SMART_REVIEW_ROUTER"
    assert stage.id == UUID(int=4)
    assert stage.pathways[0].destination_stage_id == UUID(int=5)
    assert stage.settings.to_dict() == {"newMode": {"values": [1, 2]}}
    assert isinstance(workflow.get_stage(name="REVIEW"), ReviewStage)
    assert response.to_dict()["stages"][3]["stageType"] == "SMART_REVIEW_ROUTER"


@pytest.mark.parametrize("missing_field", ["id", "name", "stageType", "settings"])
def test_unfamiliar_stage_fallback_does_not_hide_missing_required_fields(
    workflow_v3_payload: Dict[str, Any], missing_field: str
) -> None:
    workflow_v3_payload["stages"][3]["stageType"] = "SMART_REVIEW_ROUTER"
    workflow_v3_payload["stages"][3].pop(missing_field)

    with pytest.raises(EncordException):
        WorkflowV3DTO.from_dict(workflow_v3_payload)


@pytest.mark.parametrize(
    "enum_type",
    [
        StageType,
        PathwayVerdict,
    ],
)
def test_unfamiliar_response_enum_values_use_unknown_instead_of_a_known_default(enum_type: Any) -> None:
    assert enum_type("FUTURE_VALUE") is enum_type.UNKNOWN


def test_unfamiliar_pathway_verdicts_do_not_break_graph_loading(workflow_v3_payload: Dict[str, Any]) -> None:
    workflow_v3_payload["pathways"][0]["verdict"] = "FUTURE_VERDICT"

    workflow = _load_workflow(workflow_v3_payload)

    assert workflow.pathways[0].verdict is PathwayVerdict.UNKNOWN
    assert workflow.get_stage(name="EXTERNAL", type_=ExternalStage).id == UUID(int=4)


@pytest.mark.parametrize("unknown_stage", [False, True])
def test_tms3_graph_serialization_round_trips_string_keyed_probabilities_and_stage_variants(
    workflow_v3_payload: Dict[str, Any], unknown_stage: bool
) -> None:
    if unknown_stage:
        workflow_v3_payload["stages"][3]["stageType"] = "FUTURE_STAGE"
    response = WorkflowV3DTO.from_dict(workflow_v3_payload)

    serialized = response.to_dict()
    restored = WorkflowV3DTO.from_dict(serialized)
    unaliased = response.to_dict(by_alias=False, exclude_none=False)

    router = response.stages[7]
    assert isinstance(router, PercentageRouterStageDTO)
    assert router.settings.pathway_probabilities == {UUID(int=105): 0.4, UUID(int=106): 0.6}
    assert serialized["stages"][7]["settings"]["pathwayToPercentageMapping"] == {
        str(UUID(int=105)): 0.4,
        str(UUID(int=106)): 0.6,
    }
    assert unaliased["stages"][7]["settings"]["pathway_probabilities"] == {
        str(UUID(int=105)): 0.4,
        str(UUID(int=106)): 0.6,
    }
    assert restored == response
    assert type(restored.stages[3]) is type(response.stages[3])
