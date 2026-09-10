def register_tools():
    return [
        {
            "name": "Task Scheduler",
            "category": "Automation",
            "description": "Create Windows scheduled tasks using schtasks.",
            "handler": "scheduler.run",
            "cli_command": "schedule",
            "dependencies": ["schtasks"],
        },
        {
            "name": "Folder Watcher",
            "category": "Automation",
            "description": "Watch a directory for added, removed, and changed files.",
            "handler": "watcher.run",
            "cli_command": "watch",
            "dependencies": [],
        },
    ]
