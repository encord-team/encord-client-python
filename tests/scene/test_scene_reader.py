import pytest
from typing_extensions import cast

from encord.beta.scene import CompositeScene, ImageStream, PointCloudStream, SceneEvent
from encord.beta.scene.internal.scene import Scene as InternalScene
from encord.beta.scene.internal.scene import SceneResponse
from encord.beta.scene.reader import scene_from_internal


def test_scene_reader_converts_internal_streams() -> None:
    response = SceneResponse.model_validate(
        {
            "type": "composite",
            "streams": {
                "lidar": {
                    "type": "event",
                    "id": "lidar",
                    "stream": {
                        "entityType": "point_cloud",
                        "events": [
                            {
                                "timestamp": 0,
                                "url": "gs://bucket/lidar-0.pcd",
                                "signedUrl": "https://signed.example/lidar-0.pcd",
                            }
                        ],
                    },
                },
                "front": {
                    "type": "event",
                    "id": "front",
                    "stream": {
                        "entityType": "image",
                        "events": [
                            {
                                "timestamp": 0,
                                "url": "gs://bucket/front-0.jpg",
                                "signedUrl": "https://signed.example/front-0.jpg",
                            }
                        ],
                    },
                },
            },
        }
    )

    scene = scene_from_internal(cast(InternalScene, response.root))

    assert isinstance(scene, CompositeScene)
    point_cloud_stream = scene.get_stream("lidar", kind="point_cloud")
    image_stream = scene.get_stream("front", kind="image")
    assert isinstance(point_cloud_stream, PointCloudStream)
    assert isinstance(image_stream, ImageStream)
    assert point_cloud_stream.get_event(0).signed_url == "https://signed.example/lidar-0.pcd"
    assert image_stream.get_event(0).signed_url == "https://signed.example/front-0.jpg"


def test_get_stream_raises_for_unknown_stream_id() -> None:
    scene = CompositeScene(point_cloud_streams=[], image_streams=[])

    with pytest.raises(KeyError, match="No point cloud stream with id 'lidar'"):
        scene.get_stream("lidar", kind="point_cloud")

    with pytest.raises(KeyError, match="No image stream with id 'front'"):
        scene.get_stream("front", kind="image")


def test_find_stream_returns_none_for_unknown_stream_id() -> None:
    scene = CompositeScene(point_cloud_streams=[], image_streams=[])

    assert scene.find_stream("lidar", kind="point_cloud") is None
    assert scene.find_stream("front", kind="image") is None


def test_get_event_raises_when_event_missing() -> None:
    stream = ImageStream(stream_id="front", events=[])

    with pytest.raises(KeyError, match="No event with timestamp 0 for stream 'front'"):
        stream.get_event(0)


def test_find_event_returns_none_when_event_missing() -> None:
    stream = ImageStream(stream_id="front", events=[])

    assert stream.find_event(0) is None


def test_get_images_at_timestamp_skips_streams_without_matching_event() -> None:
    scene = CompositeScene(
        point_cloud_streams=[],
        image_streams=[
            ImageStream(
                stream_id="front",
                events=[
                    SceneEvent(
                        timestamp=0, url="gs://bucket/front-0.jpg", signed_url="https://signed.example/front-0.jpg"
                    )
                ],
            ),
            ImageStream(
                stream_id="rear",
                events=[
                    SceneEvent(
                        timestamp=1, url="gs://bucket/rear-1.jpg", signed_url="https://signed.example/rear-1.jpg"
                    )
                ],
            ),
        ],
    )

    images = scene.get_images_at_timestamp(0)

    assert [(stream_id, event.url) for stream_id, event in images] == [("front", "gs://bucket/front-0.jpg")]
