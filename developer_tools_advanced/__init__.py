"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Python Syntax Checker",
        "category": "Advanced Developer Tools",
        "description": "Compile a Python file to check it for syntax errors.",
        "handler": "operations.python_syntax_checker",
        "cli_command": "python-syntax-checker",
        "dependencies": []
    },
    {
        "name": "Python Import Checker",
        "category": "Advanced Developer Tools",
        "description": "Check that a Python file's imports resolve.",
        "handler": "operations.python_import_checker",
        "cli_command": "python-import-checker",
        "dependencies": []
    },
    {
        "name": "JSON Schema-Lite Validator",
        "category": "Advanced Developer Tools",
        "description": "Validate a JSON document against a compact, dependency-free schema.",
        "handler": "operations.json_schema_lite_validator",
        "cli_command": "json-schema-lite-validator",
        "dependencies": []
    },
    {
        "name": "YAML Structure Checker",
        "category": "Advanced Developer Tools",
        "description": "Parse a YAML file and report its structure or any errors.",
        "handler": "operations.yaml_structure_checker",
        "cli_command": "yaml-structure-checker",
        "dependencies": []
    },
    {
        "name": "TOML Structure Checker",
        "category": "Advanced Developer Tools",
        "description": "Parse a TOML file and report its structure or any errors.",
        "handler": "operations.toml_structure_checker",
        "cli_command": "toml-structure-checker",
        "dependencies": []
    },
    {
        "name": "Regex Tester",
        "category": "Advanced Developer Tools",
        "description": "Test a regular expression against sample text and show the matches.",
        "handler": "operations.regex_tester",
        "cli_command": "regex-tester",
        "dependencies": []
    },
    {
        "name": "Diff Text Files",
        "category": "Advanced Developer Tools",
        "description": "Show a unified diff between two text files.",
        "handler": "operations.diff_text_files",
        "cli_command": "diff-text-files",
        "dependencies": []
    },
    {
        "name": "Patch Preview",
        "category": "Advanced Developer Tools",
        "description": "Show how a patch would change a file before you apply it.",
        "handler": "operations.patch_preview",
        "cli_command": "patch-preview",
        "dependencies": []
    },
    {
        "name": "Line Ending Detector",
        "category": "Advanced Developer Tools",
        "description": "Detect whether a text file uses CRLF, LF or CR line endings.",
        "handler": "operations.line_ending_detector",
        "cli_command": "line-ending-detector",
        "dependencies": []
    },
    {
        "name": "Indentation Analyzer",
        "category": "Advanced Developer Tools",
        "description": "Report a file's indentation style, tabs versus spaces, and consistency.",
        "handler": "operations.indentation_analyzer",
        "cli_command": "indentation-analyzer",
        "dependencies": []
    },
    {
        "name": "Encoding Detector",
        "category": "Advanced Developer Tools",
        "description": "Detect the likely character encoding of a file.",
        "handler": "operations.encoding_detector",
        "cli_command": "encoding-detector",
        "dependencies": []
    },
    {
        "name": "Base64 Encoder",
        "category": "Advanced Developer Tools",
        "description": "Base64-encode text or a file.",
        "handler": "operations.base64_encoder",
        "cli_command": "base64-encoder",
        "dependencies": []
    },
    {
        "name": "Base64 Decoder",
        "category": "Advanced Developer Tools",
        "description": "Base64-decode text or a file back to its original bytes.",
        "handler": "operations.base64_decoder",
        "cli_command": "base64-decoder",
        "dependencies": []
    },
    {
        "name": "URL Encoder",
        "category": "Advanced Developer Tools",
        "description": "Percent-encode a string so it is safe inside a URL.",
        "handler": "operations.url_encoder",
        "cli_command": "url-encoder",
        "dependencies": []
    },
    {
        "name": "URL Decoder",
        "category": "Advanced Developer Tools",
        "description": "Decode percent-encoded characters in a URL back to plain text.",
        "handler": "operations.url_decoder",
        "cli_command": "url-decoder",
        "dependencies": []
    },
    {
        "name": "UUID Generator",
        "category": "Advanced Developer Tools",
        "description": "Generate one or more RFC 4122 UUIDs.",
        "handler": "operations.uuid_generator",
        "cli_command": "uuid-generator",
        "dependencies": []
    },
    {
        "name": "Hash Calculator",
        "category": "Advanced Developer Tools",
        "description": "Compute MD5, SHA-1, SHA-256 or SHA-512 digests for text or files.",
        "handler": "operations.hash_calculator",
        "cli_command": "hash-calculator",
        "dependencies": []
    },
    {
        "name": "HMAC Calculator",
        "category": "Advanced Developer Tools",
        "description": "Compute an HMAC signature for a message with a given key.",
        "handler": "operations.hmac_calculator",
        "cli_command": "hmac-calculator",
        "dependencies": []
    },
    {
        "name": "Semantic Version Comparator",
        "category": "Advanced Developer Tools",
        "description": "Compare semantic version inputs.",
        "handler": "operations.semantic_version_comparator",
        "cli_command": "semantic-version-comparator",
        "dependencies": []
    },
    {
        "name": "Version Bump Helper",
        "category": "Advanced Developer Tools",
        "description": "Assist with version bump tasks.",
        "handler": "operations.version_bump_helper",
        "cli_command": "version-bump-helper",
        "dependencies": []
    },
    {
        "name": "Multi Algorithm Hasher",
        "category": "Advanced Developer Tools",
        "description": "Compute several hash algorithms at once for a file or text.",
        "handler": "operations.multi_algorithm_hasher",
        "cli_command": "multi-hash",
        "dependencies": []
    },
    {
        "name": "Checksum Verifier",
        "category": "Advanced Developer Tools",
        "description": "Verify a file against an expected checksum.",
        "handler": "operations.checksum_verifier",
        "cli_command": "checksum-verify",
        "dependencies": []
    },
    {
        "name": "Base64 File Codec",
        "category": "Advanced Developer Tools",
        "description": "Base64-encode or decode a file.",
        "handler": "operations.base64_file_codec",
        "cli_command": "b64-file",
        "dependencies": []
    },
    {
        "name": "Hex Codec",
        "category": "Advanced Developer Tools",
        "description": "Encode or decode hex strings and files.",
        "handler": "operations.hex_codec",
        "cli_command": "hex-codec",
        "dependencies": []
    },
    {
        "name": "Charset Detector",
        "category": "Advanced Developer Tools",
        "description": "Detect the character set of a byte stream.",
        "handler": "operations.charset_detector",
        "cli_command": "charset-detect",
        "dependencies": []
    },
    {
        "name": "BOM Handler",
        "category": "Advanced Developer Tools",
        "description": "Detect or strip a byte-order mark from a text file.",
        "handler": "operations.bom_handler",
        "cli_command": "bom-handler",
        "dependencies": []
    }
]
