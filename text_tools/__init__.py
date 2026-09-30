"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Whitespace Cleaner",
        "category": "Text Processing",
        "description": "Clean up whitespace.",
        "handler": "operations.whitespace_cleaner",
        "cli_command": "whitespace-cleaner",
        "dependencies": []
    },
    {
        "name": "Blank Line Cleaner",
        "category": "Text Processing",
        "description": "Clean up blank line.",
        "handler": "operations.blank_line_cleaner",
        "cli_command": "blank-line-cleaner",
        "dependencies": []
    },
    {
        "name": "Trailing Space Cleaner",
        "category": "Text Processing",
        "description": "Clean up trailing space.",
        "handler": "operations.trailing_space_cleaner",
        "cli_command": "trailing-space-cleaner",
        "dependencies": []
    },
    {
        "name": "Indentation Normalizer",
        "category": "Text Processing",
        "description": "Normalize indentation to a canonical form.",
        "handler": "operations.indentation_normalizer",
        "cli_command": "indentation-normalizer",
        "dependencies": []
    },
    {
        "name": "Case Converter",
        "category": "Text Processing",
        "description": "Convert text to upper, lower, or swapped case.",
        "handler": "operations.case_converter",
        "cli_command": "case-converter",
        "dependencies": []
    },
    {
        "name": "Title Case Converter",
        "category": "Text Processing",
        "description": "Capitalize the first letter of every word (Title Case).",
        "handler": "operations.title_case_converter",
        "cli_command": "title-case-converter",
        "dependencies": []
    },
    {
        "name": "Snake Case Converter",
        "category": "Text Processing",
        "description": "Convert text words into snake_case identifiers.",
        "handler": "operations.snake_case_converter",
        "cli_command": "snake-case-converter",
        "dependencies": []
    },
    {
        "name": "Kebab Case Converter",
        "category": "Text Processing",
        "description": "Convert text words into kebab-case slugs.",
        "handler": "operations.kebab_case_converter",
        "cli_command": "kebab-case-converter",
        "dependencies": []
    },
    {
        "name": "Camel Case Converter",
        "category": "Text Processing",
        "description": "Convert text words into camelCase identifiers.",
        "handler": "operations.camel_case_converter",
        "cli_command": "camel-case-converter",
        "dependencies": []
    },
    {
        "name": "Text Deduplicator",
        "category": "Text Processing",
        "description": "Text Deduplicator: query and display text deduplicator details as structured JSON.",
        "handler": "operations.text_deduplicator",
        "cli_command": "text-deduplicator",
        "dependencies": []
    },
    {
        "name": "Text Sorter",
        "category": "Text Processing",
        "description": "Sort text records.",
        "handler": "operations.text_sorter",
        "cli_command": "text-sorter",
        "dependencies": []
    },
    {
        "name": "Text Reverse",
        "category": "Text Processing",
        "description": "Text Reverse: query and display text reverse details as structured JSON.",
        "handler": "operations.text_reverse",
        "cli_command": "text-reverse",
        "dependencies": []
    },
    {
        "name": "Text Wrap",
        "category": "Text Processing",
        "description": "Text Wrap: query and display text wrap details as structured JSON.",
        "handler": "operations.text_wrap",
        "cli_command": "text-wrap",
        "dependencies": []
    },
    {
        "name": "Text Unwrap",
        "category": "Text Processing",
        "description": "Text Unwrap: query and display text unwrap details as structured JSON.",
        "handler": "operations.text_unwrap",
        "cli_command": "text-unwrap",
        "dependencies": []
    },
    {
        "name": "Character Frequency",
        "category": "Text Processing",
        "description": "Character Frequency: query and display character frequency details as structured JSON.",
        "handler": "operations.character_frequency",
        "cli_command": "character-frequency",
        "dependencies": []
    },
    {
        "name": "Word Frequency",
        "category": "Text Processing",
        "description": "Word Frequency: query and display word frequency details as structured JSON.",
        "handler": "operations.word_frequency",
        "cli_command": "word-frequency",
        "dependencies": []
    },
    {
        "name": "Ngram Counter",
        "category": "Text Processing",
        "description": "Count occurrences within ngram.",
        "handler": "operations.ngram_counter",
        "cli_command": "ngram-counter",
        "dependencies": []
    },
    {
        "name": "Sentence Counter",
        "category": "Text Processing",
        "description": "Count occurrences within sentence.",
        "handler": "operations.sentence_counter",
        "cli_command": "sentence-counter",
        "dependencies": []
    },
    {
        "name": "Slugify Converter",
        "category": "Text Processing",
        "description": "Turn any title or sentence into a URL-safe lowercase slug.",
        "handler": "operations.slugify_converter",
        "cli_command": "slugify-converter",
        "dependencies": []
    },
    {
        "name": "Regex Replacer",
        "category": "Text Processing",
        "description": "Regex Replacer: query and display regex replacer details as structured JSON.",
        "handler": "operations.regex_replacer",
        "cli_command": "regex-replacer",
        "dependencies": []
    },
    {
        "name": "Markdown Table Formatter",
        "category": "Text Processing",
        "description": "Reformat markdown table to a clean layout.",
        "handler": "operations.markdown_table_formatter",
        "cli_command": "markdown-table-formatter",
        "dependencies": []
    },
    {
        "name": "Line Number Prefixer",
        "category": "Text Processing",
        "description": "Line Number Prefixer: query and display line number prefixer details as structured JSON.",
        "handler": "operations.line_number_prefixer",
        "cli_command": "line-number-prefixer",
        "dependencies": []
    },
    {
        "name": "Unicode Normalizer",
        "category": "Text Processing",
        "description": "Normalize unicode to a canonical form.",
        "handler": "operations.unicode_normalizer",
        "cli_command": "unicode-normalizer",
        "dependencies": []
    }
]
