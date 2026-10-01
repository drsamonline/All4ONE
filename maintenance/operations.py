"""Lazy operation adapters; implementations live in core.extended_ops."""


from core.handler_factory import make_handler

_HANDLERS = {
    "temp_file_aging_cleaner": "temp file aging cleaner",
    "broken_link_finder": "broken link finder",
    "disk_cleanup_preview": "disk cleanup preview",
    "log_rotation_helper": "log rotation helper",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
