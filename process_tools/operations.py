"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "process_list": "Process List",
    "process_details": "Process Details",
    "process_search": "Process Search",
    "process_tree": "Process Tree",
    "process_cpu_snapshot": "Process CPU Snapshot",
    "process_memory_snapshot": "Process Memory Snapshot",
    "process_handle_summary": "Process Handle Summary",
    "process_start_time": "Process Start Time",
    "process_environment_summary": "Process Environment Summary",
    "process_path_resolver": "Process Path Resolver",
    "process_priority_reader": "Process Priority Reader",
    "process_priority_setter": "Process Priority Setter",
    "process_affinity_reader": "Process Affinity Reader",
    "process_affinity_setter": "Process Affinity Setter",
    "process_terminate": "Process Terminate",
    "process_wait": "Process Wait",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
