"""
Converters that import external 3-D annotation platform data into a
:class:`SceneBuilder` instance.

Each public function accepts plain dicts that mirror the native JSON
structures of the respective platform and returns an *un-built*
``SceneBuilder`` so callers can tweak the result before calling ``.build()``.
"""

from __future__ import annotations

from typing import Any

from encord.scene.builder import (
    Direction,
    SceneBuilder,
    intrinsics_simple,
    quaternion_pose,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_default_world_convention(builder: SceneBuilder) -> None:
    """Apply the common x-forward / y-left / z-up convention."""
    builder.set_world_convention(x=Direction.FORWARD, y=Direction.LEFT, z=Direction.UP)


def _join(root: str, path: str) -> str:
    if not root:
        return path
    return root.rstrip("/") + "/" + path.lstrip("/")


# ---------------------------------------------------------------------------
# 1. nuScenes
# ---------------------------------------------------------------------------


def from_nuscenes(
    *,
    ego_pose: dict[str, Any],
    lidar: dict[str, Any],
    cameras: dict[str, dict[str, Any]],
    timestamp: int | float | None = None,
    data_root: str = "",
) -> SceneBuilder:
    """Import a single nuScenes sample into a :class:`SceneBuilder`.

    Parameters
    ----------
    ego_pose:
        ``{"translation": [x,y,z], "rotation": [w,x,y,z]}`` –
        vehicle pose in global frame.  Quaternion is scalar-first.
    lidar:
        ``{"channel": str, "filename": str,
          "calibrated_sensor": {"translation": [x,y,z], "rotation": [w,x,y,z]}}``
    cameras:
        Mapping of channel name → camera dict.  Each dict contains
        ``filename``, ``width``, ``height``, and ``calibrated_sensor``
        with ``translation``, ``rotation``, and ``camera_intrinsic``
        (3×3 row-major list-of-lists).
    timestamp:
        Optional numeric timestamp applied to every event.
    data_root:
        Path prefix prepended to every ``filename``.
    """
    builder = SceneBuilder()
    _set_default_world_convention(builder)

    # -- ego FoR --------------------------------------------------------
    t = ego_pose["translation"]
    r = ego_pose["rotation"]  # [w, x, y, z]
    ego_for = builder.add_for_stream("ego", for_id="ego")
    ego_for.add_event(
        quaternion_pose(qx=r[1], qy=r[2], qz=r[3], qw=r[0], x=t[0], y=t[1], z=t[2]),
        timestamp=timestamp,
    )

    # -- LiDAR -----------------------------------------------------------
    channel = lidar.get("channel", "LIDAR_TOP")
    cs = lidar["calibrated_sensor"]
    lt, lr = cs["translation"], cs["rotation"]
    lidar_pose = quaternion_pose(qx=lr[1], qy=lr[2], qz=lr[3], qw=lr[0], x=lt[0], y=lt[1], z=lt[2])

    pcd = builder.add_pcd_stream(channel, frame_of_reference="ego", pose=lidar_pose)
    pcd.add_event(uri=_join(data_root, lidar["filename"]), timestamp=timestamp)

    # -- Cameras ---------------------------------------------------------
    for cam_name, cam_data in cameras.items():
        cs = cam_data["calibrated_sensor"]
        ct, cr = cs["translation"], cs["rotation"]
        cam_pose = quaternion_pose(qx=cr[1], qy=cr[2], qz=cr[3], qw=cr[0], x=ct[0], y=ct[1], z=ct[2])

        intrinsic_matrix = cs["camera_intrinsic"]
        fx = intrinsic_matrix[0][0]
        fy = intrinsic_matrix[1][1]
        cx = intrinsic_matrix[0][2]
        cy = intrinsic_matrix[1][2]

        cam_stream_name = f"cam_{cam_name}"
        cam_stream = builder.add_camera_stream(cam_stream_name, frame_of_reference="ego")
        cam_stream.add_event(
            cam_data["width"],
            cam_data["height"],
            intrinsics_simple(fx=fx, fy=fy, ox=cx, oy=cy),
            timestamp=timestamp,
            extrinsics=cam_pose,
        )

        img_stream_name = f"img_{cam_name}"
        img_stream = builder.add_image_stream(img_stream_name, camera=cam_stream_name)
        img_stream.add_event(uri=_join(data_root, cam_data["filename"]), timestamp=timestamp)

    return builder


# ---------------------------------------------------------------------------
# 2. Scale AI
# ---------------------------------------------------------------------------


def from_scale_ai(
    task: dict[str, Any],
) -> SceneBuilder:
    """Import a Scale AI task payload into a :class:`SceneBuilder`.

    Handles both *single-frame* (``attachment`` + ``attachments`` keys)
    and *multi-frame* (``frames`` list) layouts.
    """
    builder = SceneBuilder()
    _set_default_world_convention(builder)

    if "frames" in task:
        return _scale_ai_multi_frame(builder, task)
    return _scale_ai_single_frame(builder, task)


def _scale_cam_pose(cam: dict[str, Any]):
    rot = cam.get("camera_rotation_quaternion", {})
    trans = cam.get("camera_translation", {})
    return quaternion_pose(
        qx=rot.get("x", 0.0),
        qy=rot.get("y", 0.0),
        qz=rot.get("z", 0.0),
        qw=rot.get("w", 1.0),
        x=trans.get("x", 0.0),
        y=trans.get("y", 0.0),
        z=trans.get("z", 0.0),
    )


def _scale_cam_intrinsics(cam: dict[str, Any]):
    ci = cam.get("camera_intrinsics", {})
    return intrinsics_simple(
        fx=ci.get("fx", 0.0),
        fy=ci.get("fy", 0.0),
        ox=ci.get("cx", 0.0),
        oy=ci.get("cy", 0.0),
    )


def _scale_ai_single_frame(builder: SceneBuilder, task: dict[str, Any]) -> SceneBuilder:
    # PCD
    pcd = builder.add_pcd_stream("lidar")
    pcd.add_event(uri=task["attachment"], timestamp=0)

    # Cameras
    for idx, cam in enumerate(task.get("attachments", [])):
        cam_name = cam.get("name", f"camera_{idx}")
        pose = _scale_cam_pose(cam)

        cam_stream_name = f"cam_{cam_name}"
        cam_stream = builder.add_camera_stream(cam_stream_name)
        cam_stream.add_event(
            cam.get("width", 0),
            cam.get("height", 0),
            _scale_cam_intrinsics(cam),
            timestamp=0,
            extrinsics=pose,
        )

        img_stream_name = f"img_{cam_name}"
        img_stream = builder.add_image_stream(img_stream_name, camera=cam_stream_name)
        img_stream.add_event(uri=cam["url"], timestamp=0)

    return builder


def _scale_ai_multi_frame(builder: SceneBuilder, task: dict[str, Any]) -> SceneBuilder:
    ego_for = builder.add_for_stream("ego", for_id="ego")
    pcd_stream = builder.add_pcd_stream("lidar", frame_of_reference="ego")

    cam_builders: dict[str, Any] = {}
    img_builders: dict[str, Any] = {}

    for frame_idx, frame in enumerate(task["frames"]):
        ts = frame_idx

        # Ego pose
        ego = frame.get("ego", {})
        ego_rot = ego.get("rotation", {})
        ego_trans = ego.get("translation", {})
        ego_for.add_event(
            quaternion_pose(
                qx=ego_rot.get("x", 0.0),
                qy=ego_rot.get("y", 0.0),
                qz=ego_rot.get("z", 0.0),
                qw=ego_rot.get("w", 1.0),
                x=ego_trans.get("x", 0.0),
                y=ego_trans.get("y", 0.0),
                z=ego_trans.get("z", 0.0),
            ),
            timestamp=ts,
        )

        # PCD
        pcd_stream.add_event(uri=frame["attachment"], timestamp=ts)

        # Cameras
        for idx, cam in enumerate(frame.get("attachments", [])):
            cam_name = cam.get("name", f"camera_{idx}")
            cam_stream_name = f"cam_{cam_name}"
            img_stream_name = f"img_{cam_name}"

            if cam_stream_name not in cam_builders:
                cam_builders[cam_stream_name] = builder.add_camera_stream(cam_stream_name, frame_of_reference="ego")
                img_builders[img_stream_name] = builder.add_image_stream(img_stream_name, camera=cam_stream_name)

            cam_builders[cam_stream_name].add_event(
                cam.get("width", 0),
                cam.get("height", 0),
                _scale_cam_intrinsics(cam),
                timestamp=ts,
                extrinsics=_scale_cam_pose(cam),
            )

            img_builders[img_stream_name].add_event(uri=cam["url"], timestamp=ts)

    return builder


# ---------------------------------------------------------------------------
# 3. Kognic / OpenLABEL
# ---------------------------------------------------------------------------


def from_kognic(
    openlabel: dict[str, Any],
) -> SceneBuilder:
    """Import an ASAM OpenLABEL JSON dict (Kognic export) into a :class:`SceneBuilder`."""
    builder = SceneBuilder()
    _set_default_world_convention(builder)

    root = openlabel.get("openlabel", openlabel)
    streams_def = root.get("streams", {})
    frames = root.get("frames", {})

    # Classify streams
    lidar_streams: list[str] = []
    camera_streams: list[str] = []
    for stream_name, stream_info in streams_def.items():
        stype = stream_info.get("type", "").lower()
        if "lidar" in stype or "pointcloud" in stype or "point_cloud" in stype:
            lidar_streams.append(stream_name)
        elif "camera" in stype or "image" in stype:
            camera_streams.append(stream_name)

    # If no type info, infer from stream properties in frames
    if not lidar_streams and not camera_streams:
        for _frame_id, frame_data in frames.items():
            for stream_name, stream_props in frame_data.get("frame_properties", {}).get("streams", {}).items():
                sp = stream_props.get("stream_properties", {})
                if "point_cloud_file_name" in sp or "uri" in sp:
                    lidar_streams.append(stream_name)
                elif "image_file_name" in sp:
                    camera_streams.append(stream_name)
            break  # only need first frame to classify
        lidar_streams = list(set(lidar_streams))
        camera_streams = list(set(camera_streams))

    # Create ego FoR
    ego_for = builder.add_for_stream("ego", for_id="ego")

    # Create stream builders
    pcd_builders: dict[str, Any] = {}
    for ls in lidar_streams:
        pcd_builders[ls] = builder.add_pcd_stream(ls, frame_of_reference="ego")

    cam_builders: dict[str, Any] = {}
    img_builders: dict[str, Any] = {}
    for cs_name in camera_streams:
        cam_stream_name = f"cam_{cs_name}"
        img_stream_name = f"img_{cs_name}"
        cam_builders[cs_name] = builder.add_camera_stream(cam_stream_name, frame_of_reference="ego")
        img_builders[cs_name] = builder.add_image_stream(img_stream_name, camera=cam_stream_name)

    # Process frames
    sorted_frame_ids = sorted(frames.keys(), key=lambda k: int(k) if k.isdigit() else k)
    for frame_idx, frame_id in enumerate(sorted_frame_ids):
        frame_data = frames[frame_id]
        ts = frame_idx
        frame_props = frame_data.get("frame_properties", {})

        # Ego pose from frame_properties
        ego_pose = frame_props.get("ego_pose", {})
        if ego_pose:
            val = ego_pose.get("val", [0, 0, 0, 0, 0, 0, 1])
            # OpenLABEL val: [x, y, z, qx, qy, qz, qw]
            ego_for.add_event(
                quaternion_pose(
                    qx=val[3] if len(val) > 3 else 0.0,
                    qy=val[4] if len(val) > 4 else 0.0,
                    qz=val[5] if len(val) > 5 else 0.0,
                    qw=val[6] if len(val) > 6 else 1.0,
                    x=val[0] if len(val) > 0 else 0.0,
                    y=val[1] if len(val) > 1 else 0.0,
                    z=val[2] if len(val) > 2 else 0.0,
                ),
                timestamp=ts,
            )
        else:
            # Identity ego pose
            ego_for.add_event(
                quaternion_pose(qx=0, qy=0, qz=0, qw=1, x=0, y=0, z=0),
                timestamp=ts,
            )

        # Stream data from frame_properties.streams
        stream_data = frame_props.get("streams", {})
        for stream_name, stream_props_wrapper in stream_data.items():
            sp = stream_props_wrapper.get("stream_properties", {})

            if stream_name in pcd_builders:
                uri = sp.get("uri", sp.get("point_cloud_file_name", ""))
                pcd_builders[stream_name].add_event(uri=uri, timestamp=ts)
            elif stream_name in cam_builders:
                uri = sp.get("uri", sp.get("image_file_name", ""))
                intrinsics = sp.get("intrinsics_pinhole", {})
                width = intrinsics.get("width_px", sp.get("width", 0))
                height = intrinsics.get("height_px", sp.get("height", 0))
                fx = intrinsics.get("focal_length_x", 0.0)
                fy = intrinsics.get("focal_length_y", 0.0)
                cx = intrinsics.get("principal_point_x", 0.0)
                cy = intrinsics.get("principal_point_y", 0.0)

                ext_pose = None
                extrinsics = sp.get("extrinsics", {})
                if extrinsics:
                    ext_val = extrinsics.get("val", [0, 0, 0, 0, 0, 0, 1])
                    ext_pose = quaternion_pose(
                        qx=ext_val[3] if len(ext_val) > 3 else 0.0,
                        qy=ext_val[4] if len(ext_val) > 4 else 0.0,
                        qz=ext_val[5] if len(ext_val) > 5 else 0.0,
                        qw=ext_val[6] if len(ext_val) > 6 else 1.0,
                        x=ext_val[0] if len(ext_val) > 0 else 0.0,
                        y=ext_val[1] if len(ext_val) > 1 else 0.0,
                        z=ext_val[2] if len(ext_val) > 2 else 0.0,
                    )

                cam_builders[stream_name].add_event(
                    width,
                    height,
                    intrinsics_simple(fx=fx, fy=fy, ox=cx, oy=cy),
                    timestamp=ts,
                    extrinsics=ext_pose,
                )
                img_builders[stream_name].add_event(uri=uri, timestamp=ts)

    return builder


# ---------------------------------------------------------------------------
# 4. Segments AI
# ---------------------------------------------------------------------------


def from_segments_ai(
    sample_attributes: dict[str, Any],
) -> SceneBuilder:
    """Import Segments.ai sample attributes into a :class:`SceneBuilder`.

    Handles single-frame, sequence (``frames`` list), and multi-sensor
    (``sensors`` list) layouts.
    """
    builder = SceneBuilder()
    _set_default_world_convention(builder)

    # Multi-sensor layout
    if "sensors" in sample_attributes:
        return _segments_ai_multi_sensor(builder, sample_attributes)

    # Sequence layout
    if "frames" in sample_attributes:
        return _segments_ai_sequence(builder, sample_attributes)

    # Single-frame layout
    return _segments_ai_single(builder, sample_attributes)


def _segments_ai_ego_pose(ego: dict[str, Any]):
    pos = ego.get("position", {})
    rot = ego.get("heading", ego.get("rotation", {}))
    return quaternion_pose(
        qx=rot.get("qx", 0.0),
        qy=rot.get("qy", 0.0),
        qz=rot.get("qz", 0.0),
        qw=rot.get("qw", 1.0),
        x=pos.get("x", 0.0),
        y=pos.get("y", 0.0),
        z=pos.get("z", 0.0),
    )


def _segments_ai_cam_pose(img_data: dict[str, Any]):
    ext = img_data.get("extrinsics", {})
    trans = ext.get("translation", {})
    rot = ext.get("rotation", {})
    return quaternion_pose(
        qx=rot.get("qx", 0.0),
        qy=rot.get("qy", 0.0),
        qz=rot.get("qz", 0.0),
        qw=rot.get("qw", 1.0),
        x=trans.get("x", 0.0),
        y=trans.get("y", 0.0),
        z=trans.get("z", 0.0),
    )


def _segments_ai_cam_intrinsics(img_data: dict[str, Any]):
    intr = img_data.get("intrinsics", {})
    mat = intr.get("intrinsic_matrix", None)
    if mat and len(mat) >= 3 and len(mat[0]) >= 3:
        fx = mat[0][0]
        fy = mat[1][1]
        cx = mat[0][2]
        cy = mat[1][2]
    else:
        fx = intr.get("fx", 0.0)
        fy = intr.get("fy", 0.0)
        cx = intr.get("cx", 0.0)
        cy = intr.get("cy", 0.0)
    return intrinsics_simple(fx=fx, fy=fy, ox=cx, oy=cy)


def _segments_ai_single(builder: SceneBuilder, attrs: dict[str, Any]) -> SceneBuilder:
    # Ego pose
    ego_data = attrs.get("ego_pose")
    if ego_data:
        ego_for = builder.add_for_stream("ego", for_id="ego")
        ego_for.add_event(_segments_ai_ego_pose(ego_data), timestamp=0)
        pcd = builder.add_pcd_stream("lidar", frame_of_reference="ego")
    else:
        pcd = builder.add_pcd_stream("lidar")

    # PCD
    pcd_url = attrs.get("pcd", {}).get("url", "")
    pcd.add_event(uri=pcd_url, timestamp=0)

    # Images
    for idx, img_data in enumerate(attrs.get("images", [])):
        cam_name = img_data.get("name", f"camera_{idx}")
        cam_stream_name = f"cam_{cam_name}"
        img_stream_name = f"img_{cam_name}"

        cam_kwargs: dict[str, Any] = {}
        if ego_data:
            cam_kwargs["frame_of_reference"] = "ego"

        cam_stream = builder.add_camera_stream(cam_stream_name, **cam_kwargs)
        cam_stream.add_event(
            img_data.get("width", 0),
            img_data.get("height", 0),
            _segments_ai_cam_intrinsics(img_data),
            timestamp=0,
            extrinsics=_segments_ai_cam_pose(img_data),
        )

        img_stream = builder.add_image_stream(img_stream_name, camera=cam_stream_name)
        img_stream.add_event(uri=img_data.get("url", ""), timestamp=0)

    return builder


def _segments_ai_sequence(builder: SceneBuilder, attrs: dict[str, Any]) -> SceneBuilder:
    ego_for = builder.add_for_stream("ego", for_id="ego")
    pcd_stream = builder.add_pcd_stream("lidar", frame_of_reference="ego")

    cam_builders: dict[str, Any] = {}
    img_builders: dict[str, Any] = {}

    for frame_idx, frame in enumerate(attrs["frames"]):
        ts = frame.get("timestamp", frame_idx)

        # Ego pose
        ego_data = frame.get("ego_pose")
        if ego_data:
            ego_for.add_event(_segments_ai_ego_pose(ego_data), timestamp=ts)
        else:
            ego_for.add_event(
                quaternion_pose(qx=0, qy=0, qz=0, qw=1, x=0, y=0, z=0),
                timestamp=ts,
            )

        # PCD
        pcd_url = frame.get("pcd", {}).get("url", "")
        pcd_stream.add_event(uri=pcd_url, timestamp=ts)

        # Images
        for idx, img_data in enumerate(frame.get("images", [])):
            cam_name = img_data.get("name", f"camera_{idx}")
            cam_stream_name = f"cam_{cam_name}"
            img_stream_name = f"img_{cam_name}"

            if cam_stream_name not in cam_builders:
                cam_builders[cam_stream_name] = builder.add_camera_stream(cam_stream_name, frame_of_reference="ego")
                img_builders[img_stream_name] = builder.add_image_stream(img_stream_name, camera=cam_stream_name)

            cam_builders[cam_stream_name].add_event(
                img_data.get("width", 0),
                img_data.get("height", 0),
                _segments_ai_cam_intrinsics(img_data),
                timestamp=ts,
                extrinsics=_segments_ai_cam_pose(img_data),
            )
            img_builders[img_stream_name].add_event(uri=img_data.get("url", ""), timestamp=ts)

    return builder


def _segments_ai_multi_sensor(builder: SceneBuilder, attrs: dict[str, Any]) -> SceneBuilder:
    ego_for = builder.add_for_stream("ego", for_id="ego")
    ego_for.add_event(
        quaternion_pose(qx=0, qy=0, qz=0, qw=1, x=0, y=0, z=0),
        timestamp=0,
    )

    for sensor in attrs["sensors"]:
        sensor_name = sensor.get("name", "sensor")
        sensor_type = sensor.get("type", "").lower()

        if "lidar" in sensor_type or "pointcloud" in sensor_type or "pcd" in sensor_type:
            pcd_stream = builder.add_pcd_stream(sensor_name, frame_of_reference="ego")
            for frame_idx, frame in enumerate(sensor.get("frames", [sensor])):
                uri = frame.get("pcd", {}).get("url", frame.get("url", ""))
                pcd_stream.add_event(uri=uri, timestamp=frame_idx)
        elif "camera" in sensor_type or "image" in sensor_type:
            cam_stream_name = f"cam_{sensor_name}"
            img_stream_name = f"img_{sensor_name}"
            cam_stream = builder.add_camera_stream(cam_stream_name, frame_of_reference="ego")
            img_stream = builder.add_image_stream(img_stream_name, camera=cam_stream_name)

            for frame_idx, frame in enumerate(sensor.get("frames", [sensor])):
                cam_stream.add_event(
                    frame.get("width", 0),
                    frame.get("height", 0),
                    _segments_ai_cam_intrinsics(frame),
                    timestamp=frame_idx,
                    extrinsics=_segments_ai_cam_pose(frame),
                )
                img_stream.add_event(uri=frame.get("url", ""), timestamp=frame_idx)

    return builder


# ---------------------------------------------------------------------------
# 5. Labelbox
# ---------------------------------------------------------------------------


def from_labelbox(
    row_data: dict[str, Any],
) -> SceneBuilder:
    """Import a Labelbox point-cloud data row into a :class:`SceneBuilder`.

    Parameters
    ----------
    row_data:
        The ``row_data`` JSON payload with a ``frames`` list.  Each frame
        contains ``point_cloud`` and ``images`` entries.
    """
    builder = SceneBuilder()
    _set_default_world_convention(builder)

    frames = row_data.get("frames", [])
    if not frames:
        return builder

    ego_for = builder.add_for_stream("ego", for_id="ego")
    pcd_stream = builder.add_pcd_stream("lidar", frame_of_reference="ego")

    cam_builders: dict[str, Any] = {}
    img_builders: dict[str, Any] = {}

    for frame_idx, frame in enumerate(frames):
        ts = frame_idx

        # Ego pose
        ego = frame.get("ego_pose", {})
        if ego:
            ego_rot = ego.get("rotation", {})
            ego_trans = ego.get("position", ego.get("translation", {}))
            ego_for.add_event(
                quaternion_pose(
                    qx=ego_rot.get("x", ego_rot.get("qx", 0.0)),
                    qy=ego_rot.get("y", ego_rot.get("qy", 0.0)),
                    qz=ego_rot.get("z", ego_rot.get("qz", 0.0)),
                    qw=ego_rot.get("w", ego_rot.get("qw", 1.0)),
                    x=ego_trans.get("x", 0.0),
                    y=ego_trans.get("y", 0.0),
                    z=ego_trans.get("z", 0.0),
                ),
                timestamp=ts,
            )
        else:
            ego_for.add_event(
                quaternion_pose(qx=0, qy=0, qz=0, qw=1, x=0, y=0, z=0),
                timestamp=ts,
            )

        # PCD
        pc = frame.get("point_cloud", {})
        pcd_stream.add_event(uri=pc.get("url", ""), timestamp=ts)

        # Cameras / images
        for idx, img_data in enumerate(frame.get("images", [])):
            cam_name = img_data.get("name", f"camera_{idx}")
            cam_stream_name = f"cam_{cam_name}"
            img_stream_name = f"img_{cam_name}"

            if cam_stream_name not in cam_builders:
                cam_builders[cam_stream_name] = builder.add_camera_stream(cam_stream_name, frame_of_reference="ego")
                img_builders[img_stream_name] = builder.add_image_stream(img_stream_name, camera=cam_stream_name)

            # Intrinsics
            intr = img_data.get("intrinsic", {})
            distortion_kwargs: dict[str, float] = {}
            for k_name in ("k1", "k2", "k3", "k4", "k5", "k6", "p1", "p2"):
                if k_name in intr:
                    distortion_kwargs[k_name] = intr[k_name]
            if "skew" in intr:
                distortion_kwargs["skew"] = intr["skew"]

            model = None
            if distortion_kwargs:
                model = "plumb_bob"

            intrinsics = intrinsics_simple(
                fx=intr.get("fx", 0.0),
                fy=intr.get("fy", 0.0),
                ox=intr.get("cx", 0.0),
                oy=intr.get("cy", 0.0),
                model=model,
                **distortion_kwargs,
            )

            # Extrinsics
            ext = img_data.get("extrinsic", {})
            ext_pos = ext.get("position", {})
            ext_rot = ext.get("rotation", {})
            # Labelbox quaternion: {x, y, z, w} matches Encord's {qx, qy, qz, qw}
            extrinsics_pose = quaternion_pose(
                qx=ext_rot.get("x", 0.0),
                qy=ext_rot.get("y", 0.0),
                qz=ext_rot.get("z", 0.0),
                qw=ext_rot.get("w", 1.0),
                x=ext_pos.get("x", 0.0),
                y=ext_pos.get("y", 0.0),
                z=ext_pos.get("z", 0.0),
            )

            cam_builders[cam_stream_name].add_event(
                img_data.get("width", 0),
                img_data.get("height", 0),
                intrinsics,
                timestamp=ts,
                extrinsics=extrinsics_pose,
            )
            img_builders[img_stream_name].add_event(uri=img_data.get("url", ""), timestamp=ts)

    return builder
