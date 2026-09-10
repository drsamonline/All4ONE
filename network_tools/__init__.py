def register_tools():
    return [
        {
            "name": "Download Manager",
            "category": "Network Tools",
            "description": "Stream-download a URL to a local file.",
            "handler": "download.run",
            "cli_command": "download",
            "dependencies": [],
        },
        {
            "name": "HTTP Server",
            "category": "Network Tools",
            "description": "Serve a local folder over a threaded localhost HTTP server.",
            "handler": "http_server.run",
            "cli_command": "http-serve",
            "dependencies": [],
        },
        {
            "name": "FTP Client",
            "category": "Network Tools",
            "description": "Basic FTP upload/download client.",
            "handler": "ftp_client.run",
            "cli_command": "ftp",
            "dependencies": [],
        },
    ]
