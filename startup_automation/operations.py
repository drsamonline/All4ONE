"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "startup_folder_viewer": "Startup Folder Viewer",
    "startup_entry_inventory": "Startup Entry Inventory",
    "startup_folder_cleaner": "Startup Folder Cleaner",
    "scheduled_task_list": "Scheduled Task List",
    "scheduled_task_details": "Scheduled Task Details",
    "scheduled_task_run": "Scheduled Task Run",
    "scheduled_task_disable": "Scheduled Task Disable",
    "scheduled_task_enable": "Scheduled Task Enable",
    "task_xml_export": "Task XML Export",
    "task_trigger_guide": "Task Trigger Guide",
    "folder_watch_snapshot": "Folder Watch Snapshot",
    "automation_manifest": "Automation Manifest",
    "startup_report": "Startup Report",
    "logon_task_report": "Logon Task Report",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
