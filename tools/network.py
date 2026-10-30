"""Network — addresses, DNS, ports, HTTP and certificates."""

from __future__ import annotations

import ipaddress
import json
import platform
import re
import socket
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import human_size, out_path, report_table, run_command, which

WINDOWS = platform.system() == "Windows"
UA = "Mozilla/5.0 (compatible; All4one/4.0)"


# --------------------------------------------------------------------------
# IP maths
# --------------------------------------------------------------------------
@tool(id="ip-calc", name="Subnet Calculator", category="Network",
      summary="Everything about a CIDR: mask, network, broadcast, usable host range and count.",
      keywords="subnet cidr ip mask network broadcast hosts calculator",
      fields=[F.text("cidr", "Address / prefix", "192.168.1.10/24", required=True)])
def ip_calc(v, ctx):
    raw = v["cidr"].strip()
    try:
        interface = ipaddress.ip_interface(raw)
    except ValueError:
        try:
            network = ipaddress.ip_network(raw, strict=False)
            interface = ipaddress.ip_interface(f"{network.network_address}/{network.prefixlen}")
        except ValueError as exc:
            raise ToolError(f"Not a valid address or CIDR: {exc}") from exc
    network = interface.network
    hosts = list(network.hosts()) if network.num_addresses <= 65536 else []
    result = {
        "input": raw,
        "version": f"IPv{network.version}",
        "address": str(interface.ip),
        "prefix": f"/{network.prefixlen}",
        "netmask": str(network.netmask),
        "wildcard": str(network.hostmask),
        "network": str(network.network_address),
        "broadcast": str(network.broadcast_address),
        "first_host": str(hosts[0]) if hosts else "-",
        "last_host": str(hosts[-1]) if hosts else "-",
        "usable_hosts": max(0, network.num_addresses - 2) if network.prefixlen < 31 else network.num_addresses,
        "total_addresses": network.num_addresses,
        "is_private": network.is_private,
        "is_global": network.is_global,
        "scope": ("Private (RFC 1918)" if network.is_private else
                  "Loopback" if network.is_loopback else
                  "Link-local" if network.is_link_local else "Public"),
    }
    ctx.log(report_table([{"field": k, "value": str(val)} for k, val in result.items()]))
    return result


@tool(id="subnet-split", name="Split a Subnet", category="Network",
      summary="Divide a network into equal smaller subnets, or into a set number of them.",
      keywords="subnet split divide vlsm cidr plan",
      fields=[F.text("cidr", "Network", "192.168.0.0/24", required=True),
              F.choice("mode", "Split by", ["New prefix", "Number of subnets"], "New prefix"),
              F.integer("new_prefix", "New prefix", 26, minimum=1, maximum=128),
              F.integer("count", "How many subnets", 4, minimum=2, maximum=1024)])
def subnet_split(v, ctx):
    try:
        network = ipaddress.ip_network(v["cidr"].strip(), strict=False)
    except ValueError as exc:
        raise ToolError(f"Not a valid network: {exc}") from exc
    if v["mode"] == "New prefix":
        prefix = v["new_prefix"]
    else:
        import math
        needed = math.ceil(math.log2(max(2, v["count"])))
        prefix = network.prefixlen + needed
    if prefix <= network.prefixlen or prefix > network.max_prefixlen:
        raise ToolError(f"A /{prefix} split is not possible for {network}")
    subnets = list(network.subnets(new_prefix=prefix))
    rows = []
    for subnet in subnets[:256]:
        hosts = list(subnet.hosts())
        rows.append({"subnet": str(subnet),
                     "range": f"{hosts[0]} – {hosts[-1]}" if hosts else "-",
                     "usable": subnet.num_addresses if subnet.prefixlen >= 31 else subnet.num_addresses - 2})
    ctx.log(report_table(rows))
    return f"{len(subnets)} subnet(s) of /{prefix} from {network}"


@tool(id="ip-in-subnet", name="Is an IP in a Subnet?", category="Network",
      summary="Check whether an address belongs to a network, and explain why.",
      keywords="ip subnet check contains belongs membership",
      fields=[F.text("address", "IP address", "192.168.1.50", required=True),
              F.text("network", "Network", "192.168.1.0/24", required=True)])
