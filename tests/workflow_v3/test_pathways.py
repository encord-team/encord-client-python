import json
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, is_dataclass
from typing import Any, Dict
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from encord.beta.workflow_v3 import Pathway, PathwayVerdict, Workflow
from encord.exceptions import EncordException
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow_v3 import WorkflowV3DTO


def test_public_pathways_are_frozen_dataclasses_shared_by_workflow_and_stage_views(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    response = WorkflowV3DTO.from_dict(workflow_v3_payload)

    workflow = Workflow(MagicMock(), UUID(int=10000), response)

    assert tuple(pathway.id for pathway in workflow.pathways) == tuple(pathway.id for pathway in response.pathways)
    for index, pathway in enumerate(workflow.pathways):
        assert is_dataclass(pathway)
        assert not isinstance(pathway, BaseDTO)
        assert not hasattr(pathway, "model_dump")
        assert pathway is not response.pathways[index]
        assert any(pathway is outgoing for outgoing in workflow.get_stage(id=pathway.source_stage_id).pathways)
        assert copy(pathway) == deepcopy(pathway) == pathway
        with pytest.raises(FrozenInstanceError):
            setattr(pathway, "name", "Changed")


def test_pathway_exports_detached_json_safe_sdk_fields() -> None:
    pathway = Pathway(
        id=UUID(int=1),
        source_stage_id=UUID(int=2),
        destination_stage_id=UUID(int=3),
        verdict=PathwayVerdict.NEUTRAL,
    )

    exported = pathway.to_dict()
    exported["name"] = "Changed"

    assert pathway.to_dict() == {
        "id": str(UUID(int=1)),
        "name": None,
        "source_stage_id": str(UUID(int=2)),
        "destination_stage_id": str(UUID(int=3)),
        "verdict": "neutral",
    }
    assert json.loads(json.dumps(pathway.to_dict())) == pathway.to_dict()


@pytest.mark.parametrize(
    ("wire_value", "verdict"),
    [("accept", PathwayVerdict.ACCEPT), ("reject", PathwayVerdict.REJECT), ("neutral", PathwayVerdict.NEUTRAL)],
)
def test_internal_pathway_dtos_retain_backend_wire_names_and_round_trip_without_public_models(
    workflow_v3_payload: Dict[str, Any],
    wire_value: str,
    verdict: PathwayVerdict,
) -> None:
    workflow_v3_payload["pathways"][0]["verdict"] = wire_value
    response = WorkflowV3DTO.from_dict(workflow_v3_payload)

    serialized = response.to_dict(exclude_none=False)
    restored = WorkflowV3DTO.from_dict(serialized)

    assert serialized["pathways"] == workflow_v3_payload["pathways"]
    assert restored == response
    assert response.pathways[0].verdict is verdict
    assert all(isinstance(pathway, BaseDTO) for pathway in response.pathways)


@pytest.mark.parametrize("field", ["id", "sourceStageId", "destinationStageId", "verdict"])
def test_internal_pathway_validation_rejects_missing_required_fields(
    workflow_v3_payload: Dict[str, Any],
    field: str,
) -> None:
    workflow_v3_payload["pathways"][0].pop(field)

    with pytest.raises(EncordException):
        WorkflowV3DTO.from_dict(workflow_v3_payload)


@pytest.mark.parametrize("field", ["id", "sourceStageId", "destinationStageId"])
def test_internal_pathway_validation_rejects_invalid_identifiers(
    workflow_v3_payload: Dict[str, Any],
    field: str,
) -> None:
    workflow_v3_payload["pathways"][0][field] = "not-a-uuid"

    with pytest.raises(EncordException):
        WorkflowV3DTO.from_dict(workflow_v3_payload)


def test_unfamiliar_pathway_verdict_remains_an_explicit_unknown_value_in_public_exports(
    workflow_v3_payload: Dict[str, Any],
) -> None:
    workflow_v3_payload["pathways"][0]["verdict"] = "FUTURE_VERDICT"

    pathway = Workflow(MagicMock(), UUID(int=10000), WorkflowV3DTO.from_dict(workflow_v3_payload)).pathways[0]

    assert pathway.verdict is PathwayVerdict.UNKNOWN
    assert pathway.to_dict()["verdict"] == PathwayVerdict.UNKNOWN.value
