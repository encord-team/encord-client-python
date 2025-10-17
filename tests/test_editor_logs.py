#!/usr/bin/env python3
"""
Test file for editor logs functionality.
Tests the get_editor_logs method in Project class with minimal mocking.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from encord.http.v2.payloads import Page
from encord.orm.editor_log import (
    ActionableWorkflowNodeType,
    EditorLog,
    EditorLogClassification,
    EditorLogGeneralAction,
    EditorLogObject,
    EditorLogParams,
    EditorLogsActionCategory,
    EditorLogsResponse,
)
from encord.project import Project


def test_project_get_editor_logs_basic():
    """Test Project.get_editor_logs with basic parameters."""
    # Mock the API response
    log_id = uuid4()
    project_id = uuid4()
    data_unit_id = uuid4()
    workflow_stage_id = uuid4()
    workflow_task_id = uuid4()
    session_id = uuid4()
    ontology_id = uuid4()

    mock_editor_log = EditorLogGeneralAction(
        id=log_id,
        action="label_created",
        action_category=EditorLogsActionCategory.EDITOR,
        data_unit_id=data_unit_id,
        workflow_stage_id=workflow_stage_id,
        branch_name="main",
        workflow_task_id=workflow_task_id,
        timestamp=datetime.now(),
        session_id=session_id,
        actor_user_id="user123",
        actor_organisation_id=1,
        actor_user_email="test@example.com",
        project_id=project_id,
        project_organisation_id=1,
        project_user_role="admin",
        project_organisation_user_role="admin",
        data_unit_title="Test Data Unit",
        data_unit_data_type="image",
        data_unit_dataset_id=uuid4(),
        data_unit_dataset_title="Test Dataset",
        ontology_id=ontology_id,
        label_id="label123",
        workflow_stage_type=ActionableWorkflowNodeType.ANNOTATION,
        workflow_stage_title="Annotation Stage",
        event_information={"key": "value"},
    )

    mock_response = EditorLogsResponse(results=[mock_editor_log], next_page_token=None)

    # Create a mock API client
    mock_api_client = MagicMock()
    mock_api_client.get.return_value = mock_response

    # Create a mock project instance
    test_project = MagicMock(spec=Project)
    test_project.project_hash = str(uuid4())
    test_project._api_client = mock_api_client
    test_project.get_editor_logs = Project.get_editor_logs.__get__(test_project, Project)

    # Call the method
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()

    result = test_project.get_editor_logs(start_time=start_time, end_time=end_time, limit=100)

    # Verify the API client was called correctly
    mock_api_client.get.assert_called_once()
    call_args = mock_api_client.get.call_args

    assert (call_args[0][0], f"projects/{test_project.project_hash}/editor-logs")
    assert isinstance(call_args[1]["params"], EditorLogParams)
    assert (call_args[1]["result_type"], EditorLogsResponse)

    # Verify the result
    assert isinstance(result, Page)
    assert (len(result.results), 1)
    assert (result.results[0].id, log_id)
    assert (result.results[0].action, "label_created")
    assert result.next_page_token is None


def test_project_get_editor_logs_with_filters():
    """Test Project.get_editor_logs with filtering parameters."""
    # Mock the API response
    mock_response = EditorLogsResponse(results=[], next_page_token="next_token_123")

    # Create a mock API client
    mock_api_client = MagicMock()
    mock_api_client.get.return_value = mock_response

    # Create a mock project instance
    test_project = MagicMock(spec=Project)
    test_project.project_hash = str(uuid4())
    test_project._api_client = mock_api_client
    test_project.get_editor_logs = Project.get_editor_logs.__get__(test_project, Project)

    # Call the method with filters
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()
    workflow_id = uuid4()
    data_unit_id = uuid4()

    result = test_project.get_editor_logs(
        start_time=start_time,
        end_time=end_time,
        limit=50,
        page_token="test_token",
        action="label_updated",
        actor_user_email="admin@example.com",
        workflow_stage_id=workflow_id,
        data_unit_id=data_unit_id,
    )

    # Verify the API client was called correctly
    mock_api_client.get.assert_called_once()
    call_args = mock_api_client.get.call_args

    assert call_args[0][0] == f"projects/{test_project.project_hash}/editor-logs"
    params = call_args[1]["params"]
    assert isinstance(params, EditorLogParams)
    assert params.start_time == start_time
    assert params.end_time == end_time
    assert params.limit == 50
    assert params.page_token == "test_token"
    assert params.action == "label_updated"
    assert params.actor_user_email == "admin@example.com"
    assert params.workflow_stage_id == workflow_id
    assert params.data_unit_id == data_unit_id

    # Verify the result
    assert isinstance(result, Page)
    assert len(result.results) == 0
    assert result.next_page_token == "next_token_123"


def test_project_get_editor_logs_multiple_types():
    """Test that EditorLog union type works correctly."""
    log_id = uuid4()
    project_id = uuid4()
    data_unit_id = uuid4()
    workflow_stage_id = uuid4()
    workflow_task_id = uuid4()
    session_id = uuid4()
    ontology_id = uuid4()

    # Test EditorLogGeneralAction
    general_log = EditorLogGeneralAction(
        id=log_id,
        action="label_created",
        action_category=EditorLogsActionCategory.EDITOR,
        data_unit_id=data_unit_id,
        workflow_stage_id=workflow_stage_id,
        branch_name="main",
        workflow_task_id=workflow_task_id,
        timestamp=datetime.now(),
        session_id=session_id,
        actor_user_id="user123",
        actor_organisation_id=1,
        actor_user_email="test@example.com",
        project_id=project_id,
        project_organisation_id=1,
        project_user_role="admin",
        project_organisation_user_role="admin",
        data_unit_title="Test Data Unit",
        data_unit_data_type="image",
        data_unit_dataset_id=uuid4(),
        data_unit_dataset_title="Test Dataset",
        ontology_id=ontology_id,
        label_id="label123",
        workflow_stage_type=ActionableWorkflowNodeType.ANNOTATION,
        workflow_stage_title="Annotation Stage",
        event_information={"key": "value"},
    )

    # Test EditorLogObject
    object_log = EditorLogObject(
        id=log_id,
        action="object_created",
        action_category=EditorLogsActionCategory.OBJECT,
        data_unit_id=data_unit_id,
        workflow_stage_id=workflow_stage_id,
        branch_name="main",
        workflow_task_id=workflow_task_id,
        timestamp=datetime.now(),
        session_id=session_id,
        actor_user_id="user123",
        actor_organisation_id=1,
        actor_user_email="test@example.com",
        project_id=project_id,
        project_organisation_id=1,
        project_user_role="admin",
        project_organisation_user_role="admin",
        data_unit_title="Test Data Unit",
        data_unit_data_type="image",
        data_unit_dataset_id=uuid4(),
        data_unit_dataset_title="Test Dataset",
        ontology_id=ontology_id,
        label_id="label123",
        workflow_stage_type=ActionableWorkflowNodeType.ANNOTATION,
        workflow_stage_title="Annotation Stage",
        event_information={"key": "value"},
        label_name="Test Label",
        feature_id="feature123",
        label_ranges=[(0, 10)],
        object_shape="polygon",
        object_current_frame=5,
        object_hash="object_hash_123",
        object_id=1,
    )

    # Test EditorLogClassification
    classification_log = EditorLogClassification(
        id=log_id,
        action="classification_created",
        action_category=EditorLogsActionCategory.CLASSIFICATION,
        data_unit_id=data_unit_id,
        workflow_stage_id=workflow_stage_id,
        branch_name="main",
        workflow_task_id=workflow_task_id,
        timestamp=datetime.now(),
        session_id=session_id,
        actor_user_id="user123",
        actor_organisation_id=1,
        actor_user_email="test@example.com",
        project_id=project_id,
        project_organisation_id=1,
        project_user_role="admin",
        project_organisation_user_role="admin",
        data_unit_title="Test Data Unit",
        data_unit_data_type="image",
        data_unit_dataset_id=uuid4(),
        data_unit_dataset_title="Test Dataset",
        ontology_id=ontology_id,
        label_id="label123",
        workflow_stage_type=ActionableWorkflowNodeType.ANNOTATION,
        workflow_stage_title="Annotation Stage",
        event_information={"key": "value"},
        label_name="Test Classification",
        feature_id="feature123",
        label_ranges=[(0, 10)],
        classification_hash="classification_hash_123",
    )

    # All should be valid EditorLog types
    assert isinstance(general_log, EditorLog)
    assert isinstance(object_log, EditorLog)
    assert isinstance(classification_log, EditorLog)

    # Mock the API response
    mock_response = EditorLogsResponse(results=[general_log, object_log, classification_log], next_page_token=None)

    # Create a mock API client
    mock_api_client = MagicMock()
    mock_api_client.get.return_value = mock_response

    # Create a mock project instance
    test_project = MagicMock(spec=Project)
    test_project.project_hash = str(uuid4())
    test_project._api_client = mock_api_client
    test_project.get_editor_logs = Project.get_editor_logs.__get__(test_project, Project)

    # Call the method
    result = test_project.get_editor_logs(
        start_time=datetime.now() - timedelta(days=7), end_time=datetime.now(), limit=100
    )
    assert len(result.results) == 3
    assert (all(isinstance(log, EditorLog) for log in result.results)) == True
