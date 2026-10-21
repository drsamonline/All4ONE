def register_tools():
    return [
        {
            "name": "Line/Word Counter",
            "category": "Document & Text",
            "description": "Count lines, words and characters in a text file.",
            "handler": "counter.run",
            "cli_command": "count",
            "dependencies": [],
        },
        {
            "name": "PDF Text Extractor",
            "category": "Document & Text",
            "description": "Extract text from a PDF (requires pdftotext).",
            "handler": "pdf_extract.run",
            "cli_command": "pdf-text",
            "dependencies": ["pdftotext"],
        },
        {
            "name": "Encoding Converter",
            "category": "Document & Text",
            "description": "Convert a text file between encodings.",
            "handler": "encoding.run",
            "cli_command": "encoding",
            "dependencies": [],
        },
    ]
