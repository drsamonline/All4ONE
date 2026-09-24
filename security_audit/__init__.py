"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "File Permission Report",
        "category": "Security Auditing",
        "description": "File Permission Report. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.file_permission_report",
        "cli_command": "file-permission-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "World Writable Finder",
        "category": "Security Auditing",
        "description": "World Writable Finder. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.world_writable_finder",
        "cli_command": "world-writable-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Executable Finder",
        "category": "Security Auditing",
        "description": "Executable Finder. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.executable_finder",
        "cli_command": "executable-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Hidden File Finder",
        "category": "Security Auditing",
        "description": "Hidden File Finder. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.hidden_file_finder",
        "cli_command": "hidden-file-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Sensitive Filename Finder",
        "category": "Security Auditing",
        "description": "Sensitive Filename Finder. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.sensitive_filename_finder",
        "cli_command": "sensitive-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Credential Filename Finder",
        "category": "Security Auditing",
        "description": "Credential Filename Finder. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.credential_filename_finder",
        "cli_command": "credential-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Private Key Filename Finder",
        "category": "Security Auditing",
        "description": "Private Key Filename Finder. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.private_key_filename_finder",
        "cli_command": "private-key-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "SSH Key Audit",
        "category": "Security Auditing",
        "description": "SSH Key Audit. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.ssh_key_audit",
        "cli_command": "ssh-key-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Hosts File Audit",
        "category": "Security Auditing",
        "description": "Hosts File Audit. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.hosts_file_audit",
        "cli_command": "hosts-file-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Startup Security Audit",
        "category": "Security Auditing",
        "description": "Startup Security Audit. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.startup_security_audit",
        "cli_command": "startup-security-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Open Share Guide",
        "category": "Security Auditing",
        "description": "Open Share Guide. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.open_share_guide",
        "cli_command": "open-share-guide",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Firewall Status",
        "category": "Security Auditing",
        "description": "Firewall Status. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.firewall_status",
        "cli_command": "firewall-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Defender Status",
        "category": "Security Auditing",
        "description": "Defender Status. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.defender_status",
        "cli_command": "defender-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Windows Update Status",
        "category": "Security Auditing",
        "description": "Windows Update Status. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.windows_update_status",
        "cli_command": "windows-update-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Local Account Inventory",
        "category": "Security Auditing",
        "description": "Local Account Inventory. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.local_account_inventory",
        "cli_command": "local-account-inventory",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Administrator Group Inventory",
        "category": "Security Auditing",
        "description": "Administrator Group Inventory. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.administrator_group_inventory",
        "cli_command": "administrator-group-inventory",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Service Security Report",
        "category": "Security Auditing",
        "description": "Service Security Report. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.service_security_report",
        "cli_command": "service-security-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Security Event Summary",
        "category": "Security Auditing",
        "description": "Security Event Summary. Uses safe, dependency-aware execution with clear diagnostics.",
        "handler": "operations.security_event_summary",
        "cli_command": "security-event-summary",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Portable App Suspicion Scanner",
        "category": "Security Audit",
        "description": "Portable App Suspicion Scanner. Portable App Suspicion Scanner with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.portable_app_suspicion_scanner",
        "cli_command": "portable-scan",
        "dependencies": []
    },
    {
        "name": "Autostart Registry Diff",
        "category": "Security Audit",
        "description": "Autostart Registry Diff. Autostart Registry Diff with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.autostart_registry_diff",
        "cli_command": "autostart-diff",
        "dependencies": [
            "reg"
        ]
    },
    {
        "name": "Temp Integrity Baseline",
        "category": "Security Audit",
        "description": "Temp Integrity Baseline. Stores SHA-256 baselines in a temp-dir store with --verify comparison.",
        "handler": "operations.file_integrity_baseline",
        "cli_command": "integrity-baseline-plus",
        "dependencies": []
    },
    {
        "name": "Recent Docs Privacy Report",
        "category": "Security Audit",
        "description": "Recent Docs Privacy Report. Recent Docs Privacy Report with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.recent_docs_privacy_report",
        "cli_command": "recent-docs-report",
        "dependencies": []
    }
]