def ip_in_subnet(v, ctx):
    try:
        address = ipaddress.ip_address(v["address"].strip())
        network = ipaddress.ip_network(v["network"].strip(), strict=False)
    except ValueError as exc:
        raise ToolError(f"Invalid input: {exc}") from exc
    inside = address in network
    return {"address": str(address), "network": str(network), "inside": inside,
            "network_address": str(network.network_address),
            "broadcast": str(network.broadcast_address)}


@tool(id="ip-convert", name="Convert an IP Address", category="Network",
      summary="Show an IPv4 address as decimal, hex, binary, IPv4-mapped IPv6 and reversed form.",
      keywords="ip convert decimal hex binary reverse ptr",
      fields=[F.text("address", "IP address", "192.168.1.1", required=True)])
def ip_convert(v, ctx):
    try:
        address = ipaddress.ip_address(v["address"].strip())
    except ValueError as exc:
        raise ToolError(f"Not a valid IP address: {exc}") from exc
    if address.version != 4:
        return {"ipv6": str(address), "exploded": address.exploded,
                "compressed": address.compressed,
                "integer": int(address), "hex": hex(int(address))}
    octets = [int(part) for part in str(address).split(".")]
    return {
        "ipv4": str(address),
        "integer": int(address),
        "hex": "0x" + "".join(f"{octet:02x}" for octet in octets),
        "binary": ".".join(f"{octet:08b}" for octet in octets),
        "ipv6_mapped": f"::ffff:{address}",
        "reverse_dns": ".".join(reversed(str(address).split("."))) + ".in-addr.arpa",
        "class": "A" if octets[0] < 128 else "B" if octets[0] < 192 else "C" if octets[0] < 224 else "D/E",
    }


@tool(id="cidr-list", name="List Every Address in a Range", category="Network",
      summary="Print every usable address in a subnet — for inventories and firewall lists.",
      keywords="list addresses range cidr all hosts inventory",
      fields=[F.text("cidr", "Network", "10.0.0.0/28", required=True),
              F.integer("limit", "Maximum addresses", 512, minimum=1, maximum=65536),
              F.save("output", "Save to file", required=False)])
def cidr_list(v, ctx):
    from ._util import write_text
    try:
        network = ipaddress.ip_network(v["cidr"].strip(), strict=False)
    except ValueError as exc:
        raise ToolError(f"Not a valid network: {exc}") from exc
    addresses = [str(host) for host in network.hosts()][:v["limit"]]
    if not addresses:
        addresses = [str(network.network_address)]
    ctx.log("\n".join(addresses[:400]) + ("\n…" if len(addresses) > 400 else ""))
    if v["output"].strip():
        target = write_text(out_path(v["output"], "addresses.txt"), "\n".join(addresses))
        ctx.output(str(target))
    return f"{len(addresses)} address(es)"


# --------------------------------------------------------------------------
# DNS
# --------------------------------------------------------------------------
@tool(id="dns-lookup", name="DNS Lookup", category="Network",
      summary="Resolve a hostname to its addresses, or an address back to its name.",
      keywords="dns lookup resolve hostname ip address ptr",
      fields=[F.text("host", "Hostname or IP", "example.com", required=True)])
def dns_lookup(v, ctx):
    target = v["host"].strip()
    if not target:
        raise ToolError("Give a hostname or IP address")
    try:
        ipaddress.ip_address(target)
        try:
            name, aliases, addresses = socket.gethostbyaddr(target)
        except OSError:
            return {"address": target, "reverse": "(no PTR record)"}
        return {"address": target, "hostname": name, "aliases": aliases,
                "addresses": addresses}
    except ValueError:
        pass
    try:
        name, aliases, addresses = socket.gethostbyname_ex(target)
    except socket.gaierror as exc:
        raise ToolError(f"Could not resolve {target}: {exc}") from exc
    try:
        canonical = socket.getfqdn(target)
    except OSError:
        canonical = target
    return {"hostname": target, "canonical": canonical, "addresses": addresses,
            "aliases": aliases}


@tool(id="dns-records", name="DNS Records", category="Network",
      summary="Query MX, TXT, NS, SOA and CNAME records for a domain.",
      keywords="dns records mx txt ns soa spf dmarc email",
      fields=[F.text("domain", "Domain", "example.com", required=True),
              F.choice("type", "Record type", ["MX", "TXT", "NS", "SOA", "CNAME", "A", "AAAA"],
                       "MX")])
