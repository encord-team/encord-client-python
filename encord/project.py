"""---
title: "Project"
slug: "sdk-ref-project"
hidden: false
metadata:
  title: "Project"
  description: "Encord SDK Project class"
category: "64e481b57b6027003f20aaa0"
---
"""

import datetime
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union
from uuid import UUID

from encord.client import EncordClientProject
from encord.collection import ProjectCollection
from encord.common.deprecated import deprecated
from encord.common.utils import ensure_list, ensure_uuid_list
from encord.filter_preset import ProjectFilterPreset
from encord.http.bundle import Bundle
from encord.http.v2.api_client import ApiClient
from encord.objects import LabelRowV2, OntologyStructure
from encord.ontology import Ontology
from encord.orm.active import ActiveProjectMode
from encord.orm.analytics import (
    CollaboratorTimer,
    CollaboratorTimerParams,
    CollaboratorTimersGroupBy,
    TimeSpent,
    TimeSpentParams,
)
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.collection import ProjectCollectionType
from encord.orm.dataset import Image, Video
from encord.orm.filter_preset import ActiveFilterPresetDefinition
from encord.orm.group import ProjectGroup
from encord.orm.label_log import LabelLog
from encord.orm.label_row import (
    AnnotationTaskStatus,
    LabelRow,
    LabelRowMetadata,
    LabelStatus,
    ShadowDataState,
)
from encord.orm.project import (
    CopyDatasetOptions,
    CopyLabelsOptions,
    ProjectDataset,
    ProjectDTO,
    ProjectStatus,
    ProjectType,
)
from encord.orm.project import Project as OrmProject
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.project_ontology.ontology import Ontology as LegacyOntology
from encord.utilities.coco.datastructure import CategoryID, FrameIndex, ImageID
from encord.utilities.hash_utilities import convert_to_uuid
from encord.utilities.project_user import ProjectUser, ProjectUserRole
from encord.workflow import Workflow


