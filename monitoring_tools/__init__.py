"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "CPU Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of cpu monitor snapshot.",
        "handler": "operations.cpu_monitor_snapshot",
        "cli_command": "cpu-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Memory Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of memory monitor snapshot.",
        "handler": "operations.memory_monitor_snapshot",
        "cli_command": "memory-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Disk Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of disk monitor snapshot.",
        "handler": "operations.disk_monitor_snapshot",
        "cli_command": "disk-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Network Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of network monitor snapshot.",
        "handler": "operations.network_monitor_snapshot",
        "cli_command": "network-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Process Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of process monitor snapshot.",
        "handler": "operations.process_monitor_snapshot",
        "cli_command": "process-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Directory Change Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of directory change snapshot.",
        "handler": "operations.directory_change_snapshot",
        "cli_command": "directory-change-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "File Count Monitor",
        "category": "Monitoring & Telemetry",
        "description": "Monitor file count over time.",
        "handler": "operations.file_count_monitor",
        "cli_command": "file-count-monitor",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Directory Size Monitor",
        "category": "Monitoring & Telemetry",
        "description": "Monitor directory size over time.",
        "handler": "operations.directory_size_monitor",
        "cli_command": "directory-size-monitor",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "System Load Report",
        "category": "Monitoring & Telemetry",
        "description": "System Load Report: query and display system load report details as structured JSON.",
        "handler": "operations.system_load_report",
        "cli_command": "system-load-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Trend CSV",
        "category": "Monitoring & Telemetry",
        "description": "Resource Trend CSV: query and display resource trend csv details as structured JSON.",
        "handler": "operations.resource_trend_csv",
        "cli_command": "resource-trend-csv",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Log Viewer",
        "category": "Monitoring & Telemetry",
        "description": "Display the contents of resource log.",
        "handler": "operations.resource_log_viewer",
        "cli_command": "resource-log-viewer",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Monitor Threshold Calculator",
        "category": "Monitoring & Telemetry",
        "description": "Compute monitor threshold values.",
        "handler": "operations.monitor_threshold_calculator",
        "cli_command": "monitor-threshold-calculator",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Disk Space Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "Disk Space Threshold Check: query and display disk space threshold check details as structured JSON.",
        "handler": "operations.disk_space_threshold_check",
        "cli_command": "disk-space-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Memory Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "Memory Threshold Check: query and display memory threshold check details as structured JSON.",
        "handler": "operations.memory_threshold_check",
        "cli_command": "memory-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "CPU Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "CPU Threshold Check: query and display cpu threshold check details as structured JSON.",
        "handler": "operations.cpu_threshold_check",
        "cli_command": "cpu-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Network Adapter Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Take a point-in-time snapshot of network adapter snapshot.",
        "handler": "operations.network_adapter_snapshot",
        "cli_command": "network-adapter-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Battery Status",
        "category": "Monitoring & Telemetry",
        "description": "Report current battery status.",
        "handler": "operations.battery_status",
        "cli_command": "battery-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Power Source Status",
        "category": "Monitoring & Telemetry",
        "description": "Report current power source status.",
        "handler": "operations.power_source_status",
        "cli_command": "power-source-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Snapshot Diff",
        "category": "Monitoring",
        "description": "Resource Snapshot Diff: query and display resource snapshot diff details as structured JSON.",
        "handler": "operations.resource_snapshot_diff",
        "cli_command": "resource-snapshot",
        "dependencies": [
            "python:psutil"
        ]
    },
    {
        "name": "Long Running Process Finder",
        "category": "Monitoring",
        "description": "Locate long running process on disk or in scope.",
        "handler": "operations.long_running_process_finder",
        "cli_command": "long-running-procs",
        "dependencies": [
            "python:psutil"
        ]
    },
    {
        "name": "Open File Handle Report",
        "category": "Monitoring",
        "description": "Open File Handle Report: query and display open file handle report details as structured JSON.",
        "handler": "operations.open_file_handle_report",
        "cli_command": "open-handles",
        "dependencies": [
            "python:psutil"
        ]
    }
]
