"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "exif_date_reader": "EXIF Date Reader",
    "exif_camera_reader": "EXIF Camera Reader",
    "image_mime_detector": "Image MIME Detector",
    "audio_mime_detector": "Audio MIME Detector",
    "video_mime_detector": "Video MIME Detector",
    "media_file_scanner": "Media File Scanner",
    "media_size_report": "Media Size Report",
    "media_duration_inventory": "Media Duration Inventory",
    "media_extension_summary": "Media Extension Summary",
    "media_duplicate_finder": "Media Duplicate Finder",
    "media_hash_inventory": "Media Hash Inventory",
    "media_folder_report": "Media Folder Report",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
