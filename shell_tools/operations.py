"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "shell_command_runner": "Shell Command Runner",
    "powershell_command_runner": "PowerShell Command Runner",
    "command_resolver": "Command Resolver",
    "path_inspector": "PATH Inspector",
    "executable_locator": "Executable Locator",
    "command_history_guide": "Command History Guide",
    "shell_environment_dump": "Shell Environment Dump",
    "working_directory_reporter": "Working Directory Reporter",
    "command_timeout_runner": "Command Timeout Runner",
    "batch_file_generator": "Batch File Generator",
    "powershell_script_generator": "PowerShell Script Generator",
    "shell_quoting_helper": "Shell Quoting Helper",
    "argument_escaper": "Argument Escaper",
    "exit_code_decoder": "Exit Code Decoder",
    "stdout_capture": "STDOUT Capture",
    "stderr_capture": "STDERR Capture",
    "process_pipe_helper": "Process Pipe Helper",
    "command_availability_scan": "Command Availability Scan",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
