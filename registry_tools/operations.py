"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "registry_query": "Registry Query",
    "registry_export": "Registry Export",
    "registry_import": "Registry Import",
    "registry_key_creator": "Registry Key Creator",
    "registry_key_deleter": "Registry Key Deleter",
    "registry_value_setter": "Registry Value Setter",
    "registry_value_deleter": "Registry Value Deleter",
    "registry_value_enumerator": "Registry Value Enumerator",
    "registry_backup": "Registry Backup",
    "registry_path_validator": "Registry Path Validator",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
