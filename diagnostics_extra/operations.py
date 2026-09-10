"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "system_information_json_export": "System Information JSON Export",
    "system_information_text_export": "System Information Text Export",
    "installed_software_snapshot": "Installed Software Snapshot",
    "windows_features_snapshot": "Windows Features Snapshot",
    "windows_hotfix_snapshot": "Windows Hotfix Snapshot",
    "device_class_summary": "Device Class Summary",
    "usb_device_inventory": "USB Device Inventory",
    "bluetooth_device_inventory": "Bluetooth Device Inventory",
    "printer_inventory": "Printer Inventory",
    "display_inventory": "Display Inventory",
    "audio_device_inventory": "Audio Device Inventory",
    "environment_variable_diff": "Environment Variable Diff",
    "path_deduplication_report": "PATH Deduplication Report",
    "dns_cache_viewer": "DNS Cache Viewer",
    "windows_firewall_rule_count": "Windows Firewall Rule Count",
    "network_connection_table": "Network Connection Table",
    "open_file_guide": "Open File Guide",
    "crash_dump_inventory": "Crash Dump Inventory",
    "log_directory_inventory": "Log Directory Inventory",
    "utility_suite_diagnostics": "Utility Suite Diagnostics",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
