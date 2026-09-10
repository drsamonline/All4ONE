"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "ping_host": "Ping Host",
    "dns_lookup": "DNS Lookup",
    "reverse_dns": "Reverse DNS",
    "ip_address_info": "IP Address Info",
    "whois_lookup": "WHOIS Lookup",
    "route_trace": "Route Trace",
    "arp_table_viewer": "ARP Table Viewer",
    "hosts_file_viewer": "Hosts File Viewer",
    "hosts_file_entry_checker": "Hosts File Entry Checker",
    "tcp_port_checker": "TCP Port Checker",
    "udp_port_probe": "UDP Port Probe",
    "http_header_inspector": "HTTP Header Inspector",
    "tls_certificate_inspector": "TLS Certificate Inspector",
    "url_redirect_checker": "URL Redirect Checker",
    "local_listening_ports": "Local Listening Ports",
    "network_route_viewer": "Network Route Viewer",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
