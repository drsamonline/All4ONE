"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Ping Host",
        "category": "Advanced Networking",
        "description": "Ping Host: performs the ping host action with structured, human-readable output.",
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
        "description": "DNS Lookup: performs the dns lookup action with structured, human-readable output.",
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
        "description": "Reverse DNS: performs the reverse dns action with structured, human-readable output.",
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
        "description": "IP Address Info: performs the ip address info action with structured, human-readable output.",
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
        "description": "WHOIS Lookup: performs the whois lookup action with structured, human-readable output.",
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
        "description": "Route Trace: performs the route trace action with structured, human-readable output.",
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
        "description": "ARP Table Viewer: performs the arp table viewer action with structured, human-readable output.",
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
        "description": "Hosts File Viewer: performs the hosts file viewer action with structured, human-readable output.",
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
        "description": "Hosts File Entry Checker: performs the hosts file entry checker action with structured, human-readable output.",
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
        "description": "TCP Port Checker: performs the tcp port checker action with structured, human-readable output.",
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
        "description": "UDP Port Probe: performs the udp port probe action with structured, human-readable output.",
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
        "description": "HTTP Header Inspector: performs the http header inspector action with structured, human-readable output.",
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
        "description": "TLS Certificate Inspector: performs the tls certificate inspector action with structured, human-readable output.",
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
        "description": "URL Redirect Checker: performs the url redirect checker action with structured, human-readable output.",
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
        "description": "Local Listening Ports: performs the local listening ports action with structured, human-readable output.",
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
        "description": "Network Route Viewer: performs the network route viewer action with structured, human-readable output.",
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
        "description": "Subnet Calculator: performs the subnet calculator action with structured, human-readable output.",
        "handler": "operations.subnet_calculator",
        "cli_command": "subnet-calculator",
        "dependencies": []
    },
    {
        "name": "MAC Vendor Lookup",
        "category": "Networking",
        "description": "MAC Vendor Lookup: performs the mac vendor action with structured, human-readable output.",
        "handler": "operations.mac_vendor_lookup",
        "cli_command": "mac-vendor",
        "dependencies": []
    },
    {
        "name": "SSL Expiry Monitor",
        "category": "Networking",
        "description": "SSL Expiry Monitor: performs the ssl expiry action with structured, human-readable output.",
        "handler": "operations.ssl_expiry_monitor",
        "cli_command": "ssl-expiry",
        "dependencies": []
    },
    {
        "name": "Speed Test Probe",
        "category": "Networking",
        "description": "Speed Test Probe: performs the speed probe action with structured, human-readable output.",
        "handler": "operations.speed_test_probe",
        "cli_command": "speed-probe",
        "dependencies": []
    }
]
