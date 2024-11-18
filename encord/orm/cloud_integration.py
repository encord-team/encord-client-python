from uuid import UUID

from encord.orm.base_dto import BaseDTO


class CloudIntegration(BaseDTO):
    id: str
    title: str


class CloudIntegrationV2(BaseDTO):
    integration_uuid: UUID
    title: str


class GetCloudIntegrationsResponse(BaseDTO):
    result: list[CloudIntegrationV2]
