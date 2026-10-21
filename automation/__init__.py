def register_tools():
    return [
        {
            "name": "Task Scheduler",
            "category": "Automation",
            "description": "Create a Windows Task Scheduler task to run a command on a daily or one-off schedule.",
            "handler": "scheduler.run",
            "cli_command": "schedule",
            "dependencies": ["schtasks"],
        },
        {
            "name": "Folder Watcher",
            "category": "Automation",
            "description": "Watch a directory and report files added, removed or changed.",
            "handler": "watcher.run",
            "cli_command": "watch",
            "dependencies": [],
        },
    ]
