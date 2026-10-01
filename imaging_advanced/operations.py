"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "image_resizer": "Image Resizer",
    "image_cropper": "Image Cropper",
    "image_rotator": "Image Rotator",
    "image_flipper": "Image Flipper",
    "image_converter": "Image Converter",
    "image_optimizer": "Image Optimizer",
    "image_metadata_cleaner": "Image Metadata Cleaner",
    "image_contact_sheet": "Image Contact Sheet",
    "image_montage_builder": "Image Montage Builder",
    "image_border_adder": "Image Border Adder",
    "image_watermark_tool": "Image Watermark Tool",
    "image_batch_renamer": "Image Batch Renamer",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
