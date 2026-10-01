def register_tools():
    return [
        {
            "name": "Zip Creator",
            "category": "Archive & Compression",
            "description": "Zip Creator: zip creator as structured JSON output.",
            "handler": "zip_tools.create_zip",
            "cli_command": "zip-create",
            "dependencies": [],
        },
        {
            "name": "Zip Extractor",
            "category": "Archive & Compression",
            "description": "Zip Extractor: zip extractor as structured JSON output.",
            "handler": "zip_tools.extract_zip",
            "cli_command": "zip-extract",
            "dependencies": [],
        },
        {
            "name": "Tar Creator",
            "category": "Archive & Compression",
            "description": "Tar Creator: tar creator as structured JSON output.",
            "handler": "tar_tools.create_tar",
            "cli_command": "tar-create",
            "dependencies": [],
        },
        {
            "name": "Tar Extractor",
            "category": "Archive & Compression",
            "description": "Tar Extractor: tar extractor as structured JSON output.",
            "handler": "tar_tools.extract_tar",
            "cli_command": "tar-extract",
            "dependencies": [],
        },
    ]
