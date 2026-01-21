"""Point cloud data (PCD) file loader.

This module provides functionality to load PCD files from URLs or local files,
supporting both ASCII and binary PCD formats.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from numpy.typing import NDArray

# Type mapping from PCD types to numpy dtypes
PCD_TYPE_MAP = {
    ("F", 4): np.float32,
    ("F", 8): np.float64,
    ("U", 1): np.uint8,
    ("U", 2): np.uint16,
    ("U", 4): np.uint32,
    ("I", 1): np.int8,
    ("I", 2): np.int16,
    ("I", 4): np.int32,
}


class PointCloud:
    """A point cloud loaded from a PCD file.

    Attributes:
        points: XYZ positions as array of shape (N, 3).
        colors: RGB or RGBA colors as array of shape (N, 3) or (N, 4), or None.
        intensities: Intensity values as array of shape (N,), or None.
        fields: Dictionary of all point cloud fields with their data.
    """

    def __init__(
        self,
        points: NDArray[np.float64],
        colors: Optional[NDArray[np.float64]] = None,
        intensities: Optional[NDArray[np.float64]] = None,
        fields: Optional[Dict[str, NDArray[Any]]] = None,
        _copy: bool = True,
    ):
        """Initialize a point cloud.

        Args:
            points: XYZ positions as array of shape (N, 3).
            colors: RGB or RGBA colors as array of shape (N, 3) or (N, 4), or None.
            intensities: Intensity values as array of shape (N,), or None.
            fields: Dictionary of all fields with their data.
            _copy: Internal flag. If False, takes ownership of arrays without copying.
        """
        if _copy:
            self._points = np.asarray(points, dtype=np.float64)
            self._colors = np.asarray(colors, dtype=np.float64) if colors is not None else None
            self._intensities = np.asarray(intensities, dtype=np.float64) if intensities is not None else None
            self._fields = fields.copy() if fields else {}
        else:
            # Take ownership without copying (internal use only)
            self._points = points
            self._colors = colors
            self._intensities = intensities
            self._fields = fields or {}

    @property
    def points(self) -> NDArray[np.float64]:
        """Get XYZ points as array of shape (N, 3)."""
        return self._points

    @property
    def colors(self) -> Optional[NDArray[np.float64]]:
        """Get RGB(A) colors as array of shape (N, 3) or (N, 4), or None."""
        return self._colors

    @property
    def intensities(self) -> Optional[NDArray[np.float64]]:
        """Get intensity values as array of shape (N,), or None."""
        return self._intensities

    @property
    def num_points(self) -> int:
        """Get the number of points in the cloud."""
        return self._points.shape[0]

    def get_field(self, name: str) -> Optional[NDArray[Any]]:
        """Get a specific field by name.

        Args:
            name: The field name (e.g., 'x', 'y', 'z', 'intensity', 'rgb').

        Returns:
            The field data as a numpy array, or None if not present.
        """
        return self._fields.get(name)

    def transform(self, matrix: NDArray[np.float64]) -> "PointCloud":
        """Apply a transformation matrix to the point cloud.

        Args:
            matrix: A 4x4 homogeneous transformation matrix.

        Returns:
            A new PointCloud with transformed coordinates.
        """
        matrix = np.asarray(matrix, dtype=np.float64)

        # Extract rotation and translation for more efficient transformation
        # This avoids creating the full homogeneous coordinate array
        rotation = matrix[:3, :3]
        translation = matrix[:3, 3]

        # Apply transformation: new_points = points @ R.T + t
        new_points = self._points @ rotation.T + translation

        # Share colors/intensities/fields - they don't change with transformation
        # This avoids unnecessary memory allocation and copying
        return PointCloud(
            points=new_points,
            colors=self._colors,
            intensities=self._intensities,
            fields=self._fields,
            _copy=False,
        )

    @classmethod
    def from_url(cls, url: str, timeout: float = 30.0, cache_key: Optional[str] = None) -> "PointCloud":
        """Load a point cloud from a URL (synchronous).

        Args:
            url: URL to download the PCD file from.
            timeout: Download timeout in seconds.
            cache_key: If provided, use this as the cache key (e.g., stable/unsigned URL).
                If None, no caching is performed.

        Returns:
            A PointCloud object.
        """
        if cache_key is not None:
            from encord.scene.cache import get_default_cache

            content = get_default_cache().download(url, timeout=timeout, cache_key=cache_key)
        else:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            content = response.content
        return cls.from_bytes(content)

    @classmethod
    async def from_url_async(cls, url: str, timeout: float = 30.0, cache_key: Optional[str] = None) -> "PointCloud":
        """Load a point cloud from a URL (asynchronous).

        Args:
            url: URL to download the PCD file from.
            timeout: Download timeout in seconds.
            cache_key: If provided, use this as the cache key (e.g., stable/unsigned URL).
                If None, no caching is performed.

        Returns:
            A PointCloud object.
        """
        if cache_key is not None:
            from encord.scene.cache import get_default_cache

            content = await get_default_cache().download_async(url, timeout=timeout, cache_key=cache_key)
        else:
            try:
                import aiohttp
            except ImportError:
                raise ImportError(
                    "aiohttp is required for async point cloud loading. Install it with: pip install aiohttp"
                )

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    response.raise_for_status()
                    content = await response.read()
        return cls.from_bytes(content)

    @classmethod
    def from_file(cls, path: str) -> "PointCloud":
        """Load a point cloud from a local file.

        Args:
            path: Path to the PCD file.

        Returns:
            A PointCloud object.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the PCD file format is invalid.
        """
        with open(path, "rb") as f:
            return cls.from_bytes(f.read())

    @classmethod
    def from_bytes(cls, data: bytes) -> "PointCloud":
        """Parse a point cloud from PCD file bytes.

        Args:
            data: Raw bytes of the PCD file.

        Returns:
            A PointCloud object.

        Raises:
            ValueError: If the PCD file format is invalid.
        """
        header, data_start = _parse_pcd_header(data)

        if header["data_type"] == "ascii":
            fields_data = _parse_ascii_data(data[data_start:], header)
        elif header["data_type"] == "binary":
            fields_data = _parse_binary_data(data[data_start:], header)
        elif header["data_type"] == "binary_compressed":
            raise ValueError("Compressed binary PCD format is not yet supported")
        else:
            raise ValueError(f"Unknown PCD data type: {header['data_type']}")

        # Extract standard fields
        points = _extract_xyz(fields_data)
        colors = _extract_colors(fields_data)
        intensities = fields_data.get("intensity")

        return cls(
            points=points,
            colors=colors,
            intensities=intensities,
            fields=fields_data,
        )

    def __len__(self) -> int:
        return self.num_points

    def __repr__(self) -> str:
        return f"PointCloud(num_points={self.num_points}, has_colors={self._colors is not None})"


def _parse_pcd_header(data: bytes) -> Tuple[Dict[str, Any], int]:
    """Parse the PCD file header.

    Returns:
        Tuple of (header_dict, data_start_position).
    """
    header: Dict[str, Any] = {
        "fields": [],
        "sizes": [],
        "types": [],
        "counts": [],
        "width": 0,
        "height": 1,
        "points": 0,
        "data_type": "ascii",
        "viewpoint": [0, 0, 0, 1, 0, 0, 0],
    }

    # Find the end of header (DATA line)
    lines: List[bytes] = []
    pos = 0
    while pos < len(data):
        line_end = data.find(b"\n", pos)
        if line_end == -1:
            line = data[pos:]
            pos = len(data)
        else:
            line = data[pos:line_end]
            pos = line_end + 1

        lines.append(line)

        # Check if this is the DATA line
        line_str = line.decode("ascii", errors="ignore").strip()
        if line_str.upper().startswith("DATA"):
            break

    data_start = pos

    # Parse header lines
    for line in lines:
        line_str = line.decode("ascii", errors="ignore").strip()
        if not line_str or line_str.startswith("#"):
            continue

        parts = line_str.split()
        if len(parts) < 2:
            continue

        key = parts[0].upper()

        if key == "VERSION":
            header["version"] = parts[1]
        elif key == "FIELDS":
            header["fields"] = [p.lower() for p in parts[1:]]
        elif key == "SIZE":
            header["sizes"] = [int(p) for p in parts[1:]]
        elif key == "TYPE":
            header["types"] = parts[1:]
        elif key == "COUNT":
            header["counts"] = [int(p) for p in parts[1:]]
        elif key == "WIDTH":
            header["width"] = int(parts[1])
        elif key == "HEIGHT":
            header["height"] = int(parts[1])
        elif key == "VIEWPOINT":
            header["viewpoint"] = [float(p) for p in parts[1:]]
        elif key == "POINTS":
            header["points"] = int(parts[1])
        elif key == "DATA":
            header["data_type"] = parts[1].lower()

    # Default counts to 1 if not specified
    if not header["counts"]:
        header["counts"] = [1] * len(header["fields"])

    # Calculate number of points
    if header["points"] == 0:
        header["points"] = header["width"] * header["height"]

    return header, data_start


def _parse_ascii_data(data: bytes, header: Dict[str, Any]) -> Dict[str, NDArray[Any]]:
    """Parse ASCII format PCD data."""
    text = data.decode("ascii", errors="ignore")
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    num_points = min(len(lines), header["points"])
    fields = header["fields"]
    sizes = header["sizes"]
    types = header["types"]
    counts = header["counts"]

    # Initialize arrays for each field
    field_data: Dict[str, List[Any]] = {f: [] for f in fields}

    for line in lines[:num_points]:
        values = line.split()
        idx = 0
        for field, size, typ, count in zip(fields, sizes, types, counts):
            field_values = []
            for _ in range(count):
                if idx < len(values):
                    if typ == "F":
                        field_values.append(float(values[idx]))
                    elif typ == "U" or typ == "I":
                        field_values.append(int(values[idx]))
                    else:
                        field_values.append(float(values[idx]))
                    idx += 1
            if count == 1:
                field_data[field].append(field_values[0] if field_values else 0)
            else:
                field_data[field].append(field_values)

    # Convert to numpy arrays
    result: Dict[str, NDArray[Any]] = {}
    for field, size, typ in zip(fields, sizes, types):
        dtype = PCD_TYPE_MAP.get((typ, size), np.float32)
        result[field] = np.array(field_data[field], dtype=dtype)

    return result


def _parse_binary_data(data: bytes, header: Dict[str, Any]) -> Dict[str, NDArray[Any]]:
    """Parse binary format PCD data."""
    fields = header["fields"]
    sizes = header["sizes"]
    types = header["types"]
    counts = header["counts"]
    num_points = header["points"]

    # Calculate point size
    point_size = sum(s * c for s, c in zip(sizes, counts))

    # Build dtype for structured array
    dtype_list: List[Any] = []
    for field, size, typ, count in zip(fields, sizes, types, counts):
        np_dtype = PCD_TYPE_MAP.get((typ, size), np.float32)
        if count == 1:
            dtype_list.append((field, np_dtype))
        else:
            dtype_list.append((field, np_dtype, (count,)))

    dtype = np.dtype(dtype_list)

    # Parse the binary data directly from bytes (no BytesIO needed)
    structured_data = np.frombuffer(data[: point_size * num_points], dtype=dtype)

    # Convert to dictionary - keep original dtype, only convert to float64 when needed
    result: Dict[str, NDArray[Any]] = {}
    for field in fields:
        result[field] = structured_data[field]

    return result


def _extract_xyz(fields_data: Dict[str, NDArray[Any]]) -> NDArray[np.float64]:
    """Extract XYZ coordinates from field data."""
    if "x" in fields_data and "y" in fields_data and "z" in fields_data:
        x = fields_data["x"]
        y = fields_data["y"]
        z = fields_data["z"]

        # Pre-allocate output array and fill columns directly
        n_points = len(x)
        points = np.empty((n_points, 3), dtype=np.float64)
        points[:, 0] = x
        points[:, 1] = y
        points[:, 2] = z
        return points
    else:
        raise ValueError("PCD file must contain x, y, z fields")


def _extract_colors(fields_data: Dict[str, NDArray[Any]]) -> Optional[NDArray[np.float64]]:
    """Extract RGB(A) colors from field data."""
    # Check for separate r, g, b fields
    if "r" in fields_data and "g" in fields_data and "b" in fields_data:
        n_points = len(fields_data["r"])
        has_alpha = "a" in fields_data
        colors = np.empty((n_points, 4 if has_alpha else 3), dtype=np.float64)
        colors[:, 0] = fields_data["r"]
        colors[:, 1] = fields_data["g"]
        colors[:, 2] = fields_data["b"]
        if has_alpha:
            colors[:, 3] = fields_data["a"]
        colors /= 255.0
        return colors

    # Check for packed RGB field
    if "rgb" in fields_data:
        rgb_packed = fields_data["rgb"]
        # RGB is packed as a float, need to reinterpret as int
        rgb_int = rgb_packed.view(np.uint32)
        n_points = len(rgb_int)
        colors = np.empty((n_points, 3), dtype=np.float64)
        colors[:, 0] = (rgb_int >> 16) & 0xFF
        colors[:, 1] = (rgb_int >> 8) & 0xFF
        colors[:, 2] = rgb_int & 0xFF
        colors /= 255.0
        return colors

    # Check for packed RGBA field
    if "rgba" in fields_data:
        rgba_packed = fields_data["rgba"]
        rgba_int = rgba_packed.view(np.uint32)
        n_points = len(rgba_int)
        colors = np.empty((n_points, 4), dtype=np.float64)
        colors[:, 0] = (rgba_int >> 24) & 0xFF
        colors[:, 1] = (rgba_int >> 16) & 0xFF
        colors[:, 2] = (rgba_int >> 8) & 0xFF
        colors[:, 3] = rgba_int & 0xFF
        colors /= 255.0
        return colors

    return None
