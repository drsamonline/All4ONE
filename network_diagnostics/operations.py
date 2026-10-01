"""Lazy operation adapters; implementations live in core.extended_ops."""

from core.handler_factory import make_handler

_HANDLERS = {
    "network_adapter_list": "Network Adapter List",
    "network_adapter_details": "Network Adapter Details",
    "ipv4_configuration": "IPv4 Configuration",
    "ipv6_configuration": "IPv6 Configuration",
    "dns_server_list": "DNS Server List",
    "default_gateway": "Default Gateway",
    "dhcp_status": "DHCP Status",
    "mac_address_viewer": "MAC Address Viewer",
    "connection_test": "Connection Test",
    "http_connectivity_test": "HTTP Connectivity Test",
    "https_connectivity_test": "HTTPS Connectivity Test",
    "dns_connectivity_test": "DNS Connectivity Test",
    "internet_reachability": "Internet Reachability",
    "latency_test": "Latency Test",
    "packet_loss_test": "Packet Loss Test",
    "proxy_configuration": "Proxy Configuration",
    "winhttp_proxy_viewer": "WinHTTP Proxy Viewer",
    "network_diagnostics_bundle": "Network Diagnostics Bundle",
}


def __getattr__(name: str):
    operation = _HANDLERS.get(name)
    if operation is None:
        raise AttributeError(name)
    handler = make_handler(operation)
    globals()[name] = handler
    return handler


__all__ = tuple(_HANDLERS)
