from encord.orm.base_dto import BaseDTO


class BearerTokenResponse(BaseDTO):
    token: str
