"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "JSON Formatter",
        "category": "Developer Tools",
        "description": "Validate and pretty-print JSON, optionally writing a formatted file.",
        "handler": "json_fmt.run",
        "cli_command": "json-format",
        "dependencies": []
    },
    {
        "name": "Binary Hex Viewer",
        "category": "Developer Tools",
        "description": "View arbitrary files as a conventional hexadecimal dump.",
        "handler": "hex_view.run",
        "cli_command": "hexview",
        "dependencies": []
    },
    {
        "name": "File Type Detector",
        "category": "Developer Tools",
        "description": "Identify common file types from magic bytes.",
        "handler": "file_type.run",
        "cli_command": "filetype",
        "dependencies": []
    },
    {
        "name": "JSON YAML Converter",
        "category": "Developer Tools",
        "description": "JSON YAML Converter: json-yaml operation.",
        "handler": "operations.json_yaml_converter",
        "cli_command": "json-yaml",
        "dependencies": [
            "python:yaml"
        ]
    },
    {
        "name": "JSON Diff",
        "category": "Developer Tools",
        "description": "JSON Diff: json-diff operation.",
        "handler": "operations.json_diff",
        "cli_command": "json-diff",
        "dependencies": []
    },
    {
        "name": "JSON Schema Validator",
        "category": "Developer Tools",
        "description": "JSON Schema Validator: json-schema-validate operation.",
        "handler": "operations.json_schema_validator",
        "cli_command": "json-schema-validate",
        "dependencies": []
    }
]
