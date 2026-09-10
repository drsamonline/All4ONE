"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "video_duration": "Video Duration",
    "video_stream_inspector": "Video Stream Inspector",
    "video_screenshot": "Video Screenshot",
    "video_clip_cutter": "Video Clip Cutter",
    "video_concatenator": "Video Concatenator",
    "video_gif_maker": "Video GIF Maker",
    "video_audio_extractor": "Video Audio Extractor",
    "video_frame_rate_inspector": "Video Frame Rate Inspector",
    "video_resolution_inspector": "Video Resolution Inspector",
    "video_bitrate_inspector": "Video Bitrate Inspector",
    "video_thumbnail_sheet": "Video Thumbnail Sheet",
    "video_metadata_cleaner": "Video Metadata Cleaner",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
