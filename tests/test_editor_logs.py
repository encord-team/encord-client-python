#!/usr/bin/env python3
"""
Test file for editor logs functionality.
Tests the get_editor_logs method in Project class with minimal mocking.
"""

from datetime import datetime, timedelta
from typing import Iterator
from unittest.mock import MagicMock
from uuid import uuid4

from encord.orm.editor_log import (
    ActionableWorkflowNodeType,
    EditorLog,
    EditorLogClassification,
    EditorLogGeneralAction,
    EditorLogObject,
    EditorLogParams,
    EditorLogsActionCategory,
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

    # Create a mock API client
    mock_api_client = MagicMock()
    # Mock the iterator behavior - get_paged_iterator should return an iterator
    mock_api_client.get_paged_iterator.return_value = iter([mock_editor_log])

    # Create a mock project instance
    test_project = MagicMock(spec=Project)
    test_project.project_hash = str(uuid4())
    test_project._api_client = mock_api_client
    test_project.get_editor_logs = Project.get_editor_logs.__get__(test_project, Project)

    # Call the method
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()

    result = test_project.get_editor_logs(start_time=start_time, end_time=end_time)

    # Verify the API client was called correctly
    mock_api_client.get_paged_iterator.assert_called_once()
    call_args = mock_api_client.get_paged_iterator.call_args

    assert call_args[0][0] == f"projects/{test_project.project_hash}/editor-logs"
    assert isinstance(call_args[1]["params"], EditorLogParams)
    assert call_args[1]["result_type"] == EditorLog

    # Verify the result
    assert isinstance(result, Iterator)
    results = []
    for item in result:
        results.append(item)
    assert len(results) == 1
    assert results[0].id == log_id
    assert results[0].action == "label_created"


def test_project_get_editor_logs_with_filters():
    """Test Project.get_editor_logs with filtering parameters."""

    # Create a mock API client
    mock_api_client = MagicMock()
    # Mock the iterator behavior - get_paged_iterator should return an iterator
    mock_api_client.get_paged_iterator.return_value = iter([])

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
        action="label_updated",
        actor_user_email="admin@example.com",
        workflow_stage_id=workflow_id,
        data_unit_id=data_unit_id,
    )

    # Verify the API client was called correctly
    mock_api_client.get_paged_iterator.assert_called_once()
    call_args = mock_api_client.get_paged_iterator.call_args

    assert call_args[0][0] == f"projects/{test_project.project_hash}/editor-logs"
    params = call_args[1]["params"]
    assert isinstance(params, EditorLogParams)
    assert params.start_time == start_time
    assert params.end_time == end_time
    assert params.action == "label_updated"
    assert params.actor_user_email == "admin@example.com"
    assert params.workflow_stage_id == workflow_id
    assert params.data_unit_id == data_unit_id

    # Verify the result
    assert isinstance(result, Iterator)
    results = []
    for item in result:
        results.append(item)
    assert len(results) == 0


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

    editor_logs_types_tuple = EditorLog.__args__
    # python3.9 cannot do isinstance with Union types directly

    # All should be valid EditorLog types
    assert isinstance(general_log, editor_logs_types_tuple)
    assert isinstance(object_log, editor_logs_types_tuple)
    assert isinstance(classification_log, editor_logs_types_tuple)

    # Create a mock API client
    mock_api_client = MagicMock()
    # Mock the iterator behavior - get_paged_iterator should return an iterator
    mock_api_client.get_paged_iterator.return_value = iter([general_log, object_log, classification_log])

    # Create a mock project instance
    test_project = MagicMock(spec=Project)
    test_project.project_hash = str(uuid4())
    test_project._api_client = mock_api_client
    test_project.get_editor_logs = Project.get_editor_logs.__get__(test_project, Project)

    # Call the method
    result = test_project.get_editor_logs(start_time=datetime.now() - timedelta(days=7), end_time=datetime.now())
    results = []
    for item in result:
        results.append(item)
    assert len(results) == 3
    assert all(isinstance(log, editor_logs_types_tuple) for log in results)
