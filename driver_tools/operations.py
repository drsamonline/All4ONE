"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "driver_list": "Driver List",
    "driver_details": "Driver Details",
    "driver_backup": "Driver Backup",
    "driver_store_inventory": "Driver Store Inventory",
    "driver_signature_check": "Driver Signature Check",
    "driver_version_report": "Driver Version Report",
    "driver_provider_report": "Driver Provider Report",
    "driver_class_report": "Driver Class Report",
    "driver_device_status": "Driver Device Status",
    "driver_update_reminder": "Driver Update Reminder",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
