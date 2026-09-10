def register_tools():
    return [
        {
            "name": "Image Thumbnail Generator",
            "category": "Multimedia",
            "description": "Generate optimized JPEG thumbnails using Pillow.",
            "handler": "thumbnails.run",
            "cli_command": "thumbnail",
            "dependencies": ["python:PIL"],
        },
        {
            "name": "Media Metadata Extractor",
            "category": "Multimedia",
            "description": "Extract streams and format metadata through ffprobe.",
            "handler": "media_info.run",
            "cli_command": "media-info",
            "dependencies": ["ffprobe"],
        },
        {
            "name": "Media Transcoder",
            "category": "Multimedia",
            "description": "Transcode audio/video through ffmpeg.",
            "handler": "transcode.run",
            "cli_command": "transcode",
            "dependencies": ["ffmpeg"],
        },
    ]
