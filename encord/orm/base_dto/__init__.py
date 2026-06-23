import importlib.metadata as importlib_metadata

from encord.orm.base_dto.base_dto_interface import BaseDTOInterface as BaseDTOInterface

pydantic_version_str = importlib_metadata.version("pydantic")

pydantic_version = int(pydantic_version_str.split(".")[0])
if pydantic_version < 2:
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        BaseDTO as BaseDTO,
    )
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        BaseDTOWithExtra as BaseDTOWithExtra,
    )
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        Field as Field,
    )
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        GenericBaseDTO as GenericBaseDTO,
    )
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        PrivateAttr as PrivateAttr,
    )
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        RootModelDTO as RootModelDTO,
    )
    from encord.orm.base_dto.base_dto_pydantic_v1 import (
        dto_validator as dto_validator,
    )
else:
    from encord.orm.base_dto.base_dto_pydantic_v2 import (  # type: ignore[assignment]
        BaseDTO as BaseDTO,
    )
    from encord.orm.base_dto.base_dto_pydantic_v2 import (  # type: ignore[assignment]
        BaseDTOWithExtra as BaseDTOWithExtra,
    )
    from encord.orm.base_dto.base_dto_pydantic_v2 import (
        Field as Field,
    )
    from encord.orm.base_dto.base_dto_pydantic_v2 import (  # type: ignore[assignment]
        GenericBaseDTO as GenericBaseDTO,
    )
    from encord.orm.base_dto.base_dto_pydantic_v2 import (
        PrivateAttr as PrivateAttr,
    )
    from encord.orm.base_dto.base_dto_pydantic_v2 import (  # type: ignore[assignment]
        RootModelDTO as RootModelDTO,
    )
    from encord.orm.base_dto.base_dto_pydantic_v2 import (
        dto_validator as dto_validator,
    )
