from typing import List, Optional
from uuid import UUID

from encord.orm.base_dto import BaseDTO


class CloudIntegration(BaseDTO):
    id: str
    title: str


class CloudIntegrationV2(BaseDTO):
    integration_uuid: UUID
    title: str


class GetCloudIntegrationsResponse(BaseDTO):
    result: List[CloudIntegrationV2]


class GetCloudIntegrationsParams(BaseDTO):
    filter_integration_uuids: Optional[List[UUID]] = None
    filter_integration_titles: Optional[List[str]] = None
    include_org_access: bool = False