def dns_records(v, ctx):
    domain = v["domain"].strip()
    if not domain:
        raise ToolError("Give a domain name")
    resolver = which("nslookup") or which("nslookup.exe")
    if resolver:
        code, out, err = run_command([resolver, "-type=" + v["type"], domain], timeout=60)
        if code != 0 and not out:
            raise ToolError(f"Lookup failed: {err.strip()[:200]}")
        lines = [line.strip() for line in out.splitlines()
                 if line.strip() and not line.strip().lower().startswith(("server:", "address:"))]
        ctx.log("\n".join(lines))
        return f"{v['type']} records for {domain}"
    try:
        addresses = sorted({info[4][0] for info in socket.getaddrinfo(domain, None)})
    except socket.gaierror as exc:
        raise ToolError(f"Could not resolve {domain}: {exc}") from exc
    ctx.log("nslookup is not available; showing address records only")
    return {"domain": domain, "addresses": addresses}


@tool(id="email-dns-check", name="Email Setup Check", category="Network",
      summary="Check a domain's MX, SPF and DMARC records to see if email is set up correctly.",
      keywords="email mx spf dmarc dns deliverability domain",
      fields=[F.text("domain", "Domain", "example.com", required=True)])
def email_dns_check(v, ctx):
    domain = v["domain"].strip().lstrip("@")
    if not domain:
        raise ToolError("Give a domain name")
    resolver = which("nslookup") or which("nslookup.exe")
    results: dict[str, str] = {}
    for record in ("MX", "TXT"):
        if not resolver:
            results[record] = "(nslookup unavailable)"
            continue
        _, out, _ = run_command([resolver, "-type=" + record, domain], timeout=60)
        results[record] = out.strip() or "(none)"
        ctx.log(f"--- {record} ---")
        ctx.log(results[record][:1200])
    for record in ("TXT",):
        if resolver:
            _, out, _ = run_command([resolver, "-type=TXT", "_dmarc." + domain], timeout=60)
            ctx.log("--- DMARC ---")
            ctx.log((out.strip() or "(none)")[:800])
            results["DMARC"] = out.strip()
    return {"domain": domain, "mx": "see output", "spf": "see TXT above"}


@tool(id="dns-flush", name="Flush DNS Cache", category="Network",
      summary="Clear the resolver cache so a changed DNS record takes effect immediately.",
      keywords="dns flush cache clear resolver ipconfig",
      platforms=("win",),
      fields=[F.flag("confirm", "Flush now", False)])
def dns_flush(v, ctx):
    if not v["confirm"]:
        return "Tick 'Flush now' to clear the DNS cache"
    code, out, err = run_command(["ipconfig", "/flushdns"], ctx=ctx, timeout=60)
    if code != 0:
        raise ToolError(f"ipconfig failed: {err.strip()[:200]}")
    return "DNS cache cleared"


# --------------------------------------------------------------------------
# Reachability
# --------------------------------------------------------------------------
@tool(id="ping-host", name="Ping", category="Network",
      summary="Send ICMP pings and report round-trip times, loss and reachability.",
      keywords="ping icmp latency reachable response",
      fields=[F.text("host", "Host", "8.8.8.8", required=True),
              F.integer("count", "Pings", 4, minimum=1, maximum=50),
              F.integer("timeout_ms", "Timeout (ms)", 2000, minimum=100, maximum=30000)])
