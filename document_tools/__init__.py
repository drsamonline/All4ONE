def register_tools():
    return [
        {
            "name": "Line/Word Counter",
            "category": "Document & Text",
            "description": "Line/Word Counter: line/word counter as structured JSON output.",
            "handler": "counter.run",
            "cli_command": "count",
            "dependencies": [],
        },
        {
            "name": "PDF Text Extractor",
            "category": "Document & Text",
            "description": "PDF Text Extractor: pdf text extractor as structured JSON output.",
            "handler": "pdf_extract.run",
            "cli_command": "pdf-text",
            "dependencies": ["pdftotext"],
        },
        {
            "name": "Encoding Converter",
            "category": "Document & Text",
            "description": "Encoding Converter: encoding converter as structured JSON output.",
            "handler": "encoding.run",
            "cli_command": "encoding",
            "dependencies": [],
        },
    ]
