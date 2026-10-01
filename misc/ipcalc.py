"""IPv4 subnet calculator built on the stdlib ipaddress module."""
from __future__ import annotations

import argparse
import ipaddress


def run(args=None):
    p = argparse.ArgumentParser(description="Compute network details for an IPv4 address/CIDR.")
    p.add_argument("cidr", nargs="?", help="Address or network, e.g. 192.168.1.10/24 (omit for --classless host).")
    p.add_argument("--mask", metavar="NETMASK", help="Dotted netmask instead of CIDR prefix, e.g. 255.255.255.0.")
    p.add_argument("--hosts-limit", type=int, default=10, metavar="N",
                   help="How many usable host addresses to list (0 = none).")
    a = p.parse_args(args or [])

    if not a.cidr:
        print("Provide an address/network, e.g. 'ipcalc 192.168.1.10/24'.")
        return 2

    spec = a.cidr
    if a.mask:
        try:
            prefix = ipaddress.IPv4Network(f"0.0.0.0/{a.mask}").prefixlen
        except ValueError as exc:
            print(f"Invalid netmask: {exc}")
            return 1
        spec = f"{a.cidr.split('/')[0]}/{prefix}"

    try:
        iface = ipaddress.IPv4Interface(spec)
    except ValueError as exc:
        print(f"Invalid input: {exc}")
        return 1

    net = iface.network
    info = [
        ("Address", str(iface.ip)),
        ("Netmask", str(net.netmask)),
        ("CIDR", f"/{net.prefixlen}"),
        ("Network", str(net.network_address)),
        ("Broadcast", str(net.broadcast_address)),
        ("Hosts total", str(max(net.num_addresses - 2, 0) if net.prefixlen < 31 else net.num_addresses)),
        ("Wildcard", str(net.hostmask)),
        ("Private", str(net.is_private)),
    ]
    width = max(len(k) for k, _ in info)
    for k, v in info:
        print(f"{k.ljust(width)} : {v}")

    if a.hosts_limit > 0 and net.prefixlen <= 30:
        hosts = net.hosts() if hasattr(net, "iter_hosts") else list(net)[1:-1]
        shown = hosts[: a.hosts_limit]
        print(f"First hosts   : {', '.join(map(str, shown))}"
              + (f" ... ({len(hosts) - len(shown)} more)" if len(hosts) > len(shown) else ""))
    return 0
