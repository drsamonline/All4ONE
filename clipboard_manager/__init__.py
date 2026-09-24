"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Clipboard Read",
        "category": "Clipboard Manager",
        "description": "Clipboard Read: clipboard-read operation.",
        "handler": "operations.clipboard_read",
        "cli_command": "clipboard-read",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Write",
        "category": "Clipboard Manager",
        "description": "Clipboard Write: clipboard-write operation.",
        "handler": "operations.clipboard_write",
        "cli_command": "clipboard-write",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Clear",
        "category": "Clipboard Manager",
        "description": "Clipboard Clear: clipboard-clear operation.",
        "handler": "operations.clipboard_clear",
        "cli_command": "clipboard-clear",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Append",
        "category": "Clipboard Manager",
        "description": "Clipboard Append: clipboard-append operation.",
        "handler": "operations.clipboard_append",
        "cli_command": "clipboard-append",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Text Length",
        "category": "Clipboard Manager",
        "description": "Clipboard Text Length: clipboard-text-length operation.",
        "handler": "operations.clipboard_text_length",
        "cli_command": "clipboard-text-length",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Word Count",
        "category": "Clipboard Manager",
        "description": "Clipboard Word Count: clipboard-word-count operation.",
        "handler": "operations.clipboard_word_count",
        "cli_command": "clipboard-word-count",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Line Count",
        "category": "Clipboard Manager",
        "description": "Clipboard Line Count: clipboard-line-count operation.",
        "handler": "operations.clipboard_line_count",
        "cli_command": "clipboard-line-count",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Save",
        "category": "Clipboard Manager",
        "description": "Clipboard Save: clipboard-save operation.",
        "handler": "operations.clipboard_save",
        "cli_command": "clipboard-save",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Load",
        "category": "Clipboard Manager",
        "description": "Clipboard Load: clipboard-load operation.",
        "handler": "operations.clipboard_load",
        "cli_command": "clipboard-load",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Normalize",
        "category": "Clipboard Manager",
        "description": "Clipboard Normalize: clipboard-normalize operation.",
        "handler": "operations.clipboard_normalize",
        "cli_command": "clipboard-normalize",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard History Ring",
        "category": "Clipboard",
        "description": "Clipboard History Ring: clipboard-history-ring operation.",
        "handler": "operations.clipboard_history_ring",
        "cli_command": "clipboard-history-ring",
        "dependencies": [
            "python:pyperclip"
        ]
    },
    {
        "name": "Clipboard Paste As Plain",
        "category": "Clipboard",
        "description": "Clipboard Paste As Plain: clipboard-paste-plain operation.",
        "handler": "operations.clipboard_paste_as_plain",
        "cli_command": "clipboard-paste-plain",
        "dependencies": [
            "python:pyperclip"
        ]
    },
    {
        "name": "Clipboard Hash",
        "category": "Clipboard",
        "description": "Clipboard Hash: clipboard-hash operation.",
        "handler": "operations.clipboard_hash",
        "cli_command": "clipboard-hash",
        "dependencies": [
            "python:pyperclip"
        ]
    }
]
