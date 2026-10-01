"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "JSON Formatter",
        "category": "Developer Tools",
        "description": "JSON Formatter: json formatter as structured JSON output.",
        "handler": "json_fmt.run",
        "cli_command": "json-format",
        "dependencies": []
    },
    {
        "name": "Binary Hex Viewer",
        "category": "Developer Tools",
        "description": "Binary Hex Viewer: binary hex viewer as structured JSON output.",
        "handler": "hex_view.run",
        "cli_command": "hexview",
        "dependencies": []
    },
    {
        "name": "File Type Detector",
        "category": "Developer Tools",
        "description": "File Type Detector: file type detector as structured JSON output.",
        "handler": "file_type.run",
        "cli_command": "filetype",
        "dependencies": []
    },
    {
        "name": "JSON YAML Converter",
        "category": "Developer Tools",
        "description": "Convert content between JSON and YAML formats.",
        "handler": "operations.json_yaml_converter",
        "cli_command": "json-yaml",
        "dependencies": [
            "python:yaml"
        ]
    },
    {
        "name": "JSON Diff",
        "category": "Developer Tools",
        "description": "JSON Diff: show differences between two inputs.",
        "handler": "operations.json_diff",
        "cli_command": "json-diff",
        "dependencies": []
    },
    {
        "name": "JSON Schema Validator",
        "category": "Developer Tools",
        "description": "Validate json schema structure or content.",
        "handler": "operations.json_schema_validator",
        "cli_command": "json-schema-validate",
        "dependencies": []
    }
]