def ping_host(v, ctx):
    flag_count = "-n" if WINDOWS else "-c"
    flag_wait = "-w" if WINDOWS else "-W"
    wait = str(v["timeout_ms"]) if WINDOWS else str(max(1, v["timeout_ms"] // 1000))
    code, out, err = run_command(["ping", flag_count, str(v["count"]), flag_wait, wait,
                                  v["host"].strip()], timeout=v["count"] * 5 + 10, ctx=ctx)
    times = [int(m) for m in re.findall(r"(?:time|time=)[=<]?\s*(\d+)\s*ms", out)]
    return {"host": v["host"], "reachable": code == 0,
            "replies": len(times),
            "average_ms": round(sum(times) / len(times), 1) if times else None,
            "min_ms": min(times) if times else None,
            "max_ms": max(times) if times else None}


@tool(id="traceroute", name="Trace Route", category="Network",
      summary="Show the hops a packet takes to reach a host, with timings.",
      keywords="traceroute tracert hops path route network",
      fields=[F.text("host", "Host", "8.8.8.8", required=True),
              F.integer("max_hops", "Maximum hops", 20, minimum=1, maximum=64)])
def traceroute(v, ctx):
    command = "tracert" if WINDOWS else "traceroute"
    if not which(command):
        raise ToolError(f"{command} is not available on this system")
    code, out, err = run_command([command, "-h" if WINDOWS else "-m", str(v["max_hops"]),
                                  v["host"].strip()], timeout=180)
    lines = [line for line in out.splitlines() if line.strip()]
    ctx.log("\n".join(lines[-40:]))
    return f"{len(lines)} line(s) of route output"


@tool(id="port-check", name="Check a Port", category="Network",
      summary="Test whether one TCP port on a host is open, and how fast it answers.",
      keywords="port check open closed tcp connect service",
      fields=[F.text("host", "Host", "example.com", required=True),
              F.integer("port", "Port", 443, minimum=1, maximum=65535),
              F.number("timeout", "Timeout (seconds)", 3.0, minimum=0.2, maximum=60.0)])
def port_check(v, ctx):
    host, port = v["host"].strip(), v["port"]
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=v["timeout"]):
            elapsed = (time.perf_counter() - started) * 1000
            return {"host": host, "port": port, "open": True, "connect_ms": round(elapsed, 1)}
    except (socket.timeout, TimeoutError):
        return {"host": host, "port": port, "open": False, "reason": "timed out"}
    except socket.gaierror as exc:
        raise ToolError(f"Could not resolve {host}: {exc}") from exc
    except OSError as exc:
        return {"host": host, "port": port, "open": False, "reason": str(exc)}


@tool(id="port-scan", name="Scan Ports", category="Network",
      summary="Check a range of TCP ports on a host you own, and list what is open.",
      keywords="port scan open ports range network audit nmap",
      fields=[F.text("host", "Host", "127.0.0.1", required=True),
              F.text("ports", "Ports", "1-1024", required=True,
                     help="Ranges and lists: 22,80,443,8000-8100"),
              F.number("timeout", "Timeout per port (seconds)", 0.5, minimum=0.05, maximum=10.0),
              F.integer("workers", "Parallel checks", 64, minimum=1, maximum=256)])
def port_scan(v, ctx):
    from concurrent.futures import ThreadPoolExecutor
    host = v["host"].strip()
    ports: list[int] = []
    for chunk in v["ports"].split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            start, _, end = chunk.partition("-")
            ports.extend(range(int(start), int(end) + 1))
        elif chunk:
            ports.append(int(chunk))
    if not ports:
        raise ToolError("Give at least one port or range")
    if len(ports) > 20000:
        raise ToolError("That is over 20,000 ports — narrow the range")
    open_ports: list[dict] = []
    done = 0

    def probe(port: int):
        try:
            with socket.create_connection((host, port), timeout=v["timeout"]):
                return port
        except OSError:
            return None

    with ThreadPoolExecutor(max_workers=v["workers"]) as pool:
        for result in pool.map(probe, ports):
            done += 1
            if result:
                try:
                    service = socket.getservbyport(result, "tcp")
                except OSError:
                    service = "unknown"
                open_ports.append({"port": result, "service": service})
                ctx.log(f"open  {result:<6} {service}")
            if done % 200 == 0:
                ctx.progress(done / len(ports) * 100, f"{done}/{len(ports)}")
                ctx.check_cancel()
    if not open_ports:
        return f"No open TCP ports found in {len(ports)} checked on {host}"
    return f"{len(open_ports)} open port(s) of {len(ports)} checked on {host}"


@tool(id="wake-on-lan", name="Wake-on-LAN", category="Network",
      summary="Send a magic packet to wake a sleeping machine on your network.",
      keywords="wake on lan wol magic packet mac boot remote",
      fields=[F.text("mac", "MAC address", "AA:BB:CC:DD:EE:FF", required=True),
              F.text("broadcast", "Broadcast address", "255.255.255.255"),
              F.integer("port", "Port", 9, minimum=1, maximum=65535)])
def wake_on_lan(v, ctx):
    cleaned = re.sub(r"[^0-9a-fA-F]", "", v["mac"])
    if len(cleaned) != 12:
        raise ToolError("A MAC address has 12 hex digits, like AA:BB:CC:DD:EE:FF")
    mac_bytes = bytes.fromhex(cleaned)
    packet = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(3):
            sock.sendto(packet, (v["broadcast"].strip(), v["port"]))
    return f"Magic packet sent 3× to {v['broadcast']} for {v['mac']}"


@tool(id="local-interfaces", name="Local Network Info", category="Network",
      summary="This machine's name, addresses, gateway and active interface details.",
      keywords="local ip address interfaces hostname gateway my ip",
      fields=[])
def local_interfaces(v, ctx):
    hostname = socket.gethostname()
    try:
        addresses = sorted({info[4][0] for info in socket.getaddrinfo(hostname, None)})
    except socket.gaierror:
        addresses = []
    gateway = ""
    if WINDOWS:
        code, out, _ = run_command(["ipconfig"], timeout=30)
        match = re.search(r"Default Gateway[ .]*:\s*([\d.]+)", out)
        gateway = match.group(1) if match else ""
    else:
        code, out, _ = run_command(["ip", "route"], timeout=30)
        match = re.search(r"default via ([\d.]+)", out)
        gateway = match.group(1) if match else ""
    result = {"hostname": hostname, "addresses": addresses, "default_gateway": gateway or "(unknown)",
              "fqdn": socket.getfqdn()}
    ctx.log(report_table([{"field": k, "value": str(val)} for k, val in result.items()]))
    return result


@tool(id="public-ip", name="Public IP Address", category="Network",
      summary="What the internet sees as your address, with country and provider.",
      keywords="public ip external address my internet wan",
      fields=[F.flag("detailed", "Include country and provider", True)])
def public_ip(v, ctx):
    endpoints = (["https://ipinfo.io/json"] if v["detailed"] else []) + \
                ["https://api.ipify.org", "https://ifconfig.me/ip"]
    last_error = ""
    for url in endpoints:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=8) as response:
                body = response.read().decode("utf-8", "replace").strip()
            if v["detailed"] and body.startswith("{"):
                data = json.loads(body)
                return {key: data.get(key, "") for key in ("ip", "city", "region", "country", "org", "timezone")}
            return {"public_ip": body}
        except Exception as exc:  # noqa: BLE001 - try the next endpoint
            last_error = str(exc)
    raise ToolError(f"Could not reach an IP service: {last_error}")


