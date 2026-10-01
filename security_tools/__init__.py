def register_tools():
    return [
        {
            "name": "File Encryptor",
            "category": "Security & Encryption",
            "description": "File Encryptor: file encryptor as structured JSON output.",
            "handler": "encrypt.run",
            "cli_command": "encrypt",
            "dependencies": ["gpg"],
        },
        {
            "name": "File Decryptor",
            "category": "Security & Encryption",
            "description": "File Decryptor: file decryptor as structured JSON output.",
            "handler": "encrypt.decrypt",
            "cli_command": "decrypt",
            "dependencies": ["gpg"],
        },
        {
            "name": "File Permissions Changer",
            "category": "Security & Encryption",
            "description": "File Permissions Changer: file permissions changer as structured JSON output.",
            "handler": "permissions.run",
            "cli_command": "permissions",
            "dependencies": [],
        },
        {
            "name": "File Integrity Baseline",
            "category": "Security & Encryption",
            "description": "File Integrity Baseline: file integrity baseline as structured JSON output.",
            "handler": "integrity_baseline.run",
            "cli_command": "integrity-baseline",
            "dependencies": [],
        },
    ]
