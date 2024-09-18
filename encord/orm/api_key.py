from encord.orm.base_dto import BaseDTO


class ApiKeyMeta(BaseDTO):
    """
    ApiKeyMeta contains key information.
    """

    title: str
    resource_type: str
