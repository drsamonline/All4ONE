def register_tools():
    return [
        {
            "name": "File Encryptor",
            "category": "Security & Encryption",
            "description": "Encrypt a file with GnuPG for a given recipient (requires gpg).",
            "handler": "encrypt.run",
            "cli_command": "encrypt",
            "dependencies": ["gpg"],
        },
        {
            "name": "File Decryptor",
            "category": "Security & Encryption",
            "description": "Decrypt a GnuPG-encrypted file (requires gpg).",
            "handler": "encrypt.decrypt",
            "cli_command": "decrypt",
            "dependencies": ["gpg"],
        },
        {
            "name": "File Permissions Changer",
            "category": "Security & Encryption",
            "description": "Report or change file permissions (requires PowerShell on Windows).",
            "handler": "permissions.run",
            "cli_command": "permissions",
            "dependencies": [],
        },
        {
            "name": "File Integrity Baseline",
            "category": "Security & Encryption",
            "description": "Create or verify a SHA-256 integrity baseline for a file.",
            "handler": "integrity_baseline.run",
            "cli_command": "integrity-baseline",
            "dependencies": [],
        },
    ]
