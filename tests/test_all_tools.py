#!/usr/bin/env python3
"""
Exhaustive audit sweep: invokes every registered tool in its own subprocess
(with a hard timeout) so a hang or crash in one tool can never affect the
audit of the next 499. Flags:
  - TIMEOUT   : tool did not return within the timeout (likely a blocking
                server/watcher run with no bounding option - expected for a
                known allow-list, a bug otherwise)
  - TRACEBACK : an uncaught Python traceback reached stderr (the tool_registry
                catch-all should prevent this - any hit here is a real bug)
  - CRASH     : the interpreter itself exited abnormally (e.g. segfault) -
                none expected in pure-Python tools
Everything else (clean exit 0, or a graceful "usage"/"unavailable" message
with a non-zero code) is recorded as OK.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.cli import build_registry  # noqa: E402

# Tools that intentionally block/listen/loop and must be given bounding
# arguments (or are expected to time out and are treated as OK if they do).
EXPECTED_LONG_RUNNING = {
    "http-serve",
    "watch",
    "folder-watch",
    "process-monitor",
    "log-tail",
    "port-listener",
    "clipboard-watch",
    "network-monitor",
    "idle-monitor",
}

TIMEOUT_S = 6

# Tools that shell out to WMI / PowerShell / pip and legitimately need longer
# than the default budget on a cold start.  These are not hangs - measured
# 5-10s on a warm machine and considerably longer on a cold one - so they get
# their own budget instead of being reported as unexpected timeouts.
SLOW_TOOLS = {
    "bluetooth-device-inventory",
    "driver-backup",
    "firewall-status",
    "folder-backup",
    "image-batch-hash",
    "incremental-backup",
    "installed-software-snapshot",
    "media-duration-inventory",
    "media-hash-inventory",
    "mirror-backup",
    "network-connection-table",
    "printer-inventory",
    "python-package-list",
    "python-package-versions",
    "scheduled-task-list",
    "security-event-summary",
    "service-security-report",
    "virtual-environment-finder",
    "virtual-environment-report",
}
SLOW_TIMEOUT_S = 60


def main():
    registry = build_registry()
    sandbox = tempfile.mkdtemp(prefix="us_full_sweep_")
    with open(os.path.join(sandbox, "sample.txt"), "w") as f:
        f.write("hello world\nsecond line\n")
    with open(os.path.join(sandbox, "sample.csv"), "w") as f:
        f.write("name,age\nAlice,30\nBob,40\n")
    with open(os.path.join(sandbox, "sample.json"), "w") as f:
        f.write('{"a": 1, "b": 2}')

    results = {"ok": [], "timeout": [], "traceback": [], "crash": []}
    commands = sorted(registry.tools.keys())
    print(f"Sweeping {len(commands)} tools with a {TIMEOUT_S}s budget each "
          f"({SLOW_TIMEOUT_S}s for the {len(SLOW_TOOLS)} WMI/PowerShell tools)...\n")

    for i, cmd in enumerate(commands, 1):
        tool = registry.get_tool(cmd)
        if not tool["available"]:
            results["ok"].append((cmd, "unavailable (dependency gated)"))
            continue

        # Give every tool one plausible generic argument - the sandbox
        # directory - since most take a path. Argument-order-sensitive
        # tools will simply report a usage error, which is a fine, safe
        # outcome for this sweep.
        args = [sandbox]
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join(ROOT, "run.py"), "run", cmd] + args,
                capture_output=True,
                text=True,
                timeout=SLOW_TIMEOUT_S if cmd in SLOW_TOOLS else TIMEOUT_S,
                cwd=sandbox,
                # Close stdin: several text tools fall back to reading stdin
                # when no text argument is given, and inheriting the terminal
                # made them block forever waiting for EOF.
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            if cmd in EXPECTED_LONG_RUNNING:
                results["ok"].append((cmd, "timed out as expected (long-running tool)"))
            else:
                results["timeout"].append(cmd)
            continue

        if proc.returncode < 0:
            results["crash"].append((cmd, f"killed by signal {-proc.returncode}"))
            continue

        stderr = proc.stderr or ""
        if "Traceback (most recent call last)" in stderr:
            results["traceback"].append((cmd, stderr.strip().splitlines()[-1]))
            continue

        results["ok"].append((cmd, f"exit={proc.returncode}"))

        if i % 50 == 0:
            print(f"  ...{i}/{len(commands)} checked")

    shutil.rmtree(sandbox, ignore_errors=True)

    print("\n=== SWEEP SUMMARY ===")
    print(f"OK: {len(results['ok'])}")
    print(f"Unexpected TIMEOUT: {len(results['timeout'])}")
    print(f"TRACEBACK (bug): {len(results['traceback'])}")
    print(f"CRASH: {len(results['crash'])}")

    if results["timeout"]:
        print("\nUnexpected timeouts:")
        for cmd in results["timeout"]:
            print(f"  - {cmd}")
    if results["traceback"]:
        print("\nTracebacks (these are real bugs - the registry's catch-all should have prevented this):")
        for cmd, last_line in results["traceback"]:
            print(f"  - {cmd}: {last_line}")
    if results["crash"]:
        print("\nCrashes:")
        for cmd, detail in results["crash"]:
            print(f"  - {cmd}: {detail}")

    # Write the detailed results outside the source tree so running the sweep
    # never leaves an artifact behind in the repository.
    results_path = os.path.join(tempfile.gettempdir(), "us_sweep_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results written to {results_path}")

    return 1 if (results["timeout"] or results["traceback"] or results["crash"]) else 0


if __name__ == "__main__":
    sys.exit(main())