@tool(id="netstat-connections", name="Active Connections", category="Network",
      summary="Every current TCP connection and listening port on this machine.",
      keywords="netstat connections listening ports sockets established",
      fields=[F.flag("listening_only", "Only listening ports", True)])
def netstat_connections(v, ctx):
    if WINDOWS:
        code, out, _ = run_command(["netstat", "-ano"], timeout=60)
        lines = out.splitlines()
        header = lines[:4]
        body = [line for line in lines[4:] if line.strip()]
        if v["listening_only"]:
            body = [line for line in body if "LISTEN" in line.upper()]
    else:
        code, out, _ = run_command(["ss", "-tunap"] if which("ss") else ["netstat", "-tunap"],
                                   timeout=60)
        lines = out.splitlines()
        header = lines[:1]
        body = [line for line in lines[1:] if line.strip()]
        if v["listening_only"]:
            body = [line for line in body if "LISTEN" in line.upper()]
    ctx.log("\n".join(header))
    ctx.log("\n".join(body[:120]))
    return f"{len(body)} connection(s)"


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
def _fetch(url: str, method: str = "GET", timeout: int = 20, headers: dict | None = None):
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    request = urllib.request.Request(url, method=method,
                                     headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()
    except urllib.error.URLError as exc:
        raise ToolError(f"Could not reach {url}: {exc.reason}") from exc


@tool(id="http-get", name="Fetch a URL", category="Network",
      summary="Download a page or API response, showing status, headers and the body.",
      keywords="http get fetch url request download api page",
      fields=[F.text("url", "URL", "https://example.com", required=True),
              F.integer("timeout", "Timeout (seconds)", 20, minimum=1, maximum=300),
              F.integer("max_kb", "Show at most (KB)", 32, minimum=1, maximum=10240),
              F.save("output", "Save body to", required=False)])
def http_get(v, ctx):
    status, headers, body = _fetch(v["url"].strip(), timeout=v["timeout"])
    ctx.log(f"HTTP {status}")
    for key in ("Content-Type", "Content-Length", "Server", "Location", "Cache-Control"):
        if key in headers:
            ctx.log(f"{key}: {headers[key]}")
    text = body.decode("utf-8", "replace")
    limit = v["max_kb"] * 1024
    ctx.log("")
    ctx.log(text[:limit] + ("\n… (truncated)" if len(text) > limit else ""))
    if v["output"].strip():
        target = out_path(v["output"], "response.txt")
        target.write_bytes(body)
        ctx.output(str(target))
        ctx.log(f"Saved {human_size(len(body))} to {target}")
    return {"status": status, "bytes": len(body), "content_type": headers.get("Content-Type", "")}


@tool(id="http-headers", name="Inspect HTTP Headers", category="Network",
      summary="Check a site's status, security headers and redirect chain without downloading it.",
      keywords="http headers security hsts csp redirect status",
      fields=[F.text("url", "URL", "https://example.com", required=True)])
def http_headers(v, ctx):
    status, headers, _ = _fetch(v["url"].strip(), method="HEAD")
    rows = [{"header": key, "value": str(value)[:80]} for key, value in headers.items()]
    ctx.log(report_table(rows))
    security = {
        "strict-transport-security": "HSTS",
        "content-security-policy": "CSP",
        "x-frame-options": "clickjacking protection",
        "x-content-type-options": "MIME sniffing protection",
        "referrer-policy": "referrer policy",
        "permissions-policy": "permissions policy",
    }
    lower_headers = {name.lower() for name in headers}
    present = {label: ("yes" if header in lower_headers else "no")
               for header, label in security.items()}
    ctx.log("")
    ctx.log(report_table([{"security header": k, "present": val} for k, val in present.items()]))
    return {"status": status, "security_headers": present}


@tool(id="http-download", name="Download a File", category="Network",
      summary="Download a file with progress, size and a safe resume-free write.",
      keywords="download file url save progress http",
      fields=[F.text("url", "URL", required=True),
              F.save("output", "Save as", required=True),
              F.integer("timeout", "Timeout (seconds)", 120, minimum=5, maximum=3600)])
def http_download(v, ctx):
    url = v["url"].strip()
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    target = out_path(v["output"], Path(url).name or "download.bin")
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=v["timeout"]) as response:
            total = int(response.headers.get("Content-Length", 0) or 0)
            read = 0
            with open(target, "wb") as fh:
                while True:
                    block = response.read(1 << 16)
                    if not block:
                        break
                    fh.write(block)
                    read += len(block)
                    if total:
                        ctx.progress(read / total * 100, f"{human_size(read)} of {human_size(total)}")
                    ctx.check_cancel()
    except urllib.error.URLError as exc:
        raise ToolError(f"Download failed: {exc.reason}") from exc
    ctx.output(str(target))
    return f"Downloaded {human_size(target.stat().st_size)} → {target.name}"


