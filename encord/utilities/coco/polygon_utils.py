from typing import Any, List

from encord.common.bitmask_operations import deserialise_bitmask
from encord.objects.coordinates import PolygonCoordinates


def find_contours(mask: Any) -> List[List[List[float]]]:
    """
    Find all contours in the given binary mask, including inner contours.
    Returns polygons in GeoJSON format: triple nested list where:
    - Top level = polygon
    - Second level = list of rings (first is outer contour, rest are inner/holes)
    - Third level = flat list of coordinates [x1, y1, x2, y2, ...]

    Args:
        mask: np.ndarray

    Returns:
        List of polygons in GeoJSON format
    """
    try:
        import cv2
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "The 'cv2' and 'numpy' packages are required to import polygon from COCO RLE strings"
            "Install them with: `pip install encord[coco]`"
        ) from e

    contours, hierarchy = cv2.findContours(
        mask.astype(np.uint8),
        cv2.RETR_CCOMP,  # Retrieves all contours and organizes them into a two-level hierarchy
        cv2.CHAIN_APPROX_SIMPLE,
    )

    polygons: List[List[List[float]]] = []

    # First, identify all outer contours (hierarchy[i][3] == -1)
    if hierarchy is not None and len(hierarchy) > 0:
        hierarchy = hierarchy[0]

        for i, contour in enumerate(contours):
            if hierarchy[i][3] == -1:  # This is an outer contour
                # Create a new polygon with this outer contour as the first ring
                polygon = []

                # Add outer contour as first ring
                outer_contour = contour.reshape(-1).tolist()
                polygon.append(outer_contour)

                # Find all holes for this contour
                for j, inner_contour in enumerate(contours):
                    # hierarchy[j][3] == i means this contour is a direct child of the outer contour
                    if hierarchy[j][3] == i:
                        # Add this inner contour (hole) to the polygon
                        inner_points = inner_contour.reshape(-1).tolist()
                        polygon.append(inner_points)

                polygons.append(polygon)

    return polygons


def rle_to_polygons_coordinates(*, counts: str, height: int, width: int) -> PolygonCoordinates:
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "The 'cv2' and 'numpy' packages are required to import polygon from COCO RLE strings"
            "Install them with: `pip install encord[coco]`"
        ) from e
    buffer = deserialise_bitmask(counts, height * width)
    data: np.ndarray = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width))
    polygons = find_contours(data)
    # make coordinates relative to image size
    for polygon in polygons:
        for ring in polygon:
            for i in range(0, len(ring), 2):
                ring[i] /= width
                ring[i + 1] /= height
    return PolygonCoordinates.from_polygons_list(polygons)
