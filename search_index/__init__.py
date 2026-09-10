def register_tools():
    return [
        {
            "name": "File Indexer",
            "category": "Search & Index",
            "description": "Build a fast SQLite/WAL file index for repeated searches.",
            "handler": "indexer.run",
            "cli_command": "index",
            "dependencies": [],
        },
        {
            "name": "Fast Search",
            "category": "Search & Index",
            "description": "Search indexed files by name, extension, and size.",
            "handler": "search.run",
            "cli_command": "search",
            "dependencies": [],
        },
        {
            "name": "Content Search",
            "category": "Search & Index",
            "description": "Search text content recursively with a regex-aware matcher.",
            "handler": "content_search.run",
            "cli_command": "grep",
            "dependencies": [],
        },
    ]
