from itertools import groupby
from typing import TYPE_CHECKING, List, Optional, Sequence, Set, Tuple

from encord.exceptions import LabelRowError
from encord.objects.common import Shape
from encord.objects.frames import Ranges, frames_to_ranges

if TYPE_CHECKING:
    from encord.objects.bitmask import BitmaskCoordinates
    from encord.objects.ontology_object_instance import ObjectInstance


def _string_to_rle(mask_string: str) -> List[int]:
    """Encord-compatible string to RLE-encoded mask de-serialisation"""
    cnts: List[int] = []
    p = 0

    while p < len(mask_string):
        x = 0
        k = 0
        more = 1

        while more and p < len(mask_string):
            c = ord(mask_string[p]) - 48
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
    """Encord-compatible RLE-encoded mask to string serialization"""
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


def _mask_to_rle(mask: bytes) -> List[int]:
    """Encord-compatible raw bitmask to Encord-compatible RLE"""
    if len(mask) == 0:
        return []
    raw_rle = [len(list(group)) for _, group in groupby(mask)]
    # note that the odd counts are always the numbers of zeros
    if mask[0] == 1:
        raw_rle.insert(0, 0)
    return raw_rle


def _rle_to_mask(rle: List[int], size: int) -> bytes:
    """Encord-compatible RLE to bitmask"""
    res = bytearray(size)
    offset = 0

    for i, c in enumerate(rle):
        v = i % 2
        while c > 0:
            res[offset] = v
            offset += 1
            c -= 1

    return bytes(res)


def serialise_bitmask(bitmask: bytes) -> str:
    rle = _mask_to_rle(bitmask)
    return _rle_to_string(rle)


def deserialise_bitmask(serialised_bitmask: str, length: int) -> bytes:
    rle = _string_to_rle(serialised_bitmask)
    return _rle_to_mask(rle, length)


def encord_rle_to_coco_rle(encord_rle_string: str, *, height: int, width: int) -> str:
    """Convert an Encord-compatible RLE string to a COCO-compatible RLE counts string.

    Encord bitmasks are encoded from row-major mask data. COCO RLE counts are encoded
    from column-major mask data, as produced by pycocotools.
    """
    row_major_mask = deserialise_bitmask(encord_rle_string, height * width)
    column_major_mask = transpose_bytearray(row_major_mask, shape=(height, width))
    return serialise_bitmask(column_major_mask)


def coco_rle_to_encord_rle(coco_rle_string: str, *, height: int, width: int) -> str:
    """Convert a COCO-compatible RLE counts string to an Encord-compatible RLE string.

    COCO RLE counts are encoded from column-major mask data, as produced by
    pycocotools. Encord bitmasks are encoded from row-major mask data.
    """
    column_major_mask = deserialise_bitmask(coco_rle_string, height * width)
    row_major_mask = transpose_bytearray(column_major_mask, shape=(width, height))
    return serialise_bitmask(row_major_mask)


def transpose_bytearray(byte_data: bytes, shape: Tuple[int, int]) -> bytes:
    rows, cols = shape
    transposed_byte_data = bytearray(len(byte_data))
    for row in range(rows):
        for col in range(cols):
            transposed_byte_data[col * rows + row] = byte_data[row * cols + col]

    return transposed_byte_data


def ranges_to_rle_counts(ranges: Sequence[Tuple[int, int]]) -> List[int]:
    """Convert sorted non-overlapping ranges to RLE counts.

    This is O(number of ranges) rather than O(number of points), making it
    efficient for large point sets represented as ranges.

    Args:
        ranges: Sorted list of (start, end) tuples representing inclusive ranges.
                Ranges must be non-overlapping and sorted by start.

    Returns:
        List of RLE counts alternating between empty and present runs
    """
    if len(ranges) == 0:
        return []

    run_lengths: List[int] = []
    prev_end = -1

    for start, end in ranges:
        empty_run_length = start - prev_end - 1
        present_run_length = end - start + 1
        run_lengths.append(empty_run_length)
        run_lengths.append(present_run_length)
        prev_end = end

    return run_lengths


def rle_string_to_points(rle_string: str) -> Set[int]:
    points: Set[int] = set()
    if not rle_string:
        return points

    rle_counts = _string_to_rle(rle_string)
    current_index = 0

    # RLE counts alternate between empty and present runs
    for i, count in enumerate(rle_counts):
        if i % 2 != 0:
            points.update(range(current_index, current_index + count))
        current_index += count

    return points


def _ensure_rle_supported_shape(object_instance: "ObjectInstance", supported_shape: Shape) -> None:
    if object_instance.ontology_item.shape == supported_shape:
        return

    raise LabelRowError(
        f"RLE strings are only supported for {supported_shape.value} objects, "
        f"but got shape '{object_instance.ontology_item.shape}'."
    )


def rle_string_to_ranges(object_instance: "ObjectInstance", rle_string: str, *, range_name: str) -> Ranges:
    _ensure_rle_supported_shape(object_instance, Shape.SEGMENTATION)

    ranges = frames_to_ranges(rle_string_to_points(rle_string))
    if not ranges:
        raise LabelRowError(f"The RLE string produced no valid {range_name}.")

    return ranges


def rle_string_to_bitmask_coordinates(
    object_instance: "ObjectInstance",
    rle_string: str,
    *,
    width: Optional[int],
    height: Optional[int],
) -> "BitmaskCoordinates":
    from encord.objects.bitmask import BitmaskCoordinates

    _ensure_rle_supported_shape(object_instance, Shape.BITMASK)

    if width is None or height is None or width <= 0 or height <= 0:
        raise LabelRowError("RLE string bitmask annotations require image width and height.")

    return BitmaskCoordinates(
        BitmaskCoordinates.EncodedBitmask(
            top=0,
            left=0,
            height=height,
            width=width,
            rle_string=rle_string,
        )
    )
