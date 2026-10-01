def register_tools():
    return [
        {
            "name": "Download Manager",
            "category": "Network Tools",
            "description": "Download Manager: download manager as structured JSON output.",
            "handler": "download.run",
            "cli_command": "download",
            "dependencies": [],
        },
        {
            "name": "HTTP Server",
            "category": "Network Tools",
            "description": "HTTP Server: http server as structured JSON output.",
            "handler": "http_server.run",
            "cli_command": "http-serve",
            "dependencies": [],
        },
        {
            "name": "FTP Client",
            "category": "Network Tools",
            "description": "FTP Client: ftp client as structured JSON output.",
            "handler": "ftp_client.run",
            "cli_command": "ftp",
            "dependencies": [],
        },
    ]
