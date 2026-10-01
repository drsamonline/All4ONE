def register_tools():
    return [
        {
            "name": "Service Manager",
            "category": "System Utilities",
            "description": "Service Manager: service manager as structured JSON output.",
            "handler": "services.run",
            "cli_command": "service",
            "dependencies": ["sc"],
        },
        {
            "name": "Startup Program Manager",
            "category": "System Utilities",
            "description": "Startup Program Manager: startup program manager as structured JSON output.",
            "handler": "startup.run",
            "cli_command": "startup",
            "dependencies": ["reg"],
        },
        {
            "name": "Environment Variable Editor",
            "category": "System Utilities",
            "description": "Environment Variable Editor: environment variable editor as structured JSON output.",
            "handler": "env_vars.run",
            "cli_command": "env",
            "dependencies": [],
        },
        {
            "name": "Event Log Viewer",
            "category": "System Utilities",
            "description": "Event Log Viewer: event log viewer as structured JSON output.",
            "handler": "event_log.run",
            "cli_command": "eventlog",
            "dependencies": ["wevtutil"],
        },
        {
            "name": "Network Adapter Reset",
            "category": "System Utilities",
            "description": "Network Adapter Reset: network adapter reset as structured JSON output.",
            "handler": "net_reset.run",
            "cli_command": "net-reset",
            "dependencies": ["powershell"],
        },
    ]
