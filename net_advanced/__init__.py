"""Auto-generated expansion plugin pack. All handlers are lazy and delegate to core operations."""


def register_tools():
    return [
    {
        "name": "Ping Host",
        "category": "Advanced Networking",
        "description": "Ping Host. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "DNS Lookup. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Reverse DNS. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "IP Address Info. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "WHOIS Lookup. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Route Trace. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "ARP Table Viewer. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Hosts File Viewer. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Hosts File Entry Checker. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "TCP Port Checker. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "UDP Port Probe. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "HTTP Header Inspector. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "TLS Certificate Inspector. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "URL Redirect Checker. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Local Listening Ports. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Network Route Viewer. Uses safe, dependency-aware execution with clear diagnostics.",
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
        "description": "Subnet Calculator. Subnet Calculator with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.subnet_calculator",
        "cli_command": "subnet-calculator",
        "dependencies": []
    },
    {
        "name": "MAC Vendor Lookup",
        "category": "Networking",
        "description": "MAC Vendor Lookup. Mac Vendor Lookup with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.mac_vendor_lookup",
        "cli_command": "mac-vendor",
        "dependencies": []
    },
    {
        "name": "SSL Expiry Monitor",
        "category": "Networking",
        "description": "SSL Expiry Monitor. Ssl Expiry Monitor with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.ssl_expiry_monitor",
        "cli_command": "ssl-expiry",
        "dependencies": []
    },
    {
        "name": "Speed Test Probe",
        "category": "Networking",
        "description": "Speed Test Probe. Speed Test Probe with safe, dependency-aware execution and clear diagnostics.",
        "handler": "operations.speed_test_probe",
        "cli_command": "speed-probe",
        "dependencies": []
    }
]
