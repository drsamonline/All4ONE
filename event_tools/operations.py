"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "event_log_list": "Event Log List",
    "event_log_query": "Event Log Query",
    "event_log_export": "Event Log Export",
    "event_log_source_search": "Event Log Source Search",
    "event_log_level_summary": "Event Log Level Summary",
    "event_log_time_filter": "Event Log Time Filter",
    "event_log_keyword_filter": "Event Log Keyword Filter",
    "event_log_statistics": "Event Log Statistics",
    "event_log_recent_errors": "Event Log Recent Errors",
    "event_log_recent_warnings": "Event Log Recent Warnings",
    "event_log_channel_inventory": "Event Log Channel Inventory",
    "event_log_guide": "Event Log Guide",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
