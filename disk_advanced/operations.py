"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "drive_information": "Drive Information",
    "volume_list": "Volume List",
    "partition_information": "Partition Information",
    "disk_free_space": "Disk Free Space",
    "disk_usage_top_files": "Disk Usage Top Files",
    "directory_size_tree": "Directory Size Tree",
    "sparse_file_inspector": "Sparse File Inspector",
    "file_allocation_inspector": "File Allocation Inspector",
    "disk_benchmark_reader": "Disk Benchmark Reader",
    "smart_status": "SMART Status",
    "mount_point_viewer": "Mount Point Viewer",
    "volume_serial_reader": "Volume Serial Reader",
    "ntfs_alternate_stream_finder": "NTFS Alternate Stream Finder",
    "large_file_finder": "Large File Finder",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
