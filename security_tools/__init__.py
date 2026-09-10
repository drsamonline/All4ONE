def register_tools():
    return [
        {
            "name": "File Encryptor",
            "category": "Security & Encryption",
            "description": "Encrypt a file with a GnuPG recipient key.",
            "handler": "encrypt.run",
            "cli_command": "encrypt",
            "dependencies": ["gpg"],
        },
        {
            "name": "File Decryptor",
            "category": "Security & Encryption",
            "description": "Decrypt a GnuPG-encrypted file.",
            "handler": "encrypt.decrypt",
            "cli_command": "decrypt",
            "dependencies": ["gpg"],
        },
        {
            "name": "File Permissions Changer",
            "category": "Security & Encryption",
            "description": "Inspect POSIX permissions or set an octal mode; Windows uses attrib for read-only changes.",
            "handler": "permissions.run",
            "cli_command": "permissions",
            "dependencies": [],
        },
        {
            "name": "File Integrity Baseline",
            "category": "Security & Encryption",
            "description": "Create a SHA-256 integrity baseline for a file.",
            "handler": "integrity_baseline.run",
            "cli_command": "integrity-baseline",
            "dependencies": [],
        },
    ]
