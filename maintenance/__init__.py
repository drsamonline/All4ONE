def register_tools():
    return [
        {
            "name": "Disk Cleanup",
            "category": "Maintenance",
            "description": "Launch Windows Disk Cleanup or a configured saved cleanup profile.",
            "handler": "cleanup.run",
            "cli_command": "cleanmgr",
            "dependencies": ["cleanmgr"],
        },
        {
            "name": "Temp File Cleaner",
            "category": "Maintenance",
            "description": "Remove files from the system temporary directory or a selected directory.",
            "handler": "temp_clean.run",
            "cli_command": "temp-clean",
            "dependencies": [],
        },
        {
            "name": "Junk File Finder",
            "category": "Maintenance",
            "description": "Find common temporary, backup, dump, and cache files.",
            "handler": "junk_finder.run",
            "cli_command": "junk-find",
            "dependencies": [],
        },
    ]
