def register_tools():
    return [
        {
            "name": "Random File Picker",
            "category": "Miscellaneous",
            "description": "Random File Picker: random file picker as structured JSON output.",
            "handler": "random_picker.run",
            "cli_command": "random-file",
            "dependencies": [],
        },
        {
            "name": "File Age Calculator",
            "category": "Miscellaneous",
            "description": "File Age Calculator: file age calculator as structured JSON output.",
            "handler": "age_calc.run",
            "cli_command": "file-age",
            "dependencies": [],
        },
        {
            "name": "Path Length Checker",
            "category": "Miscellaneous",
            "description": "Path Length Checker: path length checker as structured JSON output.",
            "handler": "path_length.run",
            "cli_command": "path-length",
            "dependencies": [],
        },
    ]
