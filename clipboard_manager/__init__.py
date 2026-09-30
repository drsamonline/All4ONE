"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Clipboard Read",
        "category": "Clipboard Manager",
        "description": "Clipboard Read: query and display clipboard read details as structured JSON.",
        "handler": "operations.clipboard_read",
        "cli_command": "clipboard-read",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Write",
        "category": "Clipboard Manager",
        "description": "Clipboard Write: query and display clipboard write details as structured JSON.",
        "handler": "operations.clipboard_write",
        "cli_command": "clipboard-write",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Clear",
        "category": "Clipboard Manager",
        "description": "Clipboard Clear: query and display clipboard clear details as structured JSON.",
        "handler": "operations.clipboard_clear",
        "cli_command": "clipboard-clear",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Append",
        "category": "Clipboard Manager",
        "description": "Clipboard Append: query and display clipboard append details as structured JSON.",
        "handler": "operations.clipboard_append",
        "cli_command": "clipboard-append",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Text Length",
        "category": "Clipboard Manager",
        "description": "Clipboard Text Length: query and display clipboard text length details as structured JSON.",
        "handler": "operations.clipboard_text_length",
        "cli_command": "clipboard-text-length",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Word Count",
        "category": "Clipboard Manager",
        "description": "Clipboard Word Count: query and display clipboard word count details as structured JSON.",
        "handler": "operations.clipboard_word_count",
        "cli_command": "clipboard-word-count",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Line Count",
        "category": "Clipboard Manager",
        "description": "Clipboard Line Count: query and display clipboard line count details as structured JSON.",
        "handler": "operations.clipboard_line_count",
        "cli_command": "clipboard-line-count",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Save",
        "category": "Clipboard Manager",
        "description": "Clipboard Save: query and display clipboard save details as structured JSON.",
        "handler": "operations.clipboard_save",
        "cli_command": "clipboard-save",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Load",
        "category": "Clipboard Manager",
        "description": "Clipboard Load: query and display clipboard load details as structured JSON.",
        "handler": "operations.clipboard_load",
        "cli_command": "clipboard-load",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Normalize",
        "category": "Clipboard Manager",
        "description": "Clipboard Normalize: query and display clipboard normalize details as structured JSON.",
        "handler": "operations.clipboard_normalize",
        "cli_command": "clipboard-normalize",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard History Ring",
        "category": "Clipboard",
        "description": "Clipboard History Ring: query and display clipboard history ring details as structured JSON.",
        "handler": "operations.clipboard_history_ring",
        "cli_command": "clipboard-history-ring",
        "dependencies": [
            "python:pyperclip"
        ]
    },
    {
        "name": "Clipboard Paste As Plain",
        "category": "Clipboard",
        "description": "Clipboard Paste As Plain: query and display clipboard paste as plain details as structured JSON.",
        "handler": "operations.clipboard_paste_as_plain",
        "cli_command": "clipboard-paste-plain",
        "dependencies": [
            "python:pyperclip"
        ]
    },
    {
        "name": "Clipboard Hash",
        "category": "Clipboard",
        "description": "Clipboard Hash: query and display clipboard hash details as structured JSON.",
        "handler": "operations.clipboard_hash",
        "cli_command": "clipboard-hash",
        "dependencies": [
            "python:pyperclip"
        ]
    }
]
