"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "CPU Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "CPU Monitor Snapshot: cpu-monitor-snapshot operation.",
        "handler": "operations.cpu_monitor_snapshot",
        "cli_command": "cpu-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Memory Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Memory Monitor Snapshot: memory-monitor-snapshot operation.",
        "handler": "operations.memory_monitor_snapshot",
        "cli_command": "memory-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Disk Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Disk Monitor Snapshot: disk-monitor-snapshot operation.",
        "handler": "operations.disk_monitor_snapshot",
        "cli_command": "disk-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Network Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Network Monitor Snapshot: network-monitor-snapshot operation.",
        "handler": "operations.network_monitor_snapshot",
        "cli_command": "network-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Process Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Process Monitor Snapshot: process-monitor-snapshot operation.",
        "handler": "operations.process_monitor_snapshot",
        "cli_command": "process-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Directory Change Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Directory Change Snapshot: directory-change-snapshot operation.",
        "handler": "operations.directory_change_snapshot",
        "cli_command": "directory-change-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "File Count Monitor",
        "category": "Monitoring & Telemetry",
        "description": "File Count Monitor: file-count-monitor operation.",
        "handler": "operations.file_count_monitor",
        "cli_command": "file-count-monitor",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Directory Size Monitor",
        "category": "Monitoring & Telemetry",
        "description": "Directory Size Monitor: directory-size-monitor operation.",
        "handler": "operations.directory_size_monitor",
        "cli_command": "directory-size-monitor",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "System Load Report",
        "category": "Monitoring & Telemetry",
        "description": "System Load Report: system-load-report operation.",
        "handler": "operations.system_load_report",
        "cli_command": "system-load-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Trend CSV",
        "category": "Monitoring & Telemetry",
        "description": "Resource Trend CSV: resource-trend-csv operation.",
        "handler": "operations.resource_trend_csv",
        "cli_command": "resource-trend-csv",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Log Viewer",
        "category": "Monitoring & Telemetry",
        "description": "Resource Log Viewer: resource-log-viewer operation.",
        "handler": "operations.resource_log_viewer",
        "cli_command": "resource-log-viewer",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Monitor Threshold Calculator",
        "category": "Monitoring & Telemetry",
        "description": "Monitor Threshold Calculator: monitor-threshold-calculator operation.",
        "handler": "operations.monitor_threshold_calculator",
        "cli_command": "monitor-threshold-calculator",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Disk Space Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "Disk Space Threshold Check: disk-space-threshold-check operation.",
        "handler": "operations.disk_space_threshold_check",
        "cli_command": "disk-space-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Memory Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "Memory Threshold Check: memory-threshold-check operation.",
        "handler": "operations.memory_threshold_check",
        "cli_command": "memory-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "CPU Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "CPU Threshold Check: cpu-threshold-check operation.",
        "handler": "operations.cpu_threshold_check",
        "cli_command": "cpu-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Network Adapter Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Network Adapter Snapshot: network-adapter-snapshot operation.",
        "handler": "operations.network_adapter_snapshot",
        "cli_command": "network-adapter-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Battery Status",
        "category": "Monitoring & Telemetry",
        "description": "Battery Status: battery-status operation.",
        "handler": "operations.battery_status",
        "cli_command": "battery-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Power Source Status",
        "category": "Monitoring & Telemetry",
        "description": "Power Source Status: power-source-status operation.",
        "handler": "operations.power_source_status",
        "cli_command": "power-source-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Snapshot Diff",
        "category": "Monitoring",
        "description": "Resource Snapshot Diff: resource-snapshot operation.",
        "handler": "operations.resource_snapshot_diff",
        "cli_command": "resource-snapshot",
        "dependencies": [
            "python:psutil"
        ]
    },
    {
        "name": "Long Running Process Finder",
        "category": "Monitoring",
        "description": "Long Running Process Finder: long-running-procs operation.",
        "handler": "operations.long_running_process_finder",
        "cli_command": "long-running-procs",
        "dependencies": [
            "python:psutil"
        ]
    },
    {
        "name": "Open File Handle Report",
        "category": "Monitoring",
        "description": "Open File Handle Report: open-handles operation.",
        "handler": "operations.open_file_handle_report",
        "cli_command": "open-handles",
        "dependencies": [
            "python:psutil"
        ]
    }
]
