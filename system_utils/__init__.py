def register_tools():
    return [
        {
            "name": "Service Manager",
            "category": "System Utilities",
            "description": "Query, start, stop, pause, or continue Windows services.",
            "handler": "services.run",
            "cli_command": "service",
            "dependencies": ["sc"],
        },
        {
            "name": "Startup Program Manager",
            "category": "System Utilities",
            "description": "Inspect Windows Run registry keys.",
            "handler": "startup.run",
            "cli_command": "startup",
            "dependencies": ["reg"],
        },
        {
            "name": "Environment Variable Editor",
            "category": "System Utilities",
            "description": "View variables and optionally set them for the current process or Windows environment.",
            "handler": "env_vars.run",
            "cli_command": "env",
            "dependencies": [],
        },
        {
            "name": "Event Log Viewer",
            "category": "System Utilities",
            "description": "Query Windows event logs via wevtutil.",
            "handler": "event_log.run",
            "cli_command": "eventlog",
            "dependencies": ["wevtutil"],
        },
        {
            "name": "Network Adapter Reset",
            "category": "System Utilities",
            "description": "Disable and re-enable a Windows network adapter with elevation.",
            "handler": "net_reset.run",
            "cli_command": "net-reset",
            "dependencies": ["powershell"],
        },
    ]
