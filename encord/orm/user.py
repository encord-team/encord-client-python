from encord.orm.base_dto import BaseDTO


class GetCurrentUserResponse(BaseDTO):
    user_hash: str
    user_email: str
