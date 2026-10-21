def register_tools():
    return [
        {
            "name": "Service Manager",
            "category": "System Utilities",
            "description": "Query or start/stop a Windows service (requires sc).",
            "handler": "services.run",
            "cli_command": "service",
            "dependencies": ["sc"],
        },
        {
            "name": "Startup Program Manager",
            "category": "System Utilities",
            "description": "List or edit programs that start with Windows.",
            "handler": "startup.run",
            "cli_command": "startup",
            "dependencies": ["reg"],
        },
        {
            "name": "Environment Variable Editor",
            "category": "System Utilities",
            "description": "Read or write environment variables.",
            "handler": "env_vars.run",
            "cli_command": "env",
            "dependencies": [],
        },
        {
            "name": "Event Log Viewer",
            "category": "System Utilities",
            "description": "Read entries from the Windows event log (requires wevtutil).",
            "handler": "event_log.run",
            "cli_command": "eventlog",
            "dependencies": ["wevtutil"],
        },
        {
            "name": "Network Adapter Reset",
            "category": "System Utilities",
            "description": "Disable and re-enable a network adapter to reset it (Windows, elevated, --yes required).",
            "handler": "net_reset.run",
            "cli_command": "net-reset",
            "dependencies": ["powershell"],
        },
    ]
