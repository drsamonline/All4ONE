"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "whitespace_cleaner": "Whitespace Cleaner",
    "blank_line_cleaner": "Blank Line Cleaner",
    "trailing_space_cleaner": "Trailing Space Cleaner",
    "indentation_normalizer": "Indentation Normalizer",
    "case_converter": "Case Converter",
    "title_case_converter": "Title Case Converter",
    "snake_case_converter": "Snake Case Converter",
    "kebab_case_converter": "Kebab Case Converter",
    "camel_case_converter": "Camel Case Converter",
    "text_deduplicator": "Text Deduplicator",
    "text_sorter": "Text Sorter",
    "text_reverse": "Text Reverse",
    "text_wrap": "Text Wrap",
    "text_unwrap": "Text Unwrap",
    "character_frequency": "Character Frequency",
    "word_frequency": "Word Frequency",
    "ngram_counter": "Ngram Counter",
    "sentence_counter": "Sentence Counter",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
