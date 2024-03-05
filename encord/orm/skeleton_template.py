from typing import List

from encord.orm.base_dto import BaseDTO


class SkeletonTemplateORM(BaseDTO):
    id: int  # pk, autoincr
    feature_node_hash: str
    user_hash: str
    name: str
    template: dict  # serv_def='{}'::jsonb


class SkeletonTemplatesORM(BaseDTO):
    templates: List[SkeletonTemplateORM]
