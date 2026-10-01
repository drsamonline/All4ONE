def register_tools():
    return [
        {
            "name": "Registry Editor Shortcut",
            "category": "Windows Power Tools",
            "description": "Registry Editor Shortcut: registry editor shortcut as structured JSON output.",
            "handler": "regedit.run",
            "cli_command": "regedit",
            "dependencies": ["regedit"],
        },
        {
            "name": "System Restore Point Creator",
            "category": "Windows Power Tools",
            "description": "System Restore Point Creator: system restore point creator as structured JSON output.",
            "handler": "restore_point.run",
            "cli_command": "restore-point",
            "dependencies": ["powershell"],
        },
        {
            "name": "Driver Backup",
            "category": "Windows Power Tools",
            "description": "Driver Backup: driver backup as structured JSON output.",
            "handler": "driver_backup.run",
            "cli_command": "driver-backup",
            "dependencies": ["pnputil"],
        },
    ]
