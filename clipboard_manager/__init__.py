"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Clipboard Read",
        "category": "Clipboard Manager",
        "description": "Print the current clipboard text (requires pyperclip).",
        "handler": "operations.clipboard_read",
        "cli_command": "clipboard-read",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Write",
        "category": "Clipboard Manager",
        "description": "Replace the clipboard contents with the supplied text.",
        "handler": "operations.clipboard_write",
        "cli_command": "clipboard-write",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Clear",
        "category": "Clipboard Manager",
        "description": "Empty the clipboard.",
        "handler": "operations.clipboard_clear",
        "cli_command": "clipboard-clear",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Append",
        "category": "Clipboard Manager",
        "description": "Append text to the existing clipboard contents.",
        "handler": "operations.clipboard_append",
        "cli_command": "clipboard-append",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Text Length",
        "category": "Clipboard Manager",
        "description": "Report character, word and line counts for the clipboard text.",
        "handler": "operations.clipboard_text_length",
        "cli_command": "clipboard-text-length",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Word Count",
        "category": "Clipboard Manager",
        "description": "Produce a clipboard word count count.",
        "handler": "operations.clipboard_word_count",
        "cli_command": "clipboard-word-count",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Line Count",
        "category": "Clipboard Manager",
        "description": "Produce a clipboard line count count.",
        "handler": "operations.clipboard_line_count",
        "cli_command": "clipboard-line-count",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Save",
        "category": "Clipboard Manager",
        "description": "Save the clipboard text to a file.",
        "handler": "operations.clipboard_save",
        "cli_command": "clipboard-save",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Load",
        "category": "Clipboard Manager",
        "description": "Load a file's contents into the clipboard.",
        "handler": "operations.clipboard_load",
        "cli_command": "clipboard-load",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard Normalize",
        "category": "Clipboard Manager",
        "description": "Normalise clipboard whitespace and line endings.",
        "handler": "operations.clipboard_normalize",
        "cli_command": "clipboard-normalize",
        "dependencies": [
            "python:tkinter"
        ]
    },
    {
        "name": "Clipboard History Ring",
        "category": "Clipboard",
        "description": "Maintain a rolling ring buffer of clipboard history.",
        "handler": "operations.clipboard_history_ring",
        "cli_command": "clipboard-history-ring",
        "dependencies": [
            "python:pyperclip"
        ]
    },
    {
        "name": "Clipboard Paste As Plain",
        "category": "Clipboard",
        "description": "Strip formatting and paste the clipboard as plain text.",
        "handler": "operations.clipboard_paste_as_plain",
        "cli_command": "clipboard-paste-plain",
        "dependencies": [
            "python:pyperclip"
        ]
    },
    {
        "name": "Clipboard Hash",
        "category": "Clipboard",
        "description": "Compute a hash of the current clipboard text.",
        "handler": "operations.clipboard_hash",
        "cli_command": "clipboard-hash",
        "dependencies": [
            "python:pyperclip"
        ]
    }
]
