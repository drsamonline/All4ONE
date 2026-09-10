def register_tools():
    return [
        {
            "name": "JSON Formatter",
            "category": "Developer Tools",
            "description": "Validate and pretty-print JSON, optionally writing a formatted file.",
            "handler": "json_fmt.run",
            "cli_command": "json-format",
            "dependencies": [],
        },
        {
            "name": "Binary Hex Viewer",
            "category": "Developer Tools",
            "description": "View arbitrary files as a conventional hexadecimal dump.",
            "handler": "hex_view.run",
            "cli_command": "hexview",
            "dependencies": [],
        },
        {
            "name": "File Type Detector",
            "category": "Developer Tools",
            "description": "Identify common file types from magic bytes.",
            "handler": "file_type.run",
            "cli_command": "filetype",
            "dependencies": [],
        },
    ]
