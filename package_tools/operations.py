"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "python_package_list": "Python Package List",
    "python_package_versions": "Python Package Versions",
    "pip_command_guide": "Pip Command Guide",
    "executable_package_locator": "Executable Package Locator",
    "import_package_test": "Import Package Test",
    "requirements_generator": "Requirements Generator",
    "requirements_auditor": "Requirements Auditor",
    "virtual_environment_finder": "Virtual Environment Finder",
    "virtual_environment_report": "Virtual Environment Report",
    "package_cache_guide": "Package Cache Guide",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
