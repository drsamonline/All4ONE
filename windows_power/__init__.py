def register_tools():
    return [
        {
            "name": "Registry Editor Shortcut",
            "category": "Windows Power Tools",
            "description": "Launch Windows Registry Editor.",
            "handler": "regedit.run",
            "cli_command": "regedit",
            "dependencies": ["regedit"],
        },
        {
            "name": "System Restore Point Creator",
            "category": "Windows Power Tools",
            "description": "Create a Windows system restore point through PowerShell.",
            "handler": "restore_point.run",
            "cli_command": "restore-point",
            "dependencies": ["powershell"],
        },
        {
            "name": "Driver Backup",
            "category": "Windows Power Tools",
            "description": "Export installed Windows drivers using pnputil.",
            "handler": "driver_backup.run",
            "cli_command": "driver-backup",
            "dependencies": ["pnputil"],
        },
    ]
