"""Lazy operation adapters; implementations live in core.extended_ops."""


from core.handler_factory import make_handler

_HANDLERS = {
    "json_yaml_converter": "json yaml converter",
    "json_diff": "json diff",
    "json_schema_validator": "json schema validator",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
