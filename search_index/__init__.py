def register_tools():
    return [
        {
            "name": "File Indexer",
            "category": "Search & Index",
            "description": "File Indexer: file indexer as structured JSON output.",
            "handler": "indexer.run",
            "cli_command": "index",
            "dependencies": [],
        },
        {
            "name": "Fast Search",
            "category": "Search & Index",
            "description": "Fast Search: fast search as structured JSON output.",
            "handler": "search.run",
            "cli_command": "search",
            "dependencies": [],
        },
        {
            "name": "Content Search",
            "category": "Search & Index",
            "description": "Content Search: content search as structured JSON output.",
            "handler": "content_search.run",
            "cli_command": "grep",
            "dependencies": [],
        },
    ]
