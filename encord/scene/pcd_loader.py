"""Point cloud data (PCD) file loader.

This module provides functionality to load PCD files from URLs or local files,
supporting both ASCII and binary PCD formats.
"""

from __future__ import annotations

import struct
from io import BytesIO
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
    ):
        """Initialize a point cloud.

        Args:
            points: XYZ positions as array of shape (N, 3).
            colors: RGB or RGBA colors as array of shape (N, 3) or (N, 4), or None.
            intensities: Intensity values as array of shape (N,), or None.
            fields: Dictionary of all fields with their data.
        """
        self._points = np.asarray(points, dtype=np.float64)
        self._colors = np.asarray(colors, dtype=np.float64) if colors is not None else None
        self._intensities = np.asarray(intensities, dtype=np.float64) if intensities is not None else None
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

        # Apply transformation to points
        n_points = self._points.shape[0]
        homogeneous = np.ones((n_points, 4), dtype=np.float64)
        homogeneous[:, :3] = self._points

        transformed = (matrix @ homogeneous.T).T
        new_points = transformed[:, :3]

        return PointCloud(
            points=new_points,
            colors=self._colors.copy() if self._colors is not None else None,
            intensities=self._intensities.copy() if self._intensities is not None else None,
            fields=self._fields.copy(),
        )

    @classmethod
    def from_url(cls, url: str, timeout: float = 30.0) -> "PointCloud":
        """Load a point cloud from a URL (synchronous)."""
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return cls.from_bytes(response.content)

    @classmethod
    async def from_url_async(cls, url: str, timeout: float = 30.0) -> "PointCloud":
        """Load a point cloud from a URL (asynchronous)."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for async point cloud loading. Install it with: pip install aiohttp")

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

    # Parse the binary data
    buffer = BytesIO(data)
    structured_data = np.frombuffer(buffer.read(point_size * num_points), dtype=dtype)

    # Convert to dictionary
    result: Dict[str, NDArray[Any]] = {}
    for field in fields:
        result[field] = structured_data[field].astype(np.float64)

    return result


def _extract_xyz(fields_data: Dict[str, NDArray[Any]]) -> NDArray[np.float64]:
    """Extract XYZ coordinates from field data."""
    if "x" in fields_data and "y" in fields_data and "z" in fields_data:
        x = fields_data["x"].astype(np.float64)
        y = fields_data["y"].astype(np.float64)
        z = fields_data["z"].astype(np.float64)
        return np.column_stack([x, y, z])
    else:
        raise ValueError("PCD file must contain x, y, z fields")


def _extract_colors(fields_data: Dict[str, NDArray[Any]]) -> Optional[NDArray[np.float64]]:
    """Extract RGB(A) colors from field data."""
    # Check for separate r, g, b fields
    if "r" in fields_data and "g" in fields_data and "b" in fields_data:
        r = fields_data["r"].astype(np.float64) / 255.0
        g = fields_data["g"].astype(np.float64) / 255.0
        b = fields_data["b"].astype(np.float64) / 255.0
        if "a" in fields_data:
            a = fields_data["a"].astype(np.float64) / 255.0
            return np.column_stack([r, g, b, a])
        return np.column_stack([r, g, b])

    # Check for packed RGB field
    if "rgb" in fields_data:
        rgb_packed = fields_data["rgb"]
        # RGB is packed as a float, need to reinterpret as int
        rgb_int = rgb_packed.view(np.uint32)
        r = ((rgb_int >> 16) & 0xFF).astype(np.float64) / 255.0
        g = ((rgb_int >> 8) & 0xFF).astype(np.float64) / 255.0
        b = (rgb_int & 0xFF).astype(np.float64) / 255.0
        return np.column_stack([r, g, b])

    # Check for packed RGBA field
    if "rgba" in fields_data:
        rgba_packed = fields_data["rgba"]
        rgba_int = rgba_packed.view(np.uint32)
        r = ((rgba_int >> 24) & 0xFF).astype(np.float64) / 255.0
        g = ((rgba_int >> 16) & 0xFF).astype(np.float64) / 255.0
        b = ((rgba_int >> 8) & 0xFF).astype(np.float64) / 255.0
        a = (rgba_int & 0xFF).astype(np.float64) / 255.0
        return np.column_stack([r, g, b, a])

    return None
