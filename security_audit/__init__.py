"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "File Permission Report",
        "category": "Security Auditing",
        "description": "File Permission Report: file-permission-report operation.",
        "handler": "operations.file_permission_report",
        "cli_command": "file-permission-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "World Writable Finder",
        "category": "Security Auditing",
        "description": "World Writable Finder: world-writable-finder operation.",
        "handler": "operations.world_writable_finder",
        "cli_command": "world-writable-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Executable Finder",
        "category": "Security Auditing",
        "description": "Executable Finder: executable-finder operation.",
        "handler": "operations.executable_finder",
        "cli_command": "executable-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Hidden File Finder",
        "category": "Security Auditing",
        "description": "Hidden File Finder: hidden-file-finder operation.",
        "handler": "operations.hidden_file_finder",
        "cli_command": "hidden-file-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Sensitive Filename Finder",
        "category": "Security Auditing",
        "description": "Sensitive Filename Finder: sensitive-filename-finder operation.",
        "handler": "operations.sensitive_filename_finder",
        "cli_command": "sensitive-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Credential Filename Finder",
        "category": "Security Auditing",
        "description": "Credential Filename Finder: credential-filename-finder operation.",
        "handler": "operations.credential_filename_finder",
        "cli_command": "credential-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Private Key Filename Finder",
        "category": "Security Auditing",
        "description": "Private Key Filename Finder: private-key-filename-finder operation.",
        "handler": "operations.private_key_filename_finder",
        "cli_command": "private-key-filename-finder",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "SSH Key Audit",
        "category": "Security Auditing",
        "description": "SSH Key Audit: ssh-key-audit operation.",
        "handler": "operations.ssh_key_audit",
        "cli_command": "ssh-key-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Hosts File Audit",
        "category": "Security Auditing",
        "description": "Hosts File Audit: hosts-file-audit operation.",
        "handler": "operations.hosts_file_audit",
        "cli_command": "hosts-file-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Startup Security Audit",
        "category": "Security Auditing",
        "description": "Startup Security Audit: startup-security-audit operation.",
        "handler": "operations.startup_security_audit",
        "cli_command": "startup-security-audit",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Open Share Guide",
        "category": "Security Auditing",
        "description": "Open Share Guide: open-share-guide operation.",
        "handler": "operations.open_share_guide",
        "cli_command": "open-share-guide",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Firewall Status",
        "category": "Security Auditing",
        "description": "Firewall Status: firewall-status operation.",
        "handler": "operations.firewall_status",
        "cli_command": "firewall-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Defender Status",
        "category": "Security Auditing",
        "description": "Defender Status: defender-status operation.",
        "handler": "operations.defender_status",
        "cli_command": "defender-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Windows Update Status",
        "category": "Security Auditing",
        "description": "Windows Update Status: windows-update-status operation.",
        "handler": "operations.windows_update_status",
        "cli_command": "windows-update-status",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Local Account Inventory",
        "category": "Security Auditing",
        "description": "Local Account Inventory: local-account-inventory operation.",
        "handler": "operations.local_account_inventory",
        "cli_command": "local-account-inventory",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Administrator Group Inventory",
        "category": "Security Auditing",
        "description": "Administrator Group Inventory: administrator-group-inventory operation.",
        "handler": "operations.administrator_group_inventory",
        "cli_command": "administrator-group-inventory",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Service Security Report",
        "category": "Security Auditing",
        "description": "Service Security Report: service-security-report operation.",
        "handler": "operations.service_security_report",
        "cli_command": "service-security-report",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Security Event Summary",
        "category": "Security Auditing",
        "description": "Security Event Summary: security-event-summary operation.",
        "handler": "operations.security_event_summary",
        "cli_command": "security-event-summary",
        "dependencies": [
            "powershell"
        ]
    },
    {
        "name": "Portable App Suspicion Scanner",
        "category": "Security Audit",
        "description": "Portable App Suspicion Scanner: portable-scan operation.",
        "handler": "operations.portable_app_suspicion_scanner",
        "cli_command": "portable-scan",
        "dependencies": []
    },
    {
        "name": "Autostart Registry Diff",
        "category": "Security Audit",
        "description": "Autostart Registry Diff: autostart-diff operation.",
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
        "description": "Recent Docs Privacy Report: recent-docs-report operation.",
        "handler": "operations.recent_docs_privacy_report",
        "cli_command": "recent-docs-report",
        "dependencies": []
    }
]