@tool(id="url-status-check", name="Check Many URLs", category="Network",
      summary="Test a list of links and report status codes, redirects and response times.",
      keywords="url check status links broken batch monitor",
      fields=[F.multi("urls", "URLs (one per line)", rows=8, placeholder="https://example.com"),
              F.integer("timeout", "Timeout per URL (seconds)", 10, minimum=1, maximum=120),
              F.save("report", "Save CSV to", required=False)])
def url_status_check(v, ctx):
    from ._util import write_csv
    urls = [line.strip() for line in v["urls"].splitlines() if line.strip()]
    if not urls:
        raise ToolError("Paste at least one URL")
    rows = []
    for url in urls:
        ctx.check_cancel()
        started = time.perf_counter()
        try:
            status, headers, body = _fetch(url, timeout=v["timeout"])
            rows.append({"url": url, "status": status, "ms": round((time.perf_counter() - started) * 1000),
                         "bytes": len(body), "final_url": headers.get("Location", url)})
        except ToolError as exc:
            rows.append({"url": url, "status": "error", "ms": 0, "bytes": 0, "final_url": str(exc)[:60]})
        ctx.log(f"{rows[-1]['status']}  {rows[-1]['ms']}ms  {url}")
    ctx.log("")
    ctx.log(report_table(rows[:60], ["status", "ms", "url"]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "url-check.csv"), rows)
        ctx.output(str(target))
    broken = sum(1 for row in rows if str(row["status"]).startswith(("4", "5", "error")))
    return f"{len(rows)} URL(s) checked, {broken} problem(s)"


@tool(id="tls-certificate", name="Check TLS Certificate", category="Network",
      summary="Issuer, validity dates and days remaining for a site's HTTPS certificate.",
      keywords="ssl tls certificate expiry https security issuer",
      fields=[F.text("host", "Host", "example.com", required=True),
              F.integer("port", "Port", 443, minimum=1, maximum=65535)])
