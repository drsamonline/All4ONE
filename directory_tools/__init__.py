def register_tools():
    return [
        {
            "name": "Empty Folder Cleaner",
            "category": "Directory Management",
            "description": "Empty Folder Cleaner: empty folder cleaner as structured JSON output.",
            "handler": "empty_cleaner.run",
            "cli_command": "empty-clean",
            "dependencies": [],
        },
        {
            "name": "Directory Synchronizer",
            "category": "Directory Management",
            "description": "Directory Synchronizer: directory synchronizer as structured JSON output.",
            "handler": "sync.run",
            "cli_command": "dir-sync",
            "dependencies": [],
        },
        {
            "name": "Disk Usage Analyzer",
            "category": "Directory Management",
            "description": "Disk Usage Analyzer: disk usage analyzer as structured JSON output.",
            "handler": "disk_usage.run",
            "cli_command": "disk-usage",
            "dependencies": [],
        },
        {
            "name": "Hardlink Creator",
            "category": "Directory Management",
            "description": "Hardlink Creator: hardlink creator as structured JSON output.",
            "handler": "hardlink.run",
            "cli_command": "hardlink",
            "dependencies": [],
        },
    ]
