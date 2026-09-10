"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "python_syntax_checker": "Python Syntax Checker",
    "python_import_checker": "Python Import Checker",
    "json_schema_lite_validator": "JSON Schema-Lite Validator",
    "yaml_structure_checker": "YAML Structure Checker",
    "toml_structure_checker": "TOML Structure Checker",
    "regex_tester": "Regex Tester",
    "diff_text_files": "Diff Text Files",
    "patch_preview": "Patch Preview",
    "line_ending_detector": "Line Ending Detector",
    "indentation_analyzer": "Indentation Analyzer",
    "encoding_detector": "Encoding Detector",
    "base64_encoder": "Base64 Encoder",
    "base64_decoder": "Base64 Decoder",
    "url_encoder": "URL Encoder",
    "url_decoder": "URL Decoder",
    "uuid_generator": "UUID Generator",
    "hash_calculator": "Hash Calculator",
    "hmac_calculator": "HMAC Calculator",
    "semantic_version_comparator": "Semantic Version Comparator",
    "version_bump_helper": "Version Bump Helper",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
