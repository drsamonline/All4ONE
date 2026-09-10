def register_tools():
    return [
        {
            "name": "Empty Folder Cleaner",
            "category": "Directory Management",
            "description": "Find and remove empty directories safely.",
            "handler": "empty_cleaner.run",
            "cli_command": "empty-clean",
            "dependencies": [],
        },
        {
            "name": "Directory Synchronizer",
            "category": "Directory Management",
            "description": "Synchronize a source directory to a destination with optional deletion.",
            "handler": "sync.run",
            "cli_command": "dir-sync",
            "dependencies": [],
        },
        {
            "name": "Disk Usage Analyzer",
            "category": "Directory Management",
            "description": "Calculate total size and show the largest files.",
            "handler": "disk_usage.run",
            "cli_command": "disk-usage",
            "dependencies": [],
        },
        {
            "name": "Hardlink Creator",
            "category": "Directory Management",
            "description": "Replace identical same-volume files with hardlinks.",
            "handler": "hardlink.run",
            "cli_command": "hardlink",
            "dependencies": [],
        },
    ]
