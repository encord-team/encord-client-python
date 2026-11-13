from types import MethodType
from typing import Any, Dict
from unittest.mock import MagicMock
from uuid import UUID

from encord.beta.workflow_v3 import Workflow
from encord.http.v2.api_client import ApiClient
from encord.orm.workflow_v3 import WorkflowV3DTO


def _workflow(payload: Dict[str, Any]):
    api = MagicMock(spec=ApiClient)
    api.get_paged_iterator = MethodType(ApiClient.get_paged_iterator, api)
    return Workflow(api, UUID(int=10000), WorkflowV3DTO.from_dict(payload)), api
