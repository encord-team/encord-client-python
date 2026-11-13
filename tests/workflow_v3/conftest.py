from copy import deepcopy
from typing import Any, Dict
from uuid import UUID

import pytest


@pytest.fixture
def workflow_v3_payload() -> Dict[str, Any]:
    manual = {
        "ontologyScope": {"features": [{"schemaFeatureId": str(UUID(int=60)), "mode": "readOnly"}]},
    }
    settings = [
        ("START", {}),
        ("ANNOTATION", manual),
        ("REVIEW", {**deepcopy(manual), "reviewMode": {"mode": "PER_LABEL"}}),
        ("EXTERNAL", {}),
        ("COMPLETE", {}),
        ("ARCHIVE", {}),
        ("SKIP", {}),
        ("PERCENTAGE_ROUTER", {"pathwayToPercentageMapping": {str(UUID(int=105)): 0.4, str(UUID(int=106)): 0.6}}),
        ("COLLABORATOR_ROUTER", {}),
    ]
    connections = [(1, 2), (2, 3), (3, 4), (4, 5), (8, 6), (8, 7), (9, 6), (9, 7)]
    return {
        "id": str(UUID(int=1000)),
        "stages": [
            {
                "id": str(UUID(int=index)),
                "name": stage_type,
                "stageType": stage_type,
                "settings": {"version": 1, **config},
            }
            for index, (stage_type, config) in enumerate(settings, start=1)
        ],
        "pathways": [
            {
                "id": str(UUID(int=index)),
                "name": "next" if source == 4 else None,
                "sourceStageId": str(UUID(int=source)),
                "destinationStageId": str(UUID(int=destination)),
                "verdict": "neutral",
            }
            for index, (source, destination) in enumerate(connections, start=101)
        ],
    }


@pytest.fixture
def tms3_project_payload(workflow_v3_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "projectHash": str(UUID(int=10000)),
        "projectType": "workflow",
        "status": "inProgress",
        "title": "TMS3 workflow project",
        "description": "",
        "createdAt": "2026-10-22T10:00:00Z",
        "creatorEmail": "creator@example.com",
        "lastEditedAt": "2026-10-22T10:00:00Z",
        "ontologyHash": str(UUID(int=10001)),
        "editorOntology": {},
        "workflowManagerUuid": None,
        "workflow": None,
        "workflowV3": workflow_v3_payload,
    }


@pytest.fixture
def task_payload() -> Dict[str, Any]:
    return {
        "id": str(UUID(int=200)),
        "stageId": str(UUID(int=4)),
        "stageType": "EXTERNAL",
        "target": {
            "id": str(UUID(int=300)),
            "projectId": str(UUID(int=10000)),
            "datasetId": "dataset-hash",
            "dataId": "data-hash",
            "targetType": "data_unit",
            "createdAt": "2026-10-23T10:00:00Z",
            "deletedAt": None,
        },
        "status": "entered",
        "priority": 0.5,
        "createdAt": "2026-10-23T10:00:00Z",
        "enteredAt": "2026-10-23T10:00:01Z",
        "processingAt": None,
        "doneAt": None,
        "cancelledAt": None,
        "assignment": {
            "assignedTo": "user-hash",
            "assignedBy": "manager-hash",
            "assignedAt": "2026-10-23T10:00:02Z",
        },
    }
