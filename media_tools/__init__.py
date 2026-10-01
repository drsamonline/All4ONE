def register_tools():
    return [
        {
            "name": "Image Thumbnail Generator",
            "category": "Multimedia",
            "description": "Image Thumbnail Generator: image thumbnail generator as structured JSON output.",
            "handler": "thumbnails.run",
            "cli_command": "thumbnail",
            "dependencies": ["python:PIL"],
        },
        {
            "name": "Media Metadata Extractor",
            "category": "Multimedia",
            "description": "Media Metadata Extractor: media metadata extractor as structured JSON output.",
            "handler": "media_info.run",
            "cli_command": "media-info",
            "dependencies": ["ffprobe"],
        },
        {
            "name": "Media Transcoder",
            "category": "Multimedia",
            "description": "Media Transcoder: media transcoder as structured JSON output.",
            "handler": "transcode.run",
            "cli_command": "transcode",
            "dependencies": ["ffmpeg"],
        },
    ]
