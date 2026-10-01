"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "system_summary": "System Summary",
    "os_version": "OS Version",
    "computer_name": "Computer Name",
    "cpu_information": "CPU Information",
    "memory_information": "Memory Information",
    "boot_time": "Boot Time",
    "current_user": "Current User",
    "python_environment": "Python Environment",
    "environment_report": "Environment Report",
    "locale_information": "Locale Information",
    "time_zone_information": "Time Zone Information",
    "system_uptime": "System Uptime",
    "machine_architecture": "Machine Architecture",
    "system_directory_report": "System Directory Report",
    "temporary_directory_report": "Temporary Directory Report",
    "user_profile_report": "User Profile Report",
    "powershell_version": "PowerShell Version",
    "windows_version_report": "Windows Version Report",
    "installed_ram_summary": "Installed RAM Summary",
    "system_environment_export": "System Environment Export",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
