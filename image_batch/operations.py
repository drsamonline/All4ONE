"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "image_batch_inventory": "Image Batch Inventory",
    "image_batch_dimensions": "Image Batch Dimensions",
    "image_batch_extension_convert": "Image Batch Extension Convert",
    "image_batch_resize_plan": "Image Batch Resize Plan",
    "image_batch_rename_plan": "Image Batch Rename Plan",
    "image_batch_hash": "Image Batch Hash",
    "image_batch_duplicate_report": "Image Batch Duplicate Report",
    "image_batch_contact_sheet": "Image Batch Contact Sheet",
    "image_batch_metadata_report": "Image Batch Metadata Report",
    "image_batch_orientation_report": "Image Batch Orientation Report",
    "image_batch_folder_summary": "Image Batch Folder Summary",
    "image_batch_csv_export": "Image Batch CSV Export",
    "image_batch_json_export": "Image Batch JSON Export",
    "image_batch_cleanup_plan": "Image Batch Cleanup Plan",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
