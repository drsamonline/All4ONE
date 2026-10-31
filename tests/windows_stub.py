"""Exercise the Windows-only tools without Windows.

Their logic — parsing PowerShell output, formatting tables, handling a machine
where a query finds nothing — is ordinary Python, so it can be tested here with
PowerShell stubbed out. What this cannot test is whether the cmdlets themselves
behave as documented; the Windows CI runner covers that by executing the
read-only ones for real.

Run:  python tests/windows_stub.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402
from core.tool import Tool  # noqa: E402
from tools import disk, system  # noqa: E402

SKIP = {"power-actions", "service-control", "registry-write", "registry-delete",
        "temp-clean", "recycle-bin", "file-shred", "folder-shred", "batch-delete-list",
        "defender-scan", "hosts-file", "process-kill", "disk-speed-test"}

EMPTY = ""                                   # a query that finds nothing
EMPTY_JSON = "[]"
ONE_ROW = ('[{"Name":"Spooler","DisplayName":"Print Spooler","Status":"Running",'
           '"StartType":"Automatic","TaskName":"Backup","TaskPath":"\\\\","State":"Ready",'
           '"Id":4,"ProcessName":"svc","WS":12.5,"Path":"C:\\\\x.exe","Enabled":true,'
           '"LastLogon":"2026-01-01","Description":"d","HotFixID":"KB1","InstalledOn":"2026-01-01",'
           '"MediaType":"SSD","HealthStatus":"Healthy","OperationalStatus":"OK","Size":100,'
           '"DiskNumber":0,"PartitionNumber":1,"DriveLetter":"C","Type":"Basic",'
           '"FileSystemLabel":"OS","FileSystem":"NTFS","SizeRemaining":50,'
           '"FriendlyName":"USB Stick","InstanceId":"USB\\\\VID","Direction":"Inbound",'
           '"Action":"Allow","Profile":"Domain","MountPoint":"C:","VolumeStatus":"FullyDecrypted",'
           '"ProtectionStatus":"Off","EncryptionPercentage":100,"TimeCreated":"2026-01-01",'
           '"LevelDisplayName":"Error","ProviderName":"src","Message":"m","TaskPath":"\\\\"}]')
TEXT = "Real-time protection: True\nAntivirus enabled: True\n"


def values_for(tool: Tool) -> dict:
    values = {}
    for field in tool.fields:
        if field.kind == "choice":
            values[field.key] = field.choices[0]
        elif field.kind == "bool":
            values[field.key] = False
        elif field.kind in ("int", "float", "slider"):
            values[field.key] = field.default or 1
        elif field.kind == "text":
            values[field.key] = {
                "hive": "HKEY_CURRENT_USER", "path": "Software", "name": "x",
                "value": "", "target": "x", "filter": "", "language": "eng",
                "show": "Saved profiles", "log": "System", "level": "All",
                "action": "Start", "direction": "Inbound", "kind": "Quick",
                "modified": "2026-01-01 09:30", "colour": "#3366cc",
            }.get(field.key, "")
        else:
            values[field.key] = ""
    return values


def run_case(payload: str, label: str) -> list[str]:
    failures: list[str] = []
    for module in (system, disk):
        module._powershell = lambda *a, **k: payload  # type: ignore[assignment]

    tools = [t for t in registry.all_tools()
             if t.is_windows_only and t.id not in SKIP]
    for tool in tools:
        try:
            result = execute(tool, values_for(tool), sink=lambda line: None)
        except Exception as exc:  # noqa: BLE001 - this is the thing we are testing
            failures.append(f"{tool.id} raised {type(exc).__name__}: {exc}")
            continue
        if not result.ok and "needs setup" not in (result.error or ""):
            # A controlled ToolError is acceptable; an uncaught crash is not, and
            # the runner reports those as ok=False with a traceback.
            if "Traceback" in result.text or "NameError" in (result.error or ""):
                failures.append(f"{tool.id}: {result.error}")
    print(f"{label}: {len(tools)} Windows-only tools, {len(failures)} problem(s)")
    return failures


def main() -> int:
    failures = []
    failures += run_case(EMPTY, "empty output")
    failures += run_case(EMPTY_JSON, "empty JSON")
    failures += run_case(ONE_ROW, "one JSON row")
    failures += run_case(TEXT, "text output")

    if failures:
        print("\nproblems:")
        for line in failures:
            print(f"  ✕ {line}")
        return 1
    print("\nAll Windows-only tools handled every stub without crashing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
