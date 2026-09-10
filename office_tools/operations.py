"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "docx_metadata": "DOCX Metadata",
    "docx_text_extractor": "DOCX Text Extractor",
    "docx_paragraph_counter": "DOCX Paragraph Counter",
    "docx_heading_extractor": "DOCX Heading Extractor",
    "docx_image_inspector": "DOCX Image Inspector",
    "docx_structure_inspector": "DOCX Structure Inspector",
    "xlsx_metadata": "XLSX Metadata",
    "xlsx_sheet_lister": "XLSX Sheet Lister",
    "xlsx_cell_counter": "XLSX Cell Counter",
    "xlsx_formula_counter": "XLSX Formula Counter",
    "pptx_slide_counter": "PPTX Slide Counter",
    "office_file_inventory": "Office File Inventory",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
