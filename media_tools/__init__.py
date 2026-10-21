def register_tools():
    return [
        {
            "name": "Image Thumbnail Generator",
            "category": "Multimedia",
            "description": "Generate a thumbnail image for a picture or video (requires Pillow).",
            "handler": "thumbnails.run",
            "cli_command": "thumbnail",
            "dependencies": ["python:PIL"],
        },
        {
            "name": "Media Metadata Extractor",
            "category": "Multimedia",
            "description": "Read container, codec and stream metadata from a media file (requires ffprobe).",
            "handler": "media_info.run",
            "cli_command": "media-info",
            "dependencies": ["ffprobe"],
        },
        {
            "name": "Media Transcoder",
            "category": "Multimedia",
            "description": "Convert a media file to another format (requires ffmpeg).",
            "handler": "transcode.run",
            "cli_command": "transcode",
            "dependencies": ["ffmpeg"],
        },
    ]
