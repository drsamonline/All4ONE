"""Lazy operation adapters; implementations live in core.extended_ops."""


from core.handler_factory import make_handler

_HANDLERS = {
    "csv_inspector": "CSV Inspector",
    "csv_normalizer": "CSV Normalizer",
    "csv_column_selector": "CSV Column Selector",
    "csv_row_filter": "CSV Row Filter",
    "csv_sorter": "CSV Sorter",
    "csv_deduplicator": "CSV Deduplicator",
    "csv_statistics": "CSV Statistics",
    "csv_transposer": "CSV Transposer",
    "json_inspector": "JSON Inspector",
    "json_minifier": "JSON Minifier",
    "json_pretty_printer": "JSON Pretty Printer",
    "json_path_extractor": "JSON Path Extractor",
    "json_key_flattener": "JSON Key Flattener",
    "json_unflattener": "JSON Unflattener",
    "ndjson_inspector": "NDJSON Inspector",
    "ndjson_filter": "NDJSON Filter",
    "sqlite_schema_viewer": "SQLite Schema Viewer",
    "sqlite_table_counter": "SQLite Table Counter",
    "sqlite_query_runner": "SQLite Query Runner",
    "sqlite_vacuum_helper": "SQLite Vacuum Helper",
    "csv_column_extractor": "csv column extractor",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
