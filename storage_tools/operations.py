"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "file_age_histogram": "File Age Histogram",
    "extension_statistics": "Extension Statistics",
    "directory_tree_export": "Directory Tree Export",
    "directory_csv_export": "Directory CSV Export",
    "directory_json_export": "Directory JSON Export",
    "duplicate_name_finder": "Duplicate Name Finder",
    "zero_byte_finder": "Zero Byte Finder",
    "read_only_finder": "Read Only Finder",
    "hidden_file_report": "Hidden File Report",
    "symlink_finder": "Symlink Finder",
    "junction_finder": "Junction Finder",
    "long_path_finder": "Long Path Finder",
    "old_file_finder": "Old File Finder",
    "recent_file_finder": "Recent File Finder",
    "file_size_histogram": "File Size Histogram",
    "storage_health_report": "Storage Health Report",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
