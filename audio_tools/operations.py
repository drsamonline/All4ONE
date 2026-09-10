"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "audio_duration": "Audio Duration",
    "audio_stream_inspector": "Audio Stream Inspector",
    "audio_normalizer": "Audio Normalizer",
    "audio_trim": "Audio Trim",
    "audio_concatenator": "Audio Concatenator",
    "audio_silence_detector": "Audio Silence Detector",
    "audio_waveform_exporter": "Audio Waveform Exporter",
    "audio_metadata_reader": "Audio Metadata Reader",
    "audio_metadata_cleaner": "Audio Metadata Cleaner",
    "audio_format_converter": "Audio Format Converter",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
