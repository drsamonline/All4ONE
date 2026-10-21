"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "File Permission Report",
        "category": "Security Auditing",
        "description": "Report file permissions for files in a folder (requires PowerShell).",
        "handler": "operations.file_permission_report",
        "cli_command": "file-permission-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "World Writable Finder",
        "category": "Security Auditing",
        "description": "Find world-writable files and folders (requires PowerShell).",
        "handler": "operations.world_writable_finder",
        "cli_command": "world-writable-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Executable Finder",
        "category": "Security Auditing",
        "description": "Find executable files in a folder tree (requires PowerShell).",
        "handler": "operations.executable_finder",
        "cli_command": "executable-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Hidden File Finder",
        "category": "Security Auditing",
        "description": "Find hidden files in a folder tree (requires PowerShell).",
        "handler": "operations.hidden_file_finder",
        "cli_command": "hidden-file-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Sensitive Filename Finder",
        "category": "Security Auditing",
        "description": "Find files whose names suggest secrets (password, token, credential).",
        "handler": "operations.sensitive_filename_finder",
        "cli_command": "sensitive-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Credential Filename Finder",
        "category": "Security Auditing",
        "description": "Find files whose names suggest stored credentials.",
        "handler": "operations.credential_filename_finder",
        "cli_command": "credential-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Private Key Filename Finder",
        "category": "Security Auditing",
        "description": "Find files that look like private keys.",
        "handler": "operations.private_key_filename_finder",
        "cli_command": "private-key-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "SSH Key Audit",
        "category": "Security Auditing",
        "description": "Audit ssh key for policy or safety issues.",
        "handler": "operations.ssh_key_audit",
        "cli_command": "ssh-key-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Hosts File Audit",
        "category": "Security Auditing",
        "description": "Audit hosts file for policy or safety issues.",
        "handler": "operations.hosts_file_audit",
        "cli_command": "hosts-file-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Startup Security Audit",
        "category": "Security Auditing",
        "description": "Audit startup security for policy or safety issues.",
        "handler": "operations.startup_security_audit",
        "cli_command": "startup-security-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Open Share Guide",
        "category": "Security Auditing",
        "description": "Show guidance for open share.",
        "handler": "operations.open_share_guide",
        "cli_command": "open-share-guide",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Firewall Status",
        "category": "Security Auditing",
        "description": "Report current firewall status.",
        "handler": "operations.firewall_status",
        "cli_command": "firewall-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Defender Status",
        "category": "Security Auditing",
        "description": "Report current defender status.",
        "handler": "operations.defender_status",
        "cli_command": "defender-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Windows Update Status",
        "category": "Security Auditing",
        "description": "Report current windows update status.",
        "handler": "operations.windows_update_status",
        "cli_command": "windows-update-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Local Account Inventory",
        "category": "Security Auditing",
        "description": "List local user accounts (requires PowerShell).",
        "handler": "operations.local_account_inventory",
        "cli_command": "local-account-inventory",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Administrator Group Inventory",
        "category": "Security Auditing",
        "description": "List members of the local Administrators group (requires PowerShell).",
        "handler": "operations.administrator_group_inventory",
        "cli_command": "administrator-group-inventory",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Service Security Report",
        "category": "Security Auditing",
        "description": "Report Windows services and their security-relevant settings.",
        "handler": "operations.service_security_report",
        "cli_command": "service-security-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Security Event Summary",
        "category": "Security Auditing",
        "description": "Summarize security event summary at a glance.",
        "handler": "operations.security_event_summary",
        "cli_command": "security-event-summary",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Portable App Suspicion Scanner",
        "category": "Security Audit",
        "description": "Scan for portable app suspicion and list hits.",
        "handler": "operations.portable_app_suspicion_scanner",
        "cli_command": "portable-scan",
        "dependencies": []
    },
    {
        "name": "Autostart Registry Diff",
        "category": "Security Audit",
        "description": "Autostart Registry Diff: show differences between two inputs.",
        "handler": "operations.autostart_registry_diff",
        "cli_command": "autostart-diff",
        "dependencies": [
            "reg"
        ]
    },
    {
        "name": "Temp Integrity Baseline",
        "category": "Security Audit",
        "description": "Record or verify SHA-256 baselines for files, stored in the temp directory.",
        "handler": "operations.file_integrity_baseline",
        "cli_command": "integrity-baseline-plus",
        "dependencies": []
    },
    {
        "name": "Recent Docs Privacy Report",
        "category": "Security Audit",
        "description": "Report recently opened documents from the Windows Recent folder.",
        "handler": "operations.recent_docs_privacy_report",
        "cli_command": "recent-docs-report",
        "dependencies": []
    }
]
