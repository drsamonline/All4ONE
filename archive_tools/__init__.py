def register_tools():
    return [
        {
            "name": "Zip Creator",
            "category": "Archive & Compression",
            "description": "Create deflated ZIP archives with configurable compression.",
            "handler": "zip_tools.create_zip",
            "cli_command": "zip-create",
            "dependencies": [],
        },
        {
            "name": "Zip Extractor",
            "category": "Archive & Compression",
            "description": "Extract ZIP archives with path-traversal protection.",
            "handler": "zip_tools.extract_zip",
            "cli_command": "zip-extract",
            "dependencies": [],
        },
        {
            "name": "Tar Creator",
            "category": "Archive & Compression",
            "description": "Create plain, gzip, bzip2, or xz TAR archives.",
            "handler": "tar_tools.create_tar",
            "cli_command": "tar-create",
            "dependencies": [],
        },
        {
            "name": "Tar Extractor",
            "category": "Archive & Compression",
            "description": "Safely extract TAR archives while blocking symlinks and traversal.",
            "handler": "tar_tools.extract_tar",
            "cli_command": "tar-extract",
            "dependencies": [],
        },
    ]
