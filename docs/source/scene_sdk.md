# Scene SDK

The Scene SDK (`encord.beta.scene`) provides tools for constructing and uploading
multi-sensor 3D scene data -- the kind used in autonomous driving, robotics, and spatial
perception applications.

The Scene SDK provides the data structures and builder APIs to express Scene information in a
unified format that Encord's platform can ingest, visualise, and annotate.

## Core concepts

### Streams and events

A scene is composed of **streams**, each representing a time-series from one source:

| Stream type       | What it holds                                                 |
| ----------------- | ------------------------------------------------------------- |
| **PCD stream**    | Point cloud data (URIs to file formats supported by the backend scene ingestion API) |
| **Image stream**  | Camera images (URIs), linked to a camera stream               |
| **Camera stream** | Camera intrinsics (focal length, principal point, distortion) |
| **FoR stream**    | Frame-of-reference poses (rotation + translation over time)   |

Each stream contains **events** -- ordered data points. Event timestamps are assigned sequentially.

### Frame-of-Reference (FoR) tree

FoR streams form a hierarchical tree expressing how coordinate frames relate to each other.
A typical setup:

```
root
 └── ego          (vehicle body pose in world coords, changes each frame)
      ├── lidar          (static mount offset from body to LiDAR)
      ├── camera_front   (static mount offset to front camera)
      └── camera_left    (static mount offset to left camera)
```

Streams can have a **static pose** (a fixed mount offset) and be linked to a **dynamic FoR
stream** (whose events change over time).

### Poses and rotations

Poses can be expressed as:

- `CompositePose` -- a rotation + position pair
- `AffinePose` -- a 4x4 affine transform matrix (column-major)

Rotations can be expressed as:

- `QuaternionRotation` -- unit quaternion (qx, qy, qz, qw)
- `EulerRotation` -- Euler angles in radians (extrinsic X-Y-Z)
- `MatrixRotation` -- 3x3 rotation matrix (column-major)

Convenience constructors like `quaternion_pose()`, `euler_pose()`, `matrix_pose()`, and
`affine_transform()` simplify creation.

### Camera intrinsics and distortion

Seven distortion models are supported: `pinhole`, `radial`, `plumb_bob`, `fisheye`,
`rational_polynomial`, `division`, and `ucm`. Corresponding constructors
(`intrinsics_pinhole()`, `intrinsics_fisheye()`, etc.) are provided.

## Building a scene

`SceneBuilder` constructs scenes for upload. Create the top-level builder, add stream builders to it,
and pass the `SceneBuilder` to SDK upload/create methods. The SDK validates and serialises the scene
internally when it needs the upload payload.

```python
from encord.beta.scene import SceneBuilder, quaternion_pose, intrinsics_pinhole

scene = SceneBuilder()

scene.add_for_stream("ego").add_pose(
    quaternion_pose(qx=0, qy=0, qz=0, qw=1, x=0, y=0, z=0),
    timestamp=0,
)

scene.add_pcd_stream("lidar", frame_of_reference="ego").add_pcd(
    uri="s3://bucket/frame0.pcd",
    timestamp=0,
)

scene.add_camera_stream("cam_front", frame_of_reference="ego").add_camera_params(
    width=1920,
    height=1080,
    intrinsics=intrinsics_pinhole(fx=1000, fy=1000, ox=960, oy=540),
    timestamp=0,
)

scene.add_image_stream("img_front", camera="cam_front").add_image(
    uri="s3://bucket/img0.jpg",
    timestamp=0,
)

# `storage_folder` is an `encord.storage.StorageFolder`.
scene_uuid = storage_folder.upload_scene(
    scene=scene,
    title="scene-001",
    integration_id="00000000-0000-0000-0000-000000000000",
)
```

Stream methods validate local inputs as early as possible, such as empty image/PCD URIs or invalid
advanced camera intrinsics. `StorageFolder.upload_scene` performs final structural validation (all
references resolve, no FoR cycles, non-empty streams, etc.) and serialises the
scene for the Encord API.

## Reading a scene

Use `SceneReader` from the beta scene module to fetch a composite scene storage item with signed URLs
for its constituent files.

```python
from encord.beta.scene import CompositeScene, SceneReader

# `item` is an `encord.storage.StorageItem` with item_type `StorageItemType.SCENE`.
scene = SceneReader(item).read()

front = scene.get_stream("img_front", kind="image")
signed_url = front.get_event(timestamp=0).signed_url
```

`get_stream` and `get_event` raise on missing entries. `find_stream` and `find_event` return
``None`` for the same lookups, and ``get_images_at_timestamp`` skips streams without a matching
event.
