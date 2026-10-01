def register_tools():
    return [
        {
            "name": "Task Scheduler",
            "category": "Automation",
            "description": "Task Scheduler: task scheduler as structured JSON output.",
            "handler": "scheduler.run",
            "cli_command": "schedule",
            "dependencies": ["schtasks"],
        },
        {
            "name": "Folder Watcher",
            "category": "Automation",
            "description": "Folder Watcher: folder watcher as structured JSON output.",
            "handler": "watcher.run",
            "cli_command": "watch",
            "dependencies": [],
        },
    ]
