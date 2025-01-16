"""---
title: "Objects - Bitmask"
slug: "sdk-ref-objects-bitmask"
hidden: false
metadata:
  title: "Objects - Bitmask"
  description: "Encord SDK Objects - Bitmask class."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Union, runtime_checkable

from encord.common.bitmask_operations import deserialise_bitmask, serialise_bitmask
from encord.exceptions import EncordException
from encord.orm.base_dto import BaseDTO


@runtime_checkable
class ArrayProtocol(Protocol):
    """Protocol for any object implementing
    :ref:`NumPy array interface <https://numpy.org/doc/stable/reference/arrays.interface.html>`
    """

    @property
    def __array_interface__(self) -> Dict[str, Any]: ...

    def tobytes(self) -> bytes: ...


class BitmaskCoordinates:
    class EncodedBitmask(BaseDTO):
        top: int
        left: int
        height: int
        width: int
        rle_string: str

        @staticmethod
        def try_from_dict(d: Dict[str, Any]) -> Optional[BitmaskCoordinates.EncodedBitmask]:
            try:
                return BitmaskCoordinates.EncodedBitmask.from_dict(d)
            except EncordException:
                return None

    def __init__(self, source: Union[ArrayProtocol, BitmaskCoordinates.EncodedBitmask, Dict[str, Any]]):
        """Creates a BitmaskCoordinates object from a NumPy array, or other objects that implement
        :ref:`NumPy array interface <https://numpy.org/doc/stable/reference/arrays.interface.html>`,
        such as Pillow images.

        For detailed information please refer to :ref:`bitmask tutorial <tutorials/bitmasks:Bitmasks>`
        """
        if isinstance(source, BitmaskCoordinates.EncodedBitmask):
            self._encoded_bitmask = source
        elif isinstance(source, ArrayProtocol):
            self._encoded_bitmask = BitmaskCoordinates._from_array(source)
        elif bitmask := BitmaskCoordinates.EncodedBitmask.try_from_dict(source):
            self._encoded_bitmask = bitmask
        else:
            raise ValueError(f"Failed to create BitmaskCoordinates from an object of type {type(source)}")

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> BitmaskCoordinates:
        """This method is used to construct object from Encord bitmask dictionary format.
        In most cases external users don't need it. Please consider just passing bitmask numpy array compatible object
        to the BitmaskCoordinates constructor.
        """
        bitmask = d.get("bitmask") or d  # Backward compatibility
        return BitmaskCoordinates(BitmaskCoordinates.EncodedBitmask.from_dict(bitmask))

    @staticmethod
    def _from_array(source: ArrayProtocol) -> BitmaskCoordinates.EncodedBitmask:
        if source is None:
            raise EncordException("Bitmask can't be created from None")

        if not hasattr(source, "__array_interface__"):
            raise EncordException(f"Can't import bitmask from {source.__class__}")

        arr = source.__array_interface__
        data_type = arr["typestr"]
        data = arr["data"]
        shape = arr["shape"]

        if len(shape) != 2:
            raise EncordException("Bitmask should be a 2-dimensional array.")

        if data_type != "|b1":
            raise EncordException("Bitmask should be an array of boolean values. For numpy array call .astype(bool).")

        raw_data = data if isinstance(data, bytes) else source.tobytes()

        rle_string = serialise_bitmask(raw_data)

        return BitmaskCoordinates.EncodedBitmask(top=0, left=0, height=shape[0], width=shape[1], rle_string=rle_string)

    def to_dict(self) -> Dict[str, Any]:
        """This method is used to serialise the object to Encord bitmask dictionary format.
        In most cases external users don't need it. Please consider using .to_numpy_array method, or just pass this
        BitmaskCoordinates objects to a constructor of any class that supports numpy array protocol,
        such as NumPy array, Pillow image, etc.
        """
        return self._encoded_bitmask.to_dict()

    def to_numpy_array(self):
        """Converts the mask to a 2D numpy array with dtype bool.

        Numpy needs to be installed for this call to work.
        """
        try:
            import numpy as np  # type: ignore[missing-import]
        except ImportError as e:
            raise EncordException("Numpy is required for .to_numpy_array call.") from e

        return np.array(self)

    @property
    def __array_interface__(self):
        data = deserialise_bitmask(
            self._encoded_bitmask.rle_string, self._encoded_bitmask.height * self._encoded_bitmask.width
        )
        return {
            "version": 3,
            "data": data,
            "shape": (self._encoded_bitmask.height, self._encoded_bitmask.width),
            "typestr": "|b1",
        }
