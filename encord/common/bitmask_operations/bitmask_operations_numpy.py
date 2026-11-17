from typing import List, Tuple

import numpy as np

# Importing python implementations of functions that not have numpy implementation
from .bitmask_operations import (
    _rle_to_string,
    _string_to_rle,
)


def _rle_to_mask(rle: List[int], size: int) -> bytes:
    """Encord-compatible RLE to bitmask"""
    counts = np.asarray(rle, dtype=np.int64)
    if np.any(counts < 0):
        # The pure Python version treats a negative run as empty
        counts = np.maximum(counts, 0)
    total = int(counts.sum())
    if total > size:
        raise IndexError(f"RLE covers {total} values but the mask size is {size}")
    # Even runs are zeros, odd runs are ones
    values = np.arange(len(counts), dtype=np.uint8) % 2
    mask = np.zeros(size, dtype=np.uint8)
    mask[:total] = np.repeat(values, counts)
    return mask.tobytes()


def _mask_to_rle(mask: bytes) -> List[int]:
    """Encord-compatible raw bitmask to Encord-compatible RLE"""
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
