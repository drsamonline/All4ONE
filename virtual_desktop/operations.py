"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "virtual_desktop_list": "Virtual Desktop List",
    "virtual_desktop_shortcut": "Virtual Desktop Shortcut",
    "window_desktop_mapper": "Window Desktop Mapper",
    "desktop_count_reader": "Desktop Count Reader",
    "virtual_desktop_settings": "Virtual Desktop Settings",
    "desktop_hotkey_guide": "Desktop Hotkey Guide",
    "desktop_process_summary": "Desktop Process Summary",
    "desktop_launch_helper": "Desktop Launch Helper",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
