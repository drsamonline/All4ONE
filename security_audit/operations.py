"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "file_permission_report": "File Permission Report",
    "world_writable_finder": "World Writable Finder",
    "executable_finder": "Executable Finder",
    "hidden_file_finder": "Hidden File Finder",
    "sensitive_filename_finder": "Sensitive Filename Finder",
    "credential_filename_finder": "Credential Filename Finder",
    "private_key_filename_finder": "Private Key Filename Finder",
    "ssh_key_audit": "SSH Key Audit",
    "hosts_file_audit": "Hosts File Audit",
    "startup_security_audit": "Startup Security Audit",
    "open_share_guide": "Open Share Guide",
    "firewall_status": "Firewall Status",
    "defender_status": "Defender Status",
    "windows_update_status": "Windows Update Status",
    "local_account_inventory": "Local Account Inventory",
    "administrator_group_inventory": "Administrator Group Inventory",
    "service_security_report": "Service Security Report",
    "security_event_summary": "Security Event Summary",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
