import json
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, is_dataclass
from uuid import UUID

import pytest

from encord.beta.workflow_v3 import settings
from encord.orm.base_dto import BaseDTO


@pytest.mark.parametrize(
    "value",
    [
        settings.StartStageSettingsV1(),
        settings.AnnotationStageSettingsV1(),
        settings.ReviewStageSettingsV1(),
        settings.ExternalStageSettingsV1(),
        settings.CompleteStageSettingsV1(),
        settings.ArchiveStageSettingsV1(),
        settings.SkipStageSettingsV1(),
        settings.CollaboratorRouterStageSettingsV1(),
        settings.PercentageRouterStageSettingsV1({UUID(int=1): 1.0}),
        settings.UnknownStageSettings({"newOption": [1, None]}),
    ],
)
def test_all_public_settings_are_frozen_copyable_dataclasses_with_detached_json_safe_export(
    value: settings.Settings,
) -> None:
    shallow = copy(value)
    deep = deepcopy(value)
    exported = value.to_dict()

    assert is_dataclass(value)
    assert not isinstance(value, BaseDTO)
    assert not hasattr(value, "model_dump")
    assert shallow == deep == value
    assert shallow is not value
    assert deep is not value
    assert json.loads(json.dumps(exported)) == exported
    assert value.to_dict() is not exported
    with pytest.raises(FrozenInstanceError):
        setattr(value, "unexpected_setting", True)


@pytest.mark.parametrize(
    "value",
    [
        settings.StartStageSettingsV1(),
        settings.AnnotationStageSettingsV1(),
        settings.ReviewStageSettingsV1(),
        settings.ExternalStageSettingsV1(),
        settings.CompleteStageSettingsV1(),
        settings.ArchiveStageSettingsV1(),
        settings.SkipStageSettingsV1(),
        settings.CollaboratorRouterStageSettingsV1(),
        settings.PercentageRouterStageSettingsV1({UUID(int=1): 1.0}),
    ],
)
def test_version_one_settings_expose_and_export_a_fixed_read_only_version(value: settings.StageSettings) -> None:
    assert getattr(value, "version") == value.to_dict()["version"] == 1
    with pytest.raises(FrozenInstanceError):
        setattr(value, "version", 2)


def test_shared_stage_settings_base_has_no_contract_version() -> None:
    assert not hasattr(settings.StageSettings(), "version")
    assert settings.StageSettings().to_dict() == {}
