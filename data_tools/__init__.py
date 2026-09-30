"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "CSV Inspector",
        "category": "Data & Structured Data",
        "description": "Inspect csv and report internals.",
        "handler": "operations.csv_inspector",
        "cli_command": "csv-inspector",
        "dependencies": []
    },
    {
        "name": "CSV Normalizer",
        "category": "Data & Structured Data",
        "description": "Normalize csv to a canonical form.",
        "handler": "operations.csv_normalizer",
        "cli_command": "csv-normalizer",
        "dependencies": []
    },
    {
        "name": "CSV Column Selector",
        "category": "Data & Structured Data",
        "description": "Normalize csv to a canonical form.",
        "handler": "operations.csv_column_selector",
        "cli_command": "csv-column-selector",
        "dependencies": []
    },
    {
        "name": "CSV Row Filter",
        "category": "Data & Structured Data",
        "description": "Filter csv row by criteria.",
        "handler": "operations.csv_row_filter",
        "cli_command": "csv-row-filter",
        "dependencies": []
    },
    {
        "name": "CSV Sorter",
        "category": "Data & Structured Data",
        "description": "Sort csv records.",
        "handler": "operations.csv_sorter",
        "cli_command": "csv-sorter",
        "dependencies": []
    },
    {
        "name": "CSV Deduplicator",
        "category": "Data & Structured Data",
        "description": "Sort csv records.",
        "handler": "operations.csv_deduplicator",
        "cli_command": "csv-deduplicator",
        "dependencies": []
    },
    {
        "name": "CSV Statistics",
        "category": "Data & Structured Data",
        "description": "CSV Deduplicator: run the 'csv deduplicator' operation and print structured JSON results.",
        "handler": "operations.csv_statistics",
        "cli_command": "csv-statistics",
        "dependencies": []
    },
    {
        "name": "CSV Transposer",
        "category": "Data & Structured Data",
        "description": "CSV Statistics: run the 'csv statistics' operation and print structured JSON results.",
        "handler": "operations.csv_transposer",
        "cli_command": "csv-transposer",
        "dependencies": []
    },
    {
        "name": "JSON Inspector",
        "category": "Data & Structured Data",
        "description": "Inspect json and report internals.",
        "handler": "operations.json_inspector",
        "cli_command": "json-inspector",
        "dependencies": []
    },
    {
        "name": "JSON Minifier",
        "category": "Data & Structured Data",
        "description": "Inspect json and report internals.",
        "handler": "operations.json_minifier",
        "cli_command": "json-minifier",
        "dependencies": []
    },
    {
        "name": "JSON Pretty Printer",
        "category": "Data & Structured Data",
        "description": "Print formatted json pretty.",
        "handler": "operations.json_pretty_printer",
        "cli_command": "json-pretty-printer",
        "dependencies": []
    },
    {
        "name": "JSON Path Extractor",
        "category": "Data & Structured Data",
        "description": "Extract data from json path.",
        "handler": "operations.json_path_extractor",
        "cli_command": "json-path-extractor",
        "dependencies": []
    },
    {
        "name": "JSON Key Flattener",
        "category": "Data & Structured Data",
        "description": "Extract data from json path.",
        "handler": "operations.json_key_flattener",
        "cli_command": "json-key-flattener",
        "dependencies": []
    },
    {
        "name": "JSON Unflattener",
        "category": "Data & Structured Data",
        "description": "JSON Key Flattener: run the 'json key flattener' operation and print structured JSON results.",
        "handler": "operations.json_unflattener",
        "cli_command": "json-unflattener",
        "dependencies": []
    },
    {
        "name": "NDJSON Inspector",
        "category": "Data & Structured Data",
        "description": "Inspect ndjson and report internals.",
        "handler": "operations.ndjson_inspector",
        "cli_command": "ndjson-inspector",
        "dependencies": []
    },
    {
        "name": "NDJSON Filter",
        "category": "Data & Structured Data",
        "description": "Filter ndjson by criteria.",
        "handler": "operations.ndjson_filter",
        "cli_command": "ndjson-filter",
        "dependencies": []
    },
    {
        "name": "SQLite Schema Viewer",
        "category": "Data & Structured Data",
        "description": "Display the contents of sqlite schema.",
        "handler": "operations.sqlite_schema_viewer",
        "cli_command": "sqlite-schema-viewer",
        "dependencies": []
    },
    {
        "name": "SQLite Table Counter",
        "category": "Data & Structured Data",
        "description": "Count occurrences within sqlite table.",
        "handler": "operations.sqlite_table_counter",
        "cli_command": "sqlite-table-counter",
        "dependencies": []
    },
    {
        "name": "SQLite Query Runner",
        "category": "Data & Structured Data",
        "description": "Count occurrences within sqlite table.",
        "handler": "operations.sqlite_query_runner",
        "cli_command": "sqlite-query-runner",
        "dependencies": []
    },
    {
        "name": "SQLite Vacuum Helper",
        "category": "Data & Structured Data",
        "description": "Assist with sqlite vacuum tasks.",
        "handler": "operations.sqlite_vacuum_helper",
        "cli_command": "sqlite-vacuum-helper",
        "dependencies": []
    },
    {
        "name": "CSV Column Extractor",
        "category": "Data Tools",
        "description": "Extract data from csv column.",
        "handler": "operations.csv_column_extractor",
        "cli_command": "csv-column-extractor",
        "dependencies": []
    }
]
