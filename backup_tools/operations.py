"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "folder_backup": "Folder Backup",
    "incremental_backup": "Incremental Backup",
    "mirror_backup": "Mirror Backup",
    "backup_verify": "Backup Verify",
    "backup_manifest": "Backup Manifest",
    "backup_difference": "Backup Difference",
    "backup_restore": "Backup Restore",
    "backup_cleanup": "Backup Cleanup",
    "backup_rotation": "Backup Rotation",
    "backup_compression": "Backup Compression",
    "backup_schedule_generator": "Backup Schedule Generator",
    "backup_size_calculator": "Backup Size Calculator",
    "snapshot_inventory": "Snapshot Inventory",
    "backup_log_analyzer": "Backup Log Analyzer",
    "backup_integrity_hash": "Backup Integrity Hash",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
