def register_tools():
    return [
        {
            "name": "Zip Creator",
            "category": "Archive & Compression",
            "description": "Create a ZIP archive from a file or folder, with a selectable compression level.",
            "handler": "zip_tools.create_zip",
            "cli_command": "zip-create",
            "dependencies": [],
        },
        {
            "name": "Zip Extractor",
            "category": "Archive & Compression",
            "description": "Safely extract a ZIP archive, rejecting entries that would escape the destination (zip-slip safe).",
            "handler": "zip_tools.extract_zip",
            "cli_command": "zip-extract",
            "dependencies": [],
        },
        {
            "name": "Tar Creator",
            "category": "Archive & Compression",
            "description": "Create a compressed TAR archive (gzip, bzip2, xz or uncompressed).",
            "handler": "tar_tools.create_tar",
            "cli_command": "tar-create",
            "dependencies": [],
        },
        {
            "name": "Tar Extractor",
            "category": "Archive & Compression",
            "description": "Safely extract a TAR archive; skips symlinks, hardlinks and special files and blocks path traversal.",
            "handler": "tar_tools.extract_tar",
            "cli_command": "tar-extract",
            "dependencies": [],
        },
    ]
