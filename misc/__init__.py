def register_tools():
    return [
        {
            "name": "Random File Picker",
            "category": "Miscellaneous",
            "description": "Pick one random file from a directory, optionally recursively.",
            "handler": "random_picker.run",
            "cli_command": "random-file",
            "dependencies": [],
        },
        {
            "name": "File Age Calculator",
            "category": "Miscellaneous",
            "description": "Show modification timestamp and file age.",
            "handler": "age_calc.run",
            "cli_command": "file-age",
            "dependencies": [],
        },
        {
            "name": "Path Length Checker",
            "category": "Miscellaneous",
            "description": "Find files and directories exceeding a configurable path length.",
            "handler": "path_length.run",
            "cli_command": "path-length",
            "dependencies": [],
        },
    ]
