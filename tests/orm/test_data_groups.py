from uuid import UUID

from encord.orm.group_layout import DataGroupShortInfo
from encord.orm.storage import DataGroupCustom


def test_timeline_only_data_group_serialization() -> None:
    first_item = UUID("11111111-1111-1111-1111-111111111111")
    second_item = UUID("22222222-2222-2222-2222-222222222222")

    group = DataGroupCustom(
        layout=None,
        layout_contents={"audio-1": first_item, "audio-2": second_item},
        timeline=["audio-1", "audio-2"],
    )

    assert group.layout is None
    assert group.to_dict() == {
        "layoutType": "custom",
        "layoutContents": {
            "audio-1": str(first_item),
            "audio-2": str(second_item),
        },
        "timeline": ["audio-1", "audio-2"],
    }


def test_timeline_only_data_group_summary_deserialization() -> None:
    first_item = UUID("11111111-1111-1111-1111-111111111111")
    second_item = UUID("22222222-2222-2222-2222-222222222222")

    group = DataGroupShortInfo.from_dict(
        {
            "layoutContents": {
                "audio-1": {"uuid": str(first_item)},
                "audio-2": {"uuid": str(second_item)},
            },
            "layout": None,
            "layoutSettings": {"fixedLayout": False},
            "timeline": ["audio-1", "audio-2"],
        }
    )

    assert group.layout is None
    assert group.timeline == ["audio-1", "audio-2"]
    assert group.layout_contents["audio-1"].uuid == first_item
    assert group.layout_contents["audio-2"].uuid == second_item