class Project:
    """Access project related data and manipulate the project."""

    def __init__(
        self,
        client: EncordClientProject,
        project_instance: ProjectDTO,
        ontology: Optional[Ontology],
        api_client: ApiClient,
    ):
        self._client = client
        self._project_instance = project_instance
        self._ontology_internal = ontology
        self._api_client = api_client

        if project_instance.workflow:
            self._workflow = Workflow(api_client, project_instance.project_hash, project_instance.workflow)

    @property
    def project_hash(self) -> str:
        """Get the project hash (i.e. the Project ID)."""
        # Keeping the interface backward compatible, so converting UUID to str for now
        return str(self._project_instance.project_hash)

    @property
    def status(self) -> ProjectStatus:
        """Get the status of the project."""
        return self._project_instance.status

    @property
    def title(self) -> str:
        """Get the title of the project."""
        return self._project_instance.title

    @property
    def description(self) -> str:
        """Get the description of the project."""
        return self._project_instance.description

    @property
    def created_at(self) -> datetime.datetime:
        """Get the time the project was created at."""
        return self._project_instance.created_at

    @property
    def last_edited_at(self) -> datetime.datetime:
        """Get the time the project was last edited at."""
        return self._project_instance.last_edited_at

    @property
    @deprecated(version="0.1.95", alternative=".ontology_structure")
    def ontology(self) -> Dict[str, Any]:
        """Get the ontology of the project.

        DEPRECATED: Prefer using the :meth:`encord.Project.ontology_structure` method.
        This method returns the same structure as :meth:`encord.Project.ontology_structure`, just in
        raw python dictionary format.
        """
        return self._ontology.structure.to_dict()

    @property
    def ontology_hash(self) -> str:
        """Get the ontology hash of the project's ontology."""
        return self._project_instance.ontology_hash

    @property
    def ontology_structure(self) -> OntologyStructure:
        """Get the ontology structure of the project's ontology."""
        return self._ontology.structure

    @property
    def user_role(self) -> Optional[ProjectUserRole]:
        """Get the current user's role in the project.

        This may return `None` if the user is an organisational admin and has accessed the project e.g. using
        `include_org_access=True` of :meth:`encord.user_client.UserClient.list_projects`.
        """
        return self._project_instance.user_role

    @property
    def source_projects(self) -> Optional[List[str]]:
        """Get the source projects for a Training project. Returns None for non-Training projects."""
        return self._project_instance.source_projects

    @property
    @deprecated(version="0.1.117", alternative=".list_datasets")
    def datasets(self) -> List[Dict[str, Any]]:
        """DEPRECATED: Prefer using the :meth:`encord.project.list_datasets` class to work with the data.

        Get the info about datasets associated with this project.
        """
        return [project_dataset.to_dict(by_alias=False) for project_dataset in self.list_datasets()]

    @property
    def project_type(self) -> ProjectType:
        """Get the project type."""
        return self._project_instance.project_type

    @property
    @deprecated(version="0.1.104", alternative=".list_label_rows_v2")
    def label_rows(self) -> dict:
        """Get the label rows.
        DEPRECATED: Prefer using :meth:`list_label_rows_v2()` method and :meth:`LabelRowV2` class to work with the data.

        .. code::

            from encord.orm.label_row import LabelRowMetadata

            project = user_client.get_project("[project_hash]")

            label_rows = LabelRowMetadata.from_list(project.label_rows)

        """
        return self._client.get_project(include_labels_metadata=True).label_rows

    def refetch_data(self) -> None:
        """The Project class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        self._project_instance = self._client.get_project_v2()

    def refetch_ontology(self) -> None:
        """Update the ontology for the project to reflect changes on the backend."""
        self._ontology.refetch_data()

    def get_project(self) -> OrmProject:
        """This function is exposed for convenience. You are encouraged to use the property accessors instead."""
        return self._client.get_project()

    @property
    def workflow(self) -> Workflow:
        """Get the workflow of the project.

        Available only for workflow projects.
        """
        assert (
            self.project_type == ProjectType.WORKFLOW
        ), "project.workflow property only available for workflow projects"
        return self._workflow

    @property
    def _ontology(self) -> Ontology:
        if self._ontology_internal is None:
            self._ontology_internal = Ontology(
                Ontology._fetch_ontology(self._api_client, self.ontology_hash), self._api_client
            )  # lazy loading
        return self._ontology_internal

    def list_label_rows_v2(
        self,
        data_hashes: Optional[Union[List[str], List[UUID]]] = None,
        label_hashes: Optional[Union[List[str], List[UUID]]] = None,
        edited_before: Optional[Union[str, datetime.datetime]] = None,
        edited_after: Optional[Union[str, datetime.datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
        shadow_data_state: Optional[ShadowDataState] = None,
        data_title_eq: Optional[str] = None,
        data_title_like: Optional[str] = None,
        workflow_graph_node_title_eq: Optional[str] = None,
        workflow_graph_node_title_like: Optional[str] = None,
        include_workflow_graph_node: bool = True,
        include_client_metadata: bool = False,
        include_images_data: bool = False,
        include_all_label_branches: bool = False,
        branch_name: Optional[str] = None,
    ) -> List[LabelRowV2]:
        """List label rows with various filtering options.

        Args:
            data_hashes: List of data hashes to filter by.
            label_hashes: List of label hashes to filter by.
            edited_before: Optionally filter to only rows last edited before the specified time.
            edited_after: Optionally filter to only rows last edited after the specified time.
            label_statuses: Optionally filter to only those label rows that have one of the specified :class:`~encord.orm.label_row.AnnotationTaskStatus`es.
            shadow_data_state: Optionally filter by data type in Benchmark QA projects. See :class:`~encord.orm.label_row.ShadowDataState`.
            data_title_eq: Optionally filter by exact title match.
            data_title_like: Optionally filter by fuzzy title match; SQL syntax.
            workflow_graph_node_title_eq: Optionally filter by exact match with workflow node title.
            workflow_graph_node_title_like: Optionally filter by fuzzy match with workflow node title; SQL syntax.
            include_workflow_graph_node: Include workflow graph node metadata in all the results. True by default.
            include_client_metadata: Optionally include client metadata into the result of this query.
            include_images_data: Optionally include image group metadata into the result of this query.
            include_all_label_branches: Optionally include all label branches. They will be included as separate label row objects.
            branch_name: Optionally specify a branch name. A branch name cannot be specified if include_all_label_branches is set to True

        Returns:
            A list of :class:`~encord.objects.LabelRowV2` instances for all the matching label rows.
        """
        label_row_metadatas = self._client.list_label_rows(
            edited_before,
            edited_after,
            label_statuses,
            shadow_data_state,
            data_hashes=data_hashes,
            label_hashes=label_hashes,
            include_uninitialised_labels=True,
            data_title_eq=data_title_eq,
            data_title_like=data_title_like,
            workflow_graph_node_title_eq=workflow_graph_node_title_eq,
            workflow_graph_node_title_like=workflow_graph_node_title_like,
            include_workflow_graph_node=include_workflow_graph_node,
            include_client_metadata=include_client_metadata,
            include_images_data=include_images_data,
            include_all_label_branches=include_all_label_branches,
            branch_name=branch_name,
        )
        label_rows = [
            LabelRowV2(label_row_metadata, self._client, self._ontology) for label_row_metadata in label_row_metadatas
        ]
        return label_rows

    def add_users(self, user_emails: List[str], user_role: ProjectUserRole) -> List[ProjectUser]:
        """Add users to the project.

        If the user already exists in the Project, this operation succeeds but the `user_role` remains unchanged. The
        existing `user_role` is reflected in the `ProjectUser` instance returned.

        Args:
            user_emails: List of user emails to be added.
            user_role: The user role to assign to all users.

        Returns:
            List[ProjectUser]: A list of ProjectUser objects representing the added users.

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while adding the users to the project.
        """
        return self._client.add_users(user_emails, user_role)

    def list_groups(self) -> Iterable[ProjectGroup]:
        """List all groups that have access to a particular project.

        Returns:
            Iterable[ProjectGroup]: An iterable of ProjectGroup objects.
        """
        project_hash = convert_to_uuid(self.project_hash)
        page = self._client.list_groups(project_hash)
        yield from page.results

    def add_group(self, group_hash: Union[List[UUID], UUID], user_role: ProjectUserRole):
        """Add a group to the project.

        Args:
            group_hash: List of group hashes or a single group hash to be added.
            user_role: User role that the group will be given.

        Returns:
            None
        """
        project_hash = convert_to_uuid(self.project_hash)
        if isinstance(group_hash, UUID):
            group_hash = [group_hash]
        self._client.add_groups(project_hash, group_hash, user_role)

    def remove_group(self, group_hash: Union[List[UUID], UUID]):
        """Remove a group from the project.

        Args:
            group_hash: List of group hashes or a single group hash to be removed.

        Returns:
            None
        """
        if isinstance(group_hash, UUID):
            group_hash = [group_hash]
        self._client.remove_groups(group_hash)

    def copy_project(
        self,
        copy_datasets: Union[bool, CopyDatasetOptions] = False,
        copy_collaborators=False,
        copy_models=False,
        *,
        copy_labels: Optional[CopyLabelsOptions] = None,
        new_title: Optional[str] = None,
        new_description: Optional[str] = None,
    ) -> str:
        """Copy the current project into a new one with copied contents including settings, datasets, and users.
        Labels and models are optional.

        Args:
            copy_datasets: If True, the datasets of the existing project are copied over, and new tasks are created from those datasets.
            copy_collaborators: If True, all users of the existing project are copied over with their current roles.
                                If label and/or annotator reviewer mapping is set, this will also be copied over.
            copy_models: If True, all models with their training information will be copied into the new project.
            copy_labels: Options for copying labels, defined in `CopyLabelsOptions`.
            new_title: When provided, will be used as the title for the new project.
            new_description: When provided, will be used as the description for the new project.

        Returns:
            str: The EntityId of the newly created project.

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while copying the project.
        """
        return self._client.copy_project(
            new_title=new_title,
            new_description=new_description,
            copy_datasets=copy_datasets,
            copy_collaborators=copy_collaborators,
            copy_models=copy_models,
            copy_labels=copy_labels,
        )

    def add_datasets(self, dataset_hashes: List[str]) -> bool:
        """Add datasets to the project.

        Args:
            dataset_hashes: List of dataset hashes of the datasets to be added.

        Returns:
            bool: True if the datasets were successfully added, False otherwise.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If one or more datasets don't exist by the specified dataset_hashes.
            UnknownError: If an error occurs while adding the datasets to the project.
            OperationNotAllowed: If the write operation is not allowed by the API key.
        """
        res = self._client.add_datasets(dataset_hashes)
        self.refetch_data()
        return res

    def remove_datasets(self, dataset_hashes: List[str]) -> bool:
        """Remove datasets from the project.

        Args:
            dataset_hashes: List of dataset hashes of the datasets to be removed.

        Returns:
            bool: True if the datasets were successfully removed, False otherwise.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no dataset exists by the specified dataset_hash (uid).
            UnknownError: If an error occurs while removing the datasets from the project.
            OperationNotAllowed: If the operation is not allowed by the API key.
        """
        res = self._client.remove_datasets(dataset_hashes)
        self.refetch_data()
        return res

    @deprecated(version="0.1.95", alternative=".ontology_structure")
    def get_project_ontology(self) -> LegacyOntology:
        """DEPRECATED: Prefer using the `ontology_structure` property accessor instead.

        Returns:
            LegacyOntology: The project's ontology.
        """
        return self._client.get_project_ontology()

    @deprecated("0.1.102", alternative="encord.ontology.Ontology class")
    def add_object(self, name: str, shape: ObjectShape) -> bool:
        """DEPRECATED: Prefer using :class:`Ontology [encord.ontology.Ontology]` to manipulate ontology.

        Add an object to an ontology.

        ATTENTION: This legacy method will affect all the projects sharing the same ontology.

        Args:
            name: The name of the object.
            shape: The shape of the object. (BOUNDING_BOX, POLYGON, POLYLINE, or KEY_POINT)

        Returns:
            bool: True if the object was added successfully, False otherwise.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while adding the object to the project ontology.
            OperationNotAllowed: If the operation is not allowed by the API key.
            ValueError: If invalid arguments are supplied in the function call.
        """
        res = self._client.add_object(name, shape)
        self.refetch_ontology()
        return res

    @deprecated("0.1.102", alternative="encord.ontology.Ontology class")
    def add_classification(
        self,
        name: str,
        classification_type: ClassificationType,
        required: bool,
        options: Optional[Iterable[str]] = None,
    ):
        """DEPRECATED: Prefer using :class:`Ontology encord.ontology.Ontology` to manipulate ontology.

        Add a classification to an ontology.

        ATTENTION: This legacy method will affect all the projects sharing the same ontology.

        Args:
            name: The name of the classification.
            classification_type: The classification type (RADIO, TEXT, or CHECKLIST).
            required: Whether this classification is required by the annotator.
            options: The list of options for the classification (to be set to None for texts).

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while adding the classification to the project ontology.
            OperationNotAllowed: If the operation is not allowed by the API key.
            ValueError: If invalid arguments are supplied in the function call.
        """
        res = self._client.add_classification(name, classification_type, required, options)
        self.refetch_ontology()
        return res

    def object_interpolation(
        self,
        key_frames,
        objects_to_interpolate,
    ):
        """Run object interpolation algorithm on project labels (requires an editor ontology and feature uids).

        Interpolation is supported for bounding box, polygon, and keypoint.

        Args:
            key_frames: Labels for frames to be interpolated. Key frames are consumed in the form::

            ```python
                {
                    "[frame_number]": {
                        "objects": [
                            {
                                "objectHash": "[object_hash]",
                                "featureHash": "[feature_hash]",
                                "polygon": {
                                    "0": { "x": x1, "y": y1, },
                                    "1": { "x": x2, "y": y2, },
                                    # ...,
                                }
                            },
                            # ...
                        ]
                    },
                    # ...,
                }
            ```

            objects_to_interpolate: List of object uids (hashes) of objects to interpolate.

        Returns:
            dict: Full set of filled frames including interpolated objects.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while running interpolation.
        """
        return self._client.object_interpolation(key_frames, objects_to_interpolate)

    def get_data(self, data_hash: str, get_signed_url: bool = False) -> Tuple[Optional[Video], Optional[List[Image]]]:
        """Retrieve information about a video or image group.

        Args:
            data_hash: The uid of the data object.
            get_signed_url: Optionally return signed URLs for timed public access to that resource (default False).

        Returns:
            A tuple consisting of the video (if it exists) and a list of individual images (if they exist).

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while retrieving the object.
        """
        return self._client.get_data(data_hash, get_signed_url)

    def get_label_logs(
        self,
        user_hash: Optional[str] = None,
        data_hash: Optional[str] = None,
        from_unix_seconds: Optional[int] = None,
        to_unix_seconds: Optional[int] = None,
        after: Optional[datetime.datetime] = None,
        before: Optional[datetime.datetime] = None,
        user_email: Optional[str] = None,
    ) -> List[LabelLog]:
        """Get label logs, which represent the actions taken in the UI to create labels.

        All arguments can be left as `None` if no filtering should be applied.

        Args:
            user_hash: Filter the label logs by the user.
            data_hash: Filter the label logs by the data_hash.
            from_unix_seconds: Filter the label logs to only include labels after this timestamp. **Deprecated**: use parameter **after** instead.
            to_unix_seconds: Filter the label logs to only include labels before this timestamp. **Deprecated**: use parameter **before** instead.
            after: Filter the label logs to only include labels after the specified time.
            before: Filter the label logs to only include labels before the specified time.
            user_email: Filter by the annotator email.

        Returns:
            List of label logs.
        """
        return self._client.get_label_logs(
            user_hash,
            data_hash,
            from_unix_seconds,
            to_unix_seconds,
            after,
            before,
            user_email,
        )

    @deprecated(version="0.1.154", alternative="EncordUserClient.get_cloud_integrations")
    def get_cloud_integrations(self) -> List[CloudIntegration]:
        """Get the list of cloud integrations.

        Returns:
            List of CloudIntegration objects.
        """
        return self._client.get_cloud_integrations()

    @deprecated(version="0.1.104", alternative=".list_label_rows_v2")
    def list_label_rows(
        self,
        edited_before: Optional[Union[str, datetime.datetime]] = None,
        edited_after: Optional[Union[str, datetime.datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
        shadow_data_state: Optional[ShadowDataState] = None,
        *,
        include_uninitialised_labels=False,
        label_hashes: Optional[List[str]] = None,
        data_hashes: Optional[List[str]] = None,
    ) -> List[LabelRowMetadata]:
        """DEPRECATED - use `list_label_rows_v2` to manage label rows instead.

        Args:
            edited_before: Optionally filter to only rows last edited before the specified time.
            edited_after: Optionally filter to only rows last edited after the specified time.
            label_statuses: Optionally filter to only those label rows that have one of the specified AnnotationTaskStatus.
            shadow_data_state: Optionally filter by data type in Benchmark QA projects. See ShadowDataState.
            include_uninitialised_labels: Whether to return only label rows that are "created" and have a label_hash (default).
                If set to `True`, this will return all label rows, including those that do not have a label_hash.
            data_hashes: List of data hashes to filter by.
            label_hashes: List of label hashes to filter by.

        Returns:
            A list of LabelRowMetadata instances for all the matching label rows.

        Raises:
            UnknownError: If an error occurs while retrieving the data.
        """
        return self._client.list_label_rows(
            edited_before,
            edited_after,
            label_statuses,
            shadow_data_state,
            include_uninitialised_labels=include_uninitialised_labels,
            label_hashes=label_hashes,
            data_hashes=data_hashes,
        )

    @deprecated(version="0.1.123", alternative=".list_label_rows_v2")
    def get_label_row(
        self,
        uid: str,
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
    ) -> LabelRow:
        """DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Retrieve label row. If you need to retrieve multiple label rows, prefer using get_label_rows instead.

        Args:
            uid: A label_hash (uid) string.
            get_signed_url: Whether to generate signed urls to the data asset. Generating these should be disabled if the signed urls are not used to speed up the request.
            include_object_feature_hashes: If None all the objects will be included. Otherwise, only objects labels will be included of which the feature_hash has been added.
            include_classification_feature_hashes: If None all the classifications will be included. Otherwise, only classification labels will be included of which the feature_hash has been added.
            include_reviews: Whether to request read only information about the reviews of the label row.

        Returns:
            LabelRow: A label row instance.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while retrieving the label.
            OperationNotAllowed: If the read operation is not allowed by the API key.
        """
        return self._client.get_label_row(
            uid,
            get_signed_url,
            include_object_feature_hashes=include_object_feature_hashes,
            include_classification_feature_hashes=include_classification_feature_hashes,
            include_reviews=include_reviews,
        )

    @deprecated(version="0.1.123", alternative=".list_label_rows_v2")
    def get_label_rows(
        self,
        uids: List[str],
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
    ) -> List[LabelRow]:
        """DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Retrieve a list of label rows. Duplicates will be dropped. The result will come back in a random order.

        Args:
            uids: A list of label_hash (uid).
            get_signed_url: Whether to generate signed urls to the data asset. Generating these should be disabled if the signed urls are not used to speed up the request.
            include_object_feature_hashes: If None all the objects will be included. Otherwise, only objects labels will be included of which the feature_hash has been added.
            include_classification_feature_hashes: If None all the classifications will be included. Otherwise, only classification labels will be included of which the feature_hash has been added.
            include_reviews: Whether to request read only information about the reviews of the label row.

        Returns:
            List of LabelRow instances.

        Raises:
            MultiLabelLimitError: If too many labels were requested. Check the error's maximum_labels_allowed field to read the most up to date error limit.
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while retrieving the label.
            OperationNotAllowed: If the read operation is not allowed by the API key.
        """
        return self._client.get_label_rows(
            uids,
            get_signed_url,
            include_object_feature_hashes=include_object_feature_hashes,
            include_classification_feature_hashes=include_classification_feature_hashes,
            include_reviews=include_reviews,
        )

    @deprecated(version="0.1.123", alternative=".list_label_rows_v2")
    def save_label_row(self, uid, label, validate_before_saving: bool = False):
        """DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Save an existing label row.

        If you have a series of frame labels and have not updated answer
        dictionaries, call the construct_answer_dictionaries utility function
        to do so prior to saving labels.

        Args:
            uid: A label_hash (uid) string.
            label: A label row instance.
            validate_before_saving: Enable stricter server-side integrity checks. Boolean, `False` by default.

        Returns:
            bool: True if the label row is successfully saved, False otherwise.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while saving the label.
            OperationNotAllowed: If the write operation is not allowed by the API key.
            AnswerDictionaryError: If an object or classification instance is missing in answer dictionaries.
            CorruptedLabelError: If a blurb is corrupted (e.g., if the frame labels have more frames than the video).
        """
        return self._client.save_label_row(uid, label, validate_before_saving)

    @deprecated(version="0.1.123", alternative=".list_label_rows_v2")
    def create_label_row(self, uid: str):
        """DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Create a label row (for data in a project not previously labeled).

        Args:
            uid: The data_hash (uid) of the data unit being labeled.
                Available in client.get_project().get('label_rows')
                where label_status is NOT_LABELLED.

        Returns:
            LabelRow: A label row instance.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while saving the label.
            OperationNotAllowed: If the write operation is not allowed by the API key.
            AnswerDictionaryError: If an object or classification instance is missing in answer dictionaries.
            CorruptedLabelError: If a blurb is corrupted (e.g., if the frame labels have more frames than the video).
            ResourceExistsError: If a label row already exists for this project data. Avoids overriding existing work.
        """
        return self._client.create_label_row(uid)

    def create_bundle(self, bundle_size: Optional[int] = None) -> Bundle:
        """Initializes a bundle to reduce the number of network calls performed by the Encord SDK.

        See the :class:`encord.http.bundle.Bundle` documentation for more details.

        Args:
            bundle_size: maximum number of items bundled. If more actions provided to the bundle, they will be
                automatically split into separate api calls.

        Returns:
            Bundle: An instance of the Bundle class.
        """
        return Bundle(bundle_size=bundle_size)

    @deprecated(version="0.1.157", alternative=".list_time_spent")
    def list_collaborator_timers(
        self,
        after: datetime.datetime,
        before: Optional[datetime.datetime] = None,
        group_by_data_unit: bool = True,
    ) -> Iterable[CollaboratorTimer]:
        """**DEPRECATED** - Use `list_time_spent`. `list_time_spent` provides more comprehensive and accurate information.

        Provides information about time spent by each collaborator who has worked on the project within a specified range of dates.

        This endpoint is deprecated and retrieves collaborator timers from the Legacy Performance Dashboards, not the Upgraded Analytics Dashboard.

        Args:
            after: The beginning of the period of interest.
            before: The end of the period of interest.
            group_by_data_unit: If True, time spent by a collaborator for each data unit is provided separately.
                                If False, all time spent in the scope of the project is aggregated together.

        Yields:
            CollaboratorTimer: Information about the time spent by each collaborator.
        """
        params = CollaboratorTimerParams(
            project_hash=self.project_hash,
            after=after,
            before=before,
            group_by=(CollaboratorTimersGroupBy.DATA_UNIT if group_by_data_unit else CollaboratorTimersGroupBy.PROJECT),
            page_size=100,
        )

        yield from self._client.get_collaborator_timers(params)

    def list_time_spent(
        self,
        start: datetime.datetime,
        end: Optional[datetime.datetime] = None,
        workflow_stage_uuid: Union[List[UUID], List[str], UUID, str, None] = None,
        user_email: Union[List[str], str, None] = None,
    ) -> Iterable[TimeSpent]:
        """
        Get time spent by collaborators on a task per day. If a task spans multiple days, the time spent on each day will be returned separately.

        Args:
            start: The beginning of the period of interest.
            end: The end of the period of interest.
            workflow_stage_uuid: The UUID or list of UUIDs of the workflow stages of interest.
            user_email: The email or list of emails of the users of interest.

        Returns:
            Iterable[TimeSpent]: Information about the time spent by a collaborator on a task per day.
        """
        params = TimeSpentParams(
            project_uuid=self.project_hash,
            after=start,
            before=end,
            workflow_stage_uuids=ensure_uuid_list(workflow_stage_uuid),
            user_emails=ensure_list(user_email),
        )

        yield from self._client.get_time_spent(params)

    def list_datasets(self) -> Iterable[ProjectDataset]:
        """List all datasets associated with the project.

        Returns:
            Iterable[ProjectDataset]: An iterable of ProjectDataset instances.
        """
        return self._client.list_project_datasets(self._project_instance.project_hash)

    def import_coco_labels(
        self,
        labels_dict: Dict[str, Any],
        category_id_to_feature_hash: Dict[CategoryID, str],
        image_id_to_frame_index: Dict[ImageID, FrameIndex],
        branch_name: Optional[str] = None,
        confidence_field_name: Optional[str] = None,
    ) -> None:
        """Import labels in COCO format to an Encord Project.

        Args:
            labels_dict (Dict[str, Any]): A dictionary in COCO annotation format.
            category_id_to_feature_hash (Dict[CategoryID, str]): A mapping of category IDs from the COCO data to their corresponding feature hashes in the Project's Ontology.
            image_id_to_frame_index (Dict[ImageID, FrameIndex]): A mapping of image IDs to FrameIndex(data_hash, frame_offset), used to locate the corresponding frames in the Encord Project.
            branch_name (Optional[str]): Optionally specify a branch name. Defaults to the `main` branch.
            confidence_field_name (Optional[str]): Optionally specify the name of the confidence field in the COCO annotations. Defaults to assigning `1.0` as confidence value to all annotations.
        """
        from encord.utilities.coco.datastructure import CocoRootModel
        from encord.utilities.coco.importer import import_coco_labels

        coco = CocoRootModel.from_dict(labels_dict)
        import_coco_labels(
            self,
            coco,
            category_id_to_feature_hash,
            image_id_to_frame_index,
            branch_name=branch_name,
            confidence_field_name=confidence_field_name,
        )

    def export_coco_labels(
        self,
        label_hashes: Optional[List[str]] = None,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        branch_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export labels from the project to the COCO format.
        This method requires the 'coco' extra to be installed. Install it using:
        `pip install encord[coco]`.

        Args:
            label_hashes: List of label hashes to include. If not provided, all label rows will be included.
            include_object_feature_hashes: If `None`, all objects will be included.
                 Otherwise, only objects with the specified feature hashes will be included.
            include_classification_feature_hashes: If `None`, all classifications will be included.
                Otherwise, only classifications with the specified feature hashes will be included.
            branch_name: Optionally specify a branch name. Defaults to the `main` branch.

        Returns:
            Dict[str, Any]: A dictionary in the COCO format containing the exported labels,
                including annotations and metadata conforming to COCO standards.
                The dictionary also includes additional fields specific to Encord,
                providing supplementary information not defined in the COCO standard.

        Raises:
            ImportError: If the 'coco' extra dependencies are not installed.
        """
        from encord.utilities.coco.exporter import CocoExporter

        label_rows = self.list_label_rows_v2(label_hashes=label_hashes, branch_name=branch_name)
        with self.create_bundle() as bundle:
            for row in label_rows:
                row.initialise_labels(
                    include_object_feature_hashes=include_object_feature_hashes,
                    include_classification_feature_hashes=include_classification_feature_hashes,
                    bundle=bundle,
                )
        labels = [row.to_encord_dict() for row in label_rows]
        coco_labels = CocoExporter(labels, ontology=self.ontology_structure).export()
        return coco_labels

    def get_collection(self, collection_uuid: Union[str, UUID]) -> ProjectCollection:
        return ProjectCollection._get_collection(
            project_client=self._client,
            ontology=self._ontology,
            project_uuid=self._project_instance.project_hash,
            collection_uuid=UUID(collection_uuid) if isinstance(collection_uuid, str) else collection_uuid,
        )

    def list_collections(
        self,
        collection_uuids: Optional[List[Union[str, UUID]]] = None,
        page_size: Optional[int] = None,
    ) -> Iterator[ProjectCollection]:
        """List all collections associated to the project.

        Args:
            collection_uuids: The unique identifiers (UUIDs) of the collections to retrieve.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            The list of collections which match the given criteria.

        Raises:
            ValueError: If any of the collection uuids is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        collections = (
            [UUID(collection) if isinstance(collection, str) else collection for collection in collection_uuids]
            if collection_uuids is not None
            else None
        )
        return ProjectCollection._list_collections(
            project_client=self._client,
            ontology=self._ontology,
            project_uuid=self._project_instance.project_hash,
            collection_uuids=collections,
            page_size=page_size,
        )

    def delete_collection(self, collection_uuid: Union[str, UUID]) -> None:
        """Delete a project collection by its UUID if it exists.

        Args:
            collection_uuid: The unique identifier (UUID) of the collection to delete.

        Returns:
            None
        Raises:
            ValueError: If `collection_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(collection_uuid, str):
            collection_uuid = UUID(collection_uuid)
        ProjectCollection._delete_collection(
            self._client._api_client, self._project_instance.project_hash, collection_uuid
        )

    def create_collection(
        self, name: str, description: str = "", collection_type: ProjectCollectionType = ProjectCollectionType.FRAME
    ) -> ProjectCollection:
        """Create a project collection.

        Args:
            name: The name of the collection.
            description: The description of the collection.
            collection_type: The type of the collection, could be either frame or label.

        Returns:
            ProjectCollection: Newly created collection.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to the folder.
        """
        new_uuid = ProjectCollection._create_collection(
            self._client._api_client, self._project_instance.project_hash, name, description, collection_type
        )
        return self.get_collection(new_uuid)

    def active_sync(self) -> None:
        """Sync the associated Active project"""
        self._client.active_sync()

    def active_import(self, project_mode: ActiveProjectMode, *, video_sampling_rate: Optional[float] = None) -> None:
        """Import the associated Active project. Progress in the app
        Args:
            project_mode: Active projects can be imported up to a certain stage. Use the ActiveProjectModeEnum to select the stage
            video_sampling_rate: Optional[float]: For videos, what's the sampling rate of frames for analysis
        Returns:
            None
        """
        self._client.active_import(project_mode, video_sampling_rate)

    def list_filter_presets(
        self,
        filter_preset_uuids: Optional[List[Union[str, UUID]]] = None,
        page_size: Optional[int] = None,
    ) -> Iterator[ProjectFilterPreset]:
        """List all filter presets associated to the project.

        Args:
            filter_preset_uuids: The unique identifiers (UUIDs) of the filter presets to retrieve.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            The list of filter presets which match the given criteria.

        Raises:
            ValueError: If any of the filter preset uuids is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        filter_presets = (
            [
                UUID(filter_preset) if isinstance(filter_preset, str) else filter_preset
                for filter_preset in filter_preset_uuids
            ]
            if filter_preset_uuids is not None
            else None
        )
        return ProjectFilterPreset._list_filter_presets(
            client=self._client._api_client,
            project_uuid=self._project_instance.project_hash,
            filter_preset_uuids=filter_presets,
            page_size=page_size,
        )

    def get_filter_preset(self, filter_preset_uuid: Union[str, UUID]) -> ProjectFilterPreset:
        return ProjectFilterPreset._get_filter_preset(
            client=self._client._api_client,
            project_uuid=self._project_instance.project_hash,
            filter_preset_uuid=UUID(filter_preset_uuid) if isinstance(filter_preset_uuid, str) else filter_preset_uuid,
        )

    def delete_filter_preset(self, filter_preset_uuid: Union[str, UUID]) -> None:
        ProjectFilterPreset._delete_filter_preset(
            client=self._client._api_client,
            project_uuid=self._project_instance.project_hash,
            filter_preset_uuid=UUID(filter_preset_uuid) if isinstance(filter_preset_uuid, str) else filter_preset_uuid,
        )

    def create_filter_preset(self, name: str, filter_preset: ActiveFilterPresetDefinition) -> ProjectFilterPreset:
        uuid = ProjectFilterPreset._create_filter_preset(
            client=self._client._api_client,
            project_uuid=self._project_instance.project_hash,
            name=name,
            filter_preset=filter_preset,
        )
        return ProjectFilterPreset._get_filter_preset(
            client=self._client._api_client,
            project_uuid=self._project_instance.project_hash,
            filter_preset_uuid=uuid,
        )

    def set_status(self, status: ProjectStatus):
        """Set the status of the project.

        Args:
            status: The new status of the project.
        """
        self._client.set_status(status)
