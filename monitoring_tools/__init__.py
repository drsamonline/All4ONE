"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "CPU Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "CPU Monitor Snapshot: performs the cpu monitor snapshot action with structured, human-readable output.",
        "handler": "operations.cpu_monitor_snapshot",
        "cli_command": "cpu-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Memory Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Memory Monitor Snapshot: performs the memory monitor snapshot action with structured, human-readable output.",
        "handler": "operations.memory_monitor_snapshot",
        "cli_command": "memory-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Disk Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Disk Monitor Snapshot: performs the disk monitor snapshot action with structured, human-readable output.",
        "handler": "operations.disk_monitor_snapshot",
        "cli_command": "disk-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Network Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Network Monitor Snapshot: performs the network monitor snapshot action with structured, human-readable output.",
        "handler": "operations.network_monitor_snapshot",
        "cli_command": "network-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Process Monitor Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Process Monitor Snapshot: performs the process monitor snapshot action with structured, human-readable output.",
        "handler": "operations.process_monitor_snapshot",
        "cli_command": "process-monitor-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Directory Change Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Directory Change Snapshot: performs the directory change snapshot action with structured, human-readable output.",
        "handler": "operations.directory_change_snapshot",
        "cli_command": "directory-change-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "File Count Monitor",
        "category": "Monitoring & Telemetry",
        "description": "File Count Monitor: performs the file count monitor action with structured, human-readable output.",
        "handler": "operations.file_count_monitor",
        "cli_command": "file-count-monitor",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Directory Size Monitor",
        "category": "Monitoring & Telemetry",
        "description": "Directory Size Monitor: performs the directory size monitor action with structured, human-readable output.",
        "handler": "operations.directory_size_monitor",
        "cli_command": "directory-size-monitor",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "System Load Report",
        "category": "Monitoring & Telemetry",
        "description": "System Load Report: performs the system load report action with structured, human-readable output.",
        "handler": "operations.system_load_report",
        "cli_command": "system-load-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Trend CSV",
        "category": "Monitoring & Telemetry",
        "description": "Resource Trend CSV: performs the resource trend csv action with structured, human-readable output.",
        "handler": "operations.resource_trend_csv",
        "cli_command": "resource-trend-csv",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Log Viewer",
        "category": "Monitoring & Telemetry",
        "description": "Resource Log Viewer: performs the resource log viewer action with structured, human-readable output.",
        "handler": "operations.resource_log_viewer",
        "cli_command": "resource-log-viewer",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Monitor Threshold Calculator",
        "category": "Monitoring & Telemetry",
        "description": "Monitor Threshold Calculator: performs the monitor threshold calculator action with structured, human-readable output.",
        "handler": "operations.monitor_threshold_calculator",
        "cli_command": "monitor-threshold-calculator",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Disk Space Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "Disk Space Threshold Check: performs the disk space threshold check action with structured, human-readable output.",
        "handler": "operations.disk_space_threshold_check",
        "cli_command": "disk-space-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Memory Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "Memory Threshold Check: performs the memory threshold check action with structured, human-readable output.",
        "handler": "operations.memory_threshold_check",
        "cli_command": "memory-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "CPU Threshold Check",
        "category": "Monitoring & Telemetry",
        "description": "CPU Threshold Check: performs the cpu threshold check action with structured, human-readable output.",
        "handler": "operations.cpu_threshold_check",
        "cli_command": "cpu-threshold-check",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Network Adapter Snapshot",
        "category": "Monitoring & Telemetry",
        "description": "Network Adapter Snapshot: performs the network adapter snapshot action with structured, human-readable output.",
        "handler": "operations.network_adapter_snapshot",
        "cli_command": "network-adapter-snapshot",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Battery Status",
        "category": "Monitoring & Telemetry",
        "description": "Battery Status: performs the battery status action with structured, human-readable output.",
        "handler": "operations.battery_status",
        "cli_command": "battery-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Power Source Status",
        "category": "Monitoring & Telemetry",
        "description": "Power Source Status: performs the power source status action with structured, human-readable output.",
        "handler": "operations.power_source_status",
        "cli_command": "power-source-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Resource Snapshot Diff",
        "category": "Monitoring",
        "description": "Resource Snapshot Diff: performs the resource snapshot action with structured, human-readable output.",
        "handler": "operations.resource_snapshot_diff",
        "cli_command": "resource-snapshot",
        "dependencies": [
            "python:psutil"
        ]
    },
    {
        "name": "Long Running Process Finder",
        "category": "Monitoring",
        "description": "Long Running Process Finder: performs the long running procs action with structured, human-readable output.",
        "handler": "operations.long_running_process_finder",
        "cli_command": "long-running-procs",
        "dependencies": [
            "python:psutil"
        ]
    },
    {
        "name": "Open File Handle Report",
        "category": "Monitoring",
        "description": "Open File Handle Report: performs the open handles action with structured, human-readable output.",
        "handler": "operations.open_file_handle_report",
        "cli_command": "open-handles",
        "dependencies": [
            "python:psutil"
        ]
    }
]
