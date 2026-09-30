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
        "description": "Clean up temp file aging.",
        "handler": "operations.temp_file_aging_cleaner",
        "cli_command": "temp-aging-cleaner",
        "dependencies": []
    },
    {
        "name": "Broken Link Finder",
        "category": "Maintenance",
        "description": "Locate broken link on disk or in scope.",
        "handler": "operations.broken_link_finder",
        "cli_command": "broken-link-finder",
        "dependencies": []
    },
    {
        "name": "Disk Cleanup Preview",
        "category": "Maintenance",
        "description": "Disk Cleanup Preview: query and display disk cleanup preview details as structured JSON.",
        "handler": "operations.disk_cleanup_preview",
        "cli_command": "disk-cleanup-preview",
        "dependencies": []
    },
    {
        "name": "Log Rotation Helper",
        "category": "Maintenance",
        "description": "Assist with log rotation tasks.",
        "handler": "operations.log_rotation_helper",
        "cli_command": "log-rotate",
        "dependencies": []
    }
]
