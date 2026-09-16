import pytest

from encord.exceptions import EncordException
from encord.orm.storage import DataUploadTimeSeries, TimeSeriesViewSettings
from encord.storage import TimeSeriesLineChannelViewSettings, TimeSeriesPointsChannelViewSettings


@pytest.mark.parametrize(
    "override",
    [
        {},
        {"label": "Acceleration"},
        {"color": "#123456"},
        {"hidden": True},
        {"lineWidth": 3},
        {"style": "points"},
    ],
)
def test_partial_channel_settings_round_trip(override):
    key = "acc_x"
    settings = TimeSeriesViewSettings.from_dict({"channels": {key: override}})
    serialized = DataUploadTimeSeries(object_url="gs://bucket/series.csv", settings=settings).to_dict()
    channel = serialized["settings"]["channels"][key]
    assert channel.items() >= override.items()
    assert channel["hidden"] == override.get("hidden", False)
    if override.get("style") == "points":
        assert channel["pointRadius"] == 2
    else:
        assert channel["style"] == "line"
        assert channel["lineWidth"] == override.get("lineWidth", 1.5)
    assert TimeSeriesViewSettings.from_dict(settings.to_dict()).to_dict() == settings.to_dict()


def test_existing_public_constructors_accept_partial_overrides():
    assert TimeSeriesLineChannelViewSettings(color="#123456").to_dict() == {
        "color": "#123456",
        "hidden": False,
        "style": "line",
        "lineWidth": 1.5,
    }
    assert TimeSeriesPointsChannelViewSettings(hidden=True).to_dict() == {
        "hidden": True,
        "style": "points",
        "pointRadius": 2,
    }


@pytest.mark.parametrize("model", [TimeSeriesLineChannelViewSettings, TimeSeriesPointsChannelViewSettings])
@pytest.mark.parametrize("override", [{"label": ""}, {"color": "red"}])
def test_invalid_overrides_are_still_rejected(model, override):
    with pytest.raises(ValueError):
        model(**override)


def test_channel_limit_is_preserved():
    assert len(TimeSeriesViewSettings.from_dict({"channels": {str(i): {} for i in range(100)}}).channels) == 100
    with pytest.raises(EncordException, match="at most 100"):
        TimeSeriesViewSettings.from_dict({"channels": {str(i): {} for i in range(101)}})
