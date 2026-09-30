"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Disk Cleanup",
        "category": "Maintenance",
        "description": "Launch Windows Disk Cleanup or a configured saved cleanup profile.",
        "handler": "cleanup.run",
        "cli_command": "cleanmgr",
        "dependencies": [
            "cleanmgr"
        ]
    },
    {
        "name": "Temp File Cleaner",
        "category": "Maintenance",
        "description": "Remove files from the system temporary directory or a selected directory.",
        "handler": "temp_clean.run",
        "cli_command": "temp-clean",
        "dependencies": []
    },
    {
        "name": "Junk File Finder",
        "category": "Maintenance",
        "description": "Find common temporary, backup, dump, and cache files.",
        "handler": "junk_finder.run",
        "cli_command": "junk-find",
        "dependencies": []
    },
    {
        "name": "Temp File Aging Cleaner",
        "category": "Maintenance",
        "description": "Temp File Aging Cleaner: performs the temp aging cleaner action with structured, human-readable output.",
        "handler": "operations.temp_file_aging_cleaner",
        "cli_command": "temp-aging-cleaner",
        "dependencies": []
    },
    {
        "name": "Broken Link Finder",
        "category": "Maintenance",
        "description": "Broken Link Finder: performs the broken link finder action with structured, human-readable output.",
        "handler": "operations.broken_link_finder",
        "cli_command": "broken-link-finder",
        "dependencies": []
    },
    {
        "name": "Disk Cleanup Preview",
        "category": "Maintenance",
        "description": "Disk Cleanup Preview: performs the disk cleanup preview action with structured, human-readable output.",
        "handler": "operations.disk_cleanup_preview",
        "cli_command": "disk-cleanup-preview",
        "dependencies": []
    },
    {
        "name": "Log Rotation Helper",
        "category": "Maintenance",
        "description": "Log Rotation Helper: performs the log rotate action with structured, human-readable output.",
        "handler": "operations.log_rotation_helper",
        "cli_command": "log-rotate",
        "dependencies": []
    }
]
