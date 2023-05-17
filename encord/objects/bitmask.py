from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple

from encord.exceptions import EncordException


def _string_to_rle(s: str) -> List[int]:
    """
    COCO-compatible string to RLE-encoded mask de-serialisation
    """
    cnts = []
    p = 0

    while p < len(s):
        x = 0
        k = 0
        more = 1

        while more and p < len(s):
            c = ord(s[p]) - 48
            x |= (c & 0x1F) << (5 * k)
            more = c & 0x20
            p += 1
            k += 1

            if not more and (c & 0x10):
                x |= -1 << (5 * k)

        if len(cnts) > 2:
            x += cnts[-2]

        cnts.append(x)

    return cnts


def _rle_to_string(rle: Sequence[int]) -> str:
    """
    COCO-compatible RLE-encoded mask to string serialisation
    """
    s = ""
    for i in range(len(rle)):
        x = rle[i]

        if i > 2:
            x -= rle[i - 2]

        more = 1
        while more:
            c = x & 0x1F
            x >>= 5

            if c & 0x10:
                more = x != -1
            else:
                more = x != 0

            if more:
                c |= 0x20

            c += 48
            s += chr(c)

    return s


def _rle_to_mask(rle: List[int], size: int) -> bytes:
    """
    COCO-compatible RLE to bitmask
    """
    res = bytearray(size)
    offset = 0
    for i, c in enumerate(rle):
        v = i % 2
        while c > 0:
            res[offset] = v
            offset += 1
            c -= 1

    return bytes(res)


def _mask_to_rle(mask: bytes) -> List[int]:
    """
    COCO-compatible raw bitmask to RLE
    """
    cnts = []
    c = 0
    p = 0
    for j in range(len(mask)):
        if mask[j] != p:
            cnts.append(c)
            c = 0
            p = mask[j]
        c += 1

    cnts.append(c)
    return cnts


@dataclass(frozen=True)
class BitmaskCoordinates:
    shape: Tuple[int, int]
    _bitmask_str: str

    @staticmethod
    def from_dict(d: dict, shape: Tuple[int, int]) -> BitmaskCoordinates:
        return BitmaskCoordinates(_bitmask_str=d["bitmask"], shape=shape)

    @staticmethod
    def from_array(source: Any):
        if source is not None:
            if hasattr(source, "__array_interface__"):
                arr = source.__array_interface__
                d = ["data"]
                raw_data = d if isinstance(d, bytes) else source.tobytes()

                rle = _mask_to_rle(raw_data)
                rle_str = _rle_to_string(rle)

                return BitmaskCoordinates(_bitmask_str=rle_str, shape=arr["shape"])

        raise EncordException(f"Can't import bitmask from {source.__class__}")

    def to_encoded_string(self) -> str:
        return self._bitmask_str

    @property
    def __array_interface__(self):
        rle = _string_to_rle(self._bitmask_str)
        data = _rle_to_mask(rle, self.shape[0] * self.shape[1])
        return {
            "version": 3,
            "data": data,
            "shape": self.shape,
            "typestr": "|i1",
        }
