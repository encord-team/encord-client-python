import pydantic

pydantic_version = int(pydantic.__version__.split(".")[0])
if pydantic_version < 2:
    from encord.orm.base_dto.base_dto_pydantic_v1 import BaseDTO, GenericBaseDTO
else:
    from encord.orm.base_dto.base_dto_pydantic_v2 import BaseDTO, GenericBaseDTO
