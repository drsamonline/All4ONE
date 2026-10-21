def register_tools():
    return [
        {
            "name": "Empty Folder Cleaner",
            "category": "Directory Management",
            "description": "Find and (optionally) delete empty directories.",
            "handler": "empty_cleaner.run",
            "cli_command": "empty-clean",
            "dependencies": [],
        },
        {
            "name": "Directory Synchronizer",
            "category": "Directory Management",
            "description": "Synchronise one directory tree to another, copying new and changed files.",
            "handler": "sync.run",
            "cli_command": "dir-sync",
            "dependencies": [],
        },
        {
            "name": "Disk Usage Analyzer",
            "category": "Directory Management",
            "description": "Report how much space each entry in a directory consumes.",
            "handler": "disk_usage.run",
            "cli_command": "disk-usage",
            "dependencies": [],
        },
        {
            "name": "Hardlink Creator",
            "category": "Directory Management",
            "description": "Create a hard link to a file (same volume only).",
            "handler": "hardlink.run",
            "cli_command": "hardlink",
            "dependencies": [],
        },
    ]
