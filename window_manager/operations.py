"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "window_list": "Window List",
    "window_details": "Window Details",
    "window_focus_helper": "Window Focus Helper",
    "always_on_top_toggle": "Always On Top Toggle",
    "window_minimize_all": "Window Minimize All",
    "window_restore_all": "Window Restore All",
    "window_title_search": "Window Title Search",
    "window_process_mapping": "Window Process Mapping",
    "window_geometry_reader": "Window Geometry Reader",
    "window_geometry_setter": "Window Geometry Setter",
    "window_cascade_helper": "Window Cascade Helper",
    "window_tile_helper": "Window Tile Helper",
    "window_transparency_guide": "Window Transparency Guide",
    "window_hotkey_guide": "Window Hotkey Guide",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
