try:
    from encord.common.bitmask_operations.bitmask_operations_numpy import (
        _mask_to_rle,
        _rle_to_mask,
        _rle_to_string,
        _string_to_rle,
        deserialise_bitmask,
        serialise_bitmask,
        transpose_bytearray,
    )
except ImportError:
    from encord.common.bitmask_operations.bitmask_operations import (
        _mask_to_rle,
        _rle_to_mask,
        _rle_to_string,
        _string_to_rle,
        deserialise_bitmask,
        serialise_bitmask,
        transpose_bytearray,
    )

from encord.common.bitmask_operations.bitmask_operations import coco_rle_to_encord_rle, encord_rle_to_coco_rle

__all__ = [
    "_mask_to_rle",
    "_rle_to_mask",
    "_rle_to_string",
    "_string_to_rle",
    "coco_rle_to_encord_rle",
    "deserialise_bitmask",
    "encord_rle_to_coco_rle",
    "serialise_bitmask",
    "transpose_bytearray",
]
