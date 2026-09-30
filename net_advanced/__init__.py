"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Ping Host",
        "category": "Advanced Networking",
        "description": "Ping Host: run the 'ping host' operation and print structured JSON results.",
        "handler": "operations.ping_host",
        "cli_command": "ping-host",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "DNS Lookup",
        "category": "Advanced Networking",
        "description": "Ping Host: run the 'ping host' operation and print structured JSON results.",
        "handler": "operations.dns_lookup",
        "cli_command": "dns-lookup",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Reverse DNS",
        "category": "Advanced Networking",
        "description": "DNS Lookup: run the 'dns lookup' operation and print structured JSON results.",
        "handler": "operations.reverse_dns",
        "cli_command": "reverse-dns",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "IP Address Info",
        "category": "Advanced Networking",
        "description": "Reverse DNS: run the 'reverse dns' operation and print structured JSON results.",
        "handler": "operations.ip_address_info",
        "cli_command": "ip-address-info",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "WHOIS Lookup",
        "category": "Advanced Networking",
        "description": "Show ip address information.",
        "handler": "operations.whois_lookup",
        "cli_command": "whois-lookup",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Route Trace",
        "category": "Advanced Networking",
        "description": "WHOIS Lookup: run the 'whois lookup' operation and print structured JSON results.",
        "handler": "operations.route_trace",
        "cli_command": "route-trace",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "ARP Table Viewer",
        "category": "Advanced Networking",
        "description": "Display the contents of arp table.",
        "handler": "operations.arp_table_viewer",
        "cli_command": "arp-table-viewer",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Hosts File Viewer",
        "category": "Advanced Networking",
        "description": "Display the contents of hosts file.",
        "handler": "operations.hosts_file_viewer",
        "cli_command": "hosts-file-viewer",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Hosts File Entry Checker",
        "category": "Advanced Networking",
        "description": "Check and validate hosts file entry.",
        "handler": "operations.hosts_file_entry_checker",
        "cli_command": "hosts-file-entry-checker",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "TCP Port Checker",
        "category": "Advanced Networking",
        "description": "Check and validate tcp port.",
        "handler": "operations.tcp_port_checker",
        "cli_command": "tcp-port-checker",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "UDP Port Probe",
        "category": "Advanced Networking",
        "description": "Check and validate tcp port.",
        "handler": "operations.udp_port_probe",
        "cli_command": "udp-port-probe",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "HTTP Header Inspector",
        "category": "Advanced Networking",
        "description": "Inspect http header and report internals.",
        "handler": "operations.http_header_inspector",
        "cli_command": "http-header-inspector",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "TLS Certificate Inspector",
        "category": "Advanced Networking",
        "description": "Inspect tls certificate and report internals.",
        "handler": "operations.tls_certificate_inspector",
        "cli_command": "tls-certificate-inspector",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "URL Redirect Checker",
        "category": "Advanced Networking",
        "description": "Check and validate url redirect.",
        "handler": "operations.url_redirect_checker",
        "cli_command": "url-redirect-checker",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Local Listening Ports",
        "category": "Advanced Networking",
        "description": "Check and validate url redirect.",
        "handler": "operations.local_listening_ports",
        "cli_command": "local-listening-ports",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Network Route Viewer",
        "category": "Advanced Networking",
        "description": "Display the contents of network route.",
        "handler": "operations.network_route_viewer",
        "cli_command": "network-route-viewer",
        "dependencies": [
            "ping",
            "nslookup"
        ]
    },
    {
        "name": "Subnet Calculator",
        "category": "Networking",
        "description": "Compute subnet values.",
        "handler": "operations.subnet_calculator",
        "cli_command": "subnet-calculator",
        "dependencies": []
    },
    {
        "name": "MAC Vendor Lookup",
        "category": "Networking",
        "description": "Compute subnet values.",
        "handler": "operations.mac_vendor_lookup",
        "cli_command": "mac-vendor",
        "dependencies": []
    },
    {
        "name": "SSL Expiry Monitor",
        "category": "Networking",
        "description": "Monitor ssl expiry over time.",
        "handler": "operations.ssl_expiry_monitor",
        "cli_command": "ssl-expiry",
        "dependencies": []
    },
    {
        "name": "Speed Test Probe",
        "category": "Networking",
        "description": "Monitor ssl expiry over time.",
        "handler": "operations.speed_test_probe",
        "cli_command": "speed-probe",
        "dependencies": []
    }
]
