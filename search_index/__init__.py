def register_tools():
    return [
        {
            "name": "File Indexer",
            "category": "Search & Index",
            "description": "Build a searchable index of a directory tree (SQLite-backed).",
            "handler": "indexer.run",
            "cli_command": "index",
            "dependencies": [],
        },
        {
            "name": "Fast Search",
            "category": "Search & Index",
            "description": "Search the index by filename.",
            "handler": "search.run",
            "cli_command": "search",
            "dependencies": [],
        },
        {
            "name": "Content Search",
            "category": "Search & Index",
            "description": "Search file contents for a pattern.",
            "handler": "content_search.run",
            "cli_command": "grep",
            "dependencies": [],
        },
    ]
