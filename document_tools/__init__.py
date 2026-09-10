def register_tools():
    return [
        {
            "name": "Line/Word Counter",
            "category": "Document & Text",
            "description": "Count characters, words, and lines in text.",
            "handler": "counter.run",
            "cli_command": "count",
            "dependencies": [],
        },
        {
            "name": "PDF Text Extractor",
            "category": "Document & Text",
            "description": "Extract PDF text with pdftotext when installed.",
            "handler": "pdf_extract.run",
            "cli_command": "pdf-text",
            "dependencies": ["pdftotext"],
        },
        {
            "name": "Encoding Converter",
            "category": "Document & Text",
            "description": "Convert text files between character encodings.",
            "handler": "encoding.run",
            "cli_command": "encoding",
            "dependencies": [],
        },
    ]
