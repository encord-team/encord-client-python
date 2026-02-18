from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from .builder import (
    ROOT_FOR,
    SceneBuilder,
    SimpleIntrinsics,
    intrinsics_fisheye,
    intrinsics_pinhole,
    intrinsics_plumb_bob,
    quaternion_pose,
)

if TYPE_CHECKING:
    from scale_sensor_fusion_io.spec.sfs.types import CameraIntrinsics


def _sfs_intrinsics(intr: CameraIntrinsics) -> SimpleIntrinsics:
    """Convert SFS camera intrinsics to Encord :class:`SimpleIntrinsics`.

    Handles ``brown_conrady`` (mapped to ``plumb_bob``) and fisheye-family
    distortion models.  Raises for unknown distortion models.
    """
    fx, fy, ox, oy = intr.fx, intr.fy, intr.cx, intr.cy

    if intr.distortion is None:
        return intrinsics_pinhole(fx=fx, fy=fy, ox=ox, oy=oy)

    model = intr.distortion.model
    params = intr.distortion.params

    if model == "brown_conrady":
        # brown_conrady params are OpenCV-ordered: [k1, k2, p1, p2, k3]
        # Encord plumb_bob expects: k1, k2, t1, t2, k3
        return intrinsics_plumb_bob(
            fx=fx,
            fy=fy,
            ox=ox,
            oy=oy,
            k1=params[0],
            k2=params[1],
            t1=params[2],
            t2=params[3],
            k3=params[4],
        )

    if model == "fisheye":
        # That's standard Kannala-Brandt:
        # theta_d = theta + k1*theta^3 + k2*theta^5 + k3*theta^7 + k4*theta^9.
        # Same as OpenCV's fisheye model.
        return intrinsics_fisheye(
            fx=fx,
            fy=fy,
            ox=ox,
            oy=oy,
            k1=params[0],
            k2=params[1],
            k3=params[2],
            k4=params[3],
        )

    raise ValueError(f"Unsupported SFS distortion model: {model!r}")


def _write_pcd(path: Path, positions: np.ndarray, intensities: np.ndarray | None, colors: np.ndarray | None) -> None:
    """Write a minimal binary PCD file from an (N, 3) float32 array with optional intensity and RGB."""
    pts = np.asarray(positions, dtype=np.float32).reshape(-1, 3)
    n = len(pts)

    fields = ["x", "y", "z"]
    sizes = ["4", "4", "4"]
    types = ["F", "F", "F"]
    counts = ["1", "1", "1"]

    extra_columns: list[np.ndarray] = []

    if intensities is not None:
        inten = np.asarray(intensities, dtype=np.float32).reshape(n, 1)
        fields.append("intensity")
        sizes.append("4")
        types.append("F")
        counts.append("1")
        extra_columns.append(inten)

    if colors is not None:
        # Pack (N, 3) uint8 RGB into the PCL-standard float32 "rgb" field.
        rgb = np.asarray(colors, dtype=np.uint8).reshape(n, 3)
        packed = (rgb[:, 0].astype(np.uint32) << 16) | (rgb[:, 1].astype(np.uint32) << 8) | rgb[:, 2].astype(np.uint32)
        rgb_float = packed.view(np.float32).reshape(n, 1)
        fields.append("rgb")
        sizes.append("4")
        types.append("F")
        counts.append("1")
        extra_columns.append(rgb_float)

    if extra_columns:
        pts = np.hstack([pts] + extra_columns)

    header = (
        "VERSION 0.7\n"
        f"FIELDS {' '.join(fields)}\n"
        f"SIZE {' '.join(sizes)}\n"
        f"TYPE {' '.join(types)}\n"
        f"COUNT {' '.join(counts)}\n"
        f"WIDTH {n}\n"
        "HEIGHT 1\n"
        "VIEWPOINT 0 0 0 1 0 0 0\n"
        f"POINTS {n}\n"
        "DATA binary\n"
    )
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(pts.tobytes())


