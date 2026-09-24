"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "cpu_monitor_snapshot": "CPU Monitor Snapshot",
    "memory_monitor_snapshot": "Memory Monitor Snapshot",
    "disk_monitor_snapshot": "Disk Monitor Snapshot",
    "network_monitor_snapshot": "Network Monitor Snapshot",
    "process_monitor_snapshot": "Process Monitor Snapshot",
    "directory_change_snapshot": "Directory Change Snapshot",
    "file_count_monitor": "File Count Monitor",
    "directory_size_monitor": "Directory Size Monitor",
    "system_load_report": "System Load Report",
    "resource_trend_csv": "Resource Trend CSV",
    "resource_log_viewer": "Resource Log Viewer",
    "monitor_threshold_calculator": "Monitor Threshold Calculator",
    "disk_space_threshold_check": "Disk Space Threshold Check",
    "memory_threshold_check": "Memory Threshold Check",
    "cpu_threshold_check": "CPU Threshold Check",
    "network_adapter_snapshot": "Network Adapter Snapshot",
    "battery_status": "Battery Status",
    "power_source_status": "Power Source Status",
    "resource_snapshot_diff": "resource snapshot diff",
    "long_running_process_finder": "long running process finder",
    "open_file_handle_report": "open file handle report",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
