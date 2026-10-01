"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "pdf_metadata_reader": "PDF Metadata Reader",
    "pdf_metadata_cleaner": "PDF Metadata Cleaner",
    "pdf_page_counter": "PDF Page Counter",
    "pdf_text_search": "PDF Text Search",
    "pdf_page_extractor": "PDF Page Extractor",
    "pdf_merge": "PDF Merge",
    "pdf_split": "PDF Split",
    "pdf_rotate": "PDF Rotate",
    "pdf_compress": "PDF Compress",
    "pdf_watermark": "PDF Watermark",
    "pdf_image_extractor": "PDF Image Extractor",
    "pdf_attachment_inspector": "PDF Attachment Inspector",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