def tls_certificate(v, ctx):
    host = v["host"].strip()
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, v["port"]), timeout=10) as raw:
            with context.wrap_socket(raw, server_hostname=host) as secure:
                certificate = secure.getpeercert()
                protocol = secure.version()
    except (ssl.SSLError, socket.error, OSError) as exc:
        raise ToolError(f"Could not read the certificate: {exc}") from exc
    expires = certificate.get("notAfter", "")
    days_left = None
    if expires:
        from datetime import datetime
        try:
            days_left = (datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z") - datetime.utcnow()).days
        except ValueError:
            pass
    issuer = dict(item[0] for item in certificate.get("issuer", ()) if item)
    subject = dict(item[0] for item in certificate.get("subject", ()) if item)
    sans = [value for kind, value in certificate.get("subjectAltName", ()) if kind == "DNS"]
    result = {
        "host": host, "protocol": protocol,
        "subject": subject.get("commonName", ""),
        "issuer": issuer.get("organizationName", issuer.get("commonName", "")),
        "valid_from": certificate.get("notBefore", ""),
        "valid_until": expires,
        "days_remaining": days_left,
        "status": "expired" if days_left is not None and days_left < 0 else
                  "expiring soon" if days_left is not None and days_left < 30 else "valid",
        "names": sans[:12],
    }
    ctx.log(report_table([{"field": k, "value": str(val)} for k, val in result.items()]))
    return result


@tool(id="mac-format", name="Normalise a MAC Address", category="Network",
      summary="Reformat a MAC address into the style a device or router expects.",
      keywords="mac address format colon hyphen cisco dot",
      fields=[F.text("mac", "MAC address", "aabbccddeeff", required=True),
              F.choice("style", "Style",
                       ["AA:BB:CC:DD:EE:FF", "AA-BB-CC-DD-EE-FF", "aabb.ccdd.eeff",
                        "AABBCCDDEEFF"], "AA:BB:CC:DD:EE:FF")])
def mac_format(v, ctx):
    cleaned = re.sub(r"[^0-9a-fA-F]", "", v["mac"])
    if len(cleaned) != 12:
        raise ToolError("A MAC address has 12 hex digits")
    upper = cleaned.upper()
    pairs = [upper[i:i + 2] for i in range(0, 12, 2)]
    styles = {
        "AA:BB:CC:DD:EE:FF": ":".join(pairs),
        "AA-BB-CC-DD-EE-FF": "-".join(pairs),
        "aabb.ccdd.eeff": ".".join([cleaned[i:i + 4].lower() for i in range(0, 12, 4)]),
        "AABBCCDDEEFF": upper,
    }
    return {"mac": styles[v["style"]], "all_styles": styles,
            "locally_administered": bool(int(pairs[0], 16) & 0x02),
            "multicast": bool(int(pairs[0], 16) & 0x01)}


@tool(id="whois-lookup", name="WHOIS Lookup", category="Network",
      summary="Registration details for a domain, straight from the WHOIS server.",
      keywords="whois domain registration owner expiry nameserver",
      fields=[F.text("domain", "Domain", "example.com", required=True)])
def whois_lookup(v, ctx):
    domain = v["domain"].strip().lower()
    if "." not in domain:
        raise ToolError("Give a full domain, like example.com")
    server = "whois.iana.org"
    try:
        with socket.create_connection((server, 43), timeout=10) as sock:
            sock.sendall((domain + "\r\n").encode())
            chunks = []
            while True:
                block = sock.recv(4096)
                if not block:
                    break
                chunks.append(block)
    except OSError as exc:
        raise ToolError(f"Could not reach the WHOIS server: {exc}") from exc
    text = b"".join(chunks).decode("utf-8", "replace")
    refer = re.search(r"(?im)^refer:\s*(\S+)", text)
    if refer:
        try:
            with socket.create_connection((refer.group(1), 43), timeout=10) as sock:
                sock.sendall((domain + "\r\n").encode())
                chunks = []
                while True:
                    block = sock.recv(4096)
                    if not block:
                        break
                    chunks.append(block)
            text = b"".join(chunks).decode("utf-8", "replace")
        except OSError:
            pass
    interesting = [line for line in text.splitlines()
                   if re.match(r"(?i)^(domain|registrar|creation|created|expiry|expires|"
                               r"updated|name server|status|org|country)", line.strip())]
    ctx.log("\n".join(interesting[:40]) or text[:1500])
    return f"{len(interesting)} key line(s) for {domain}"
