try:
    """Trying to import the coco encoder to see if dependencies are installed."""

    from encord.transformers.coco.coco_encoder import CocoEncoder as __CocoEncoder

except ModuleNotFoundError as e:
    raise RuntimeError(
        "Some dependencies were not found. Please ensure to install encord[coco] when using the COCO parsers."
    ) from e