def _save_image(path: Path, content: np.ndarray) -> None:
    """Save an ndarray image to PNG."""
    from PIL import Image

    Image.fromarray(content).save(path)


def load_sfs(
    file: Path,
    to_cloud_upload_path: Path,
    cloud_target: str,
) -> SceneBuilder:
    """
    Unpack a SFS file into an encord scene format.
    Stores files that need to be extracted (images, point clouds) in to_cloud_upload_path
    with 1 level of nesting. Url is assumed to be {cloud_target}/{file_name}.
    """
    # Imports only in function so it's not a required dependency (optional dep)
    from scale_sensor_fusion_io.loaders import SFSLoader
    from scale_sensor_fusion_io.spec.sfs import CameraSensor, LidarSensor, OdometrySensor, RadarSensor

    sfs = SFSLoader(str(file)).load_as_sfs()
    encord = SceneBuilder()

    if not sfs.sensors:
        return encord

    to_cloud_upload_path.mkdir(parents=True, exist_ok=True)
    cloud_target = cloud_target.rstrip("/")

    _SensorWithPoses = (CameraSensor, LidarSensor, OdometrySensor, RadarSensor)

    # -- First pass: FoR stream for every sensor that carries poses -----
    # e.g. OdometrySensor "car" defines ego→world; cameras/lidars are children.
    for_names: set[str] = set()
    for sensor in sfs.sensors:
        if not isinstance(sensor, _SensorWithPoses):
            continue
        if sensor.poses is None or not sensor.poses.timestamps:
            continue

        sensor_for_id = f"for_{sensor.id}"
        parent_for_id = f"for_{sensor.parent_id}" if sensor.parent_id is not None else ROOT_FOR

        for_stream = encord.add_for_stream(sensor_for_id, parent_for_id=parent_for_id)
        for ts, vals in zip(sensor.poses.timestamps, sensor.poses.values):
            # PosePath values: [x, y, z, qx, qy, qz, qw]
            for_stream.add_event(
                quaternion_pose(
                    qx=vals[3],
                    qy=vals[4],
                    qz=vals[5],
                    qw=vals[6],
                    x=vals[0],
                    y=vals[1],
                    z=vals[2],
                ),
                timestamp=ts,
            )
        for_names.add(sensor_for_id)

    # -- Second pass: data streams (images, point clouds) ---------------
    for sensor in sfs.sensors:
        sensor_id = str(sensor.id)
        for_ref = f"for_{sensor_id}" if sensor_id in for_names else ROOT_FOR

        # -- Camera sensor -----------------------------------------------
        if isinstance(sensor, CameraSensor) and sensor.images:
            intr = sensor.intrinsics
            intrinsics = _sfs_intrinsics(intr)

            img_name = f"img_{sensor_id}"
            img_stream = encord.add_image_stream_with_camera(
                img_name,
                width=intr.width,
                height=intr.height,
                intrinsics=intrinsics,
                frame_of_reference=for_ref,
            )

            for idx, image in enumerate(sensor.images):
                filename = f"{sensor_id}_{idx}.png"
                _save_image(to_cloud_upload_path / filename, image.content)
                uri = f"{cloud_target}/{filename}"
                img_stream.add_event(uri=uri, timestamp=image.timestamp)

        # -- LiDAR sensor ------------------------------------------------
        elif isinstance(sensor, LidarSensor) and sensor.frames:
            pcd_name = f"pcd_{sensor_id}"
            pcd_stream = encord.add_pcd_stream(pcd_name, frame_of_reference=for_ref)

            for idx, frame in enumerate(sensor.frames):
                filename = f"{sensor_id}_{idx}.pcd"
                _write_pcd(
                    to_cloud_upload_path / filename,
                    frame.points.positions,
                    frame.points.intensities,
                    frame.points.colors,
                )
                uri = f"{cloud_target}/{filename}"
                pcd_stream.add_event(uri=uri, timestamp=frame.timestamp)

    return encord
