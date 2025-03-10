from typing import List, Sequence, Tuple

import numpy as np

# Importing python implementations of functions that not have numpy implementation
from .bitmask_operations import _rle_to_mask, _rle_to_string, _string_to_rle


def _mask_to_rle(mask: bytes) -> List[int]:
    """COCO-compatible raw bitmask to COCO-compatible RLE"""
    if len(mask) == 0:
        return []
    mask_buffer = np.frombuffer(mask, dtype=np.bool_)
    changes = np.diff(mask_buffer, prepend=mask_buffer[0], append=mask_buffer[-1])
    change_indices = np.flatnonzero(changes != 0)
    run_lengths = np.diff(np.concatenate(([0], change_indices, [len(mask_buffer)])))

    # note that the odd counts are always the numbers of zeros
    if mask_buffer[0] == True:
        run_lengths = np.concatenate(([0], run_lengths))

    return run_lengths.tolist()


def serialise_bitmask(bitmask: bytes) -> str:
    rle = _mask_to_rle(bitmask)
    return _rle_to_string(rle)


def deserialise_bitmask(serialised_bitmask: str, length: int) -> bytes:
    rle = _string_to_rle(serialised_bitmask)
    return _rle_to_mask(rle, length)


def transpose_bytearray(byte_data: bytes, shape: Tuple[int, int]) -> bytes:
    np_byte_data = np.frombuffer(byte_data, dtype=np.int8).reshape(shape)
    return bytearray(np_byte_data.T.tobytes())
