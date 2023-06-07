from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Sequence

from encord.exceptions import EncordException


def _string_to_rle(s: str) -> List[int]:
    """
    COCO-compatible string to RLE-encoded mask de-serialisation
    """
    cnts: List[int] = []
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
    rle_string = ""
    for i, x in enumerate(rle):
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
            rle_string += chr(c)

    return rle_string


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
    COCO-compatible raw bitmask to COCO-compatible RLE
    """
    rle_counts = []
    c = 0
    p = 0
    for mask_value in mask:
        if mask_value != p:
            rle_counts.append(c)
            c = 0
            p = mask_value
        c += 1

    rle_counts.append(c)
    return rle_counts


class BitmaskCoordinates:
    @dataclasses.dataclass(frozen=True)
    class EncodedBitmask:
        top: int
        left: int
        height: int
        width: int
        rle_string: str

    def __init__(self, source: Any):
        """
        Creates a BitmaskCoordinates object from a NumPy array, or other objects that implement
        :ref:`NumPy array interface <https://numpy.org/doc/stable/reference/arrays.interface.html>`

        For detailed information please refer to :ref:`bitmask tutorial <tutorials/bitmasks:Bitmasks>`
        """

        if isinstance(source, BitmaskCoordinates.EncodedBitmask):
            self._encoded_bitmask = source
        else:
            self._encoded_bitmask = BitmaskCoordinates._from_array(source)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> BitmaskCoordinates:
        bitmask = d["bitmask"]
        return BitmaskCoordinates(
            BitmaskCoordinates.EncodedBitmask(
                top=int(bitmask["top"]),
                left=int(bitmask["top"]),
                height=int(bitmask["height"]),
                width=int(bitmask["width"]),
                rle_string=bitmask["rleString"],
            )
        )

    @staticmethod
    def _from_array(source: Any) -> BitmaskCoordinates.EncodedBitmask:
        if source is not None:
            if hasattr(source, "__array_interface__"):
                arr = source.__array_interface__
                data_type = arr["typestr"]
                data = arr["data"]
                shape = arr["shape"]

                if data_type != "|b1":
                    raise EncordException(
                        "Bitmask should be an array of boolean values. " "For numpy array call .astype(bool)."
                    )

                raw_data = data if isinstance(data, bytes) else source.tobytes()

                rle = _mask_to_rle(raw_data)
                rle_string = _rle_to_string(rle)

                return BitmaskCoordinates.EncodedBitmask(
                    top=0, left=0, height=shape[0], width=shape[1], rle_string=rle_string
                )

        raise EncordException(f"Can't import bitmask from {source.__class__}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "top": self._encoded_bitmask.top,
            "left": self._encoded_bitmask.left,
            "width": self._encoded_bitmask.width,
            "height": self._encoded_bitmask.height,
            "rleString": self._encoded_bitmask.rle_string,
        }

    def to_numpy_array(self):
        """
        Converts the mask to numpy array with dtype bool.

        Numpy needs to be installed for this call to work
        """
        try:
            import numpy as np
        except ImportError:
            raise EncordException("Numpy is required for .to_numpy call.")

        return np.array(self)

    @property
    def __array_interface__(self):
        rle = _string_to_rle(self._encoded_bitmask.rle_string)
        data = _rle_to_mask(rle, self._encoded_bitmask.height * self._encoded_bitmask.width)
        return {
            "version": 3,
            "data": data,
            "shape": (self._encoded_bitmask.height, self._encoded_bitmask.width),
            "typestr": "|b1",
        }
