from collections import OrderedDict

from encord.orm import base_orm


class LabelingAlgorithm(base_orm.BaseORM):
    """
    Labeling algorithm base ORM.

    ORM:

    algorithm_name,
    algorithm_params

    """

    DB_FIELDS = OrderedDict(
        [
            ("algorithm_name", str),
            ("algorithm_parameters", dict),  # Algorithm params
        ]
    )


class ObjectInterpolationParams(base_orm.BaseORM):
    """
    Labeling algorithm parameters for interpolation algorithm

    ORM:

    key_frames,
    objects_to_interpolate

    """

    DB_FIELDS = OrderedDict(
        [
            ("key_frames", dict),
            ("objects_to_interpolate", list),
        ]
    )


class BoundingBoxFittingParams(base_orm.BaseORM):
    """
    Labeling algorithm parameters for bounding box fitting algorithm

    ORM:

    labels,
    video

    """

    DB_FIELDS = OrderedDict(
        [
            ("labels", dict),
            ("video", dict),
        ]
    )
