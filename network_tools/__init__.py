def register_tools():
    return [
        {
            "name": "Download Manager",
            "category": "Network Tools",
            "description": "Download a URL to a file using streaming I/O.",
            "handler": "download.run",
            "cli_command": "download",
            "dependencies": [],
        },
        {
            "name": "HTTP Server",
            "category": "Network Tools",
            "description": "Serve a local directory over HTTP on 127.0.0.1.",
            "handler": "http_server.run",
            "cli_command": "http-serve",
            "dependencies": [],
        },
        {
            "name": "FTP Client",
            "category": "Network Tools",
            "description": "Upload or download a file over FTP.",
            "handler": "ftp_client.run",
            "cli_command": "ftp",
            "dependencies": [],
        },
    ]
