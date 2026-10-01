"""Lazy operation adapters; implementations live in core.extended_ops."""


from core.handler_factory import make_handler

_HANDLERS = {
    "clipboard_read": "Clipboard Read",
    "clipboard_write": "Clipboard Write",
    "clipboard_clear": "Clipboard Clear",
    "clipboard_append": "Clipboard Append",
    "clipboard_text_length": "Clipboard Text Length",
    "clipboard_word_count": "Clipboard Word Count",
    "clipboard_line_count": "Clipboard Line Count",
    "clipboard_save": "Clipboard Save",
    "clipboard_load": "Clipboard Load",
    "clipboard_normalize": "Clipboard Normalize",
    "clipboard_history_ring": "clipboard history ring",
    "clipboard_paste_as_plain": "clipboard paste as plain",
    "clipboard_hash": "clipboard hash",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
