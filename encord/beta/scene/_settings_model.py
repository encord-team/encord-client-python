import importlib.metadata as importlib_metadata

pydantic_version = int(importlib_metadata.version("pydantic").split(".")[0])

if pydantic_version < 2:
    from encord.beta.scene._settings_model_pydantic_v1 import SceneSettingsModel as SceneSettingsModel
    from encord.beta.scene._settings_model_pydantic_v1 import hex_color_field as hex_color_field
else:
    from encord.beta.scene._settings_model_pydantic_v2 import (  # type: ignore[assignment]
        SceneSettingsModel as SceneSettingsModel,
    )
    from encord.beta.scene._settings_model_pydantic_v2 import hex_color_field as hex_color_field
