#!/usr/bin/env python3
"""Environment gate for TD Factory.

Usage:
    python scripts/check_env.py

Verifies everything a build session needs: TouchDesigner install and version,
Embody/Envoy configuration (.mcp.json + bridge), the seed project, the git
repo, and the Python side (PyYAML) for scaffold scripts. Exit 0 means the
factory is ready to produce .toe files. See templates/SEED-SETUP.md for the
steps that fix whatever is missing.
"""
from __future__ import annotations

import json
import plistlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_TD = (2025, 33070)


def td_install():
    apps = sorted(Path("/Applications").glob("TouchDesigner*.app"))
    for app in apps:
        plist = app / "Contents" / "Info.plist"
        if plist.is_file():
            try:
                version = plistlib.load(open(plist, "rb")).get(
                    "CFBundleShortVersionString", "")
            except Exception:
                version = ""
            return app, version
    return None, ""


def version_tuple(v: str):
    return tuple(int(p) for p in v.split(".") if p.isdigit())


def td_pids():
    try:
        out = subprocess.run(
            ["pgrep", "-f", "TouchDesigner.app/Contents/MacOS/TouchDesigner"],
            capture_output=True, text=True, timeout=10)
        return [int(p) for p in out.stdout.split()]
    except Exception:
        return []


def envoy_listener(pids):
    for pid in pids:
        try:
            out = subprocess.run(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-a", "-p", str(pid)],
                capture_output=True, text=True, timeout=10)
            for line in out.stdout.splitlines()[1:]:
                if "127.0.0.1" in line:
                    return line.split()[-2] if len(line.split()) >= 2 else ""
        except Exception:
            pass
    return ""


def main() -> int:
    checks = []

    checks.append(("python", sys.version_info >= (3, 11),
                   sys.version.split()[0], True))

    try:
        import yaml  # noqa: F401
        checks.append(("pyyaml", True, "", True))
    except ImportError:
        checks.append(("pyyaml", False, "pip install pyyaml", True))

    app, version = td_install()
    if app is None:
        checks.append(("touchdesigner", False,
                       "not found in /Applications (need 2025.33070+)", True))
    else:
        ok = version_tuple(version) >= MIN_TD
        checks.append(("touchdesigner", ok,
                       f"{version} at {app}" + ("" if ok else f" (need {'.'.join(map(str, MIN_TD))}+)"), True))

    checks.append(("git repo", (ROOT / ".git").exists(), str(ROOT), True))

    mcp = ROOT / ".mcp.json"
    if mcp.is_file():
        try:
            data = json.loads(mcp.read_text(encoding="utf-8"))
            servers = list((data.get("mcpServers") or {}).keys())
            checks.append((".mcp.json", bool(servers),
                           "servers: " + ", ".join(servers) if servers
                           else "no mcpServers entry", True))
        except Exception as e:
            checks.append((".mcp.json", False, f"unparsable: {e}", True))
    else:
        checks.append((".mcp.json", False,
                       "missing (written by the Embody Setup Wizard)", True))

    bridge = ROOT / ".embody" / "envoy-bridge.py"
    checks.append(("envoy bridge", bridge.is_file(),
                   str(bridge.relative_to(ROOT)) if bridge.is_file()
                   else "missing (.embody/envoy-bridge.py)", True))

    seed = ROOT / "templates" / "seed.toe"
    checks.append(("seed.toe",
                   seed.is_file() and seed.stat().st_size > 0,
                   str(seed.relative_to(ROOT)) if seed.is_file()
                   else "missing (save the blank .toe as templates/seed.toe, see templates/SEED-SETUP.md)", True))

    pids = td_pids()
    checks.append(("td running", bool(pids),
                   f"pids: {', '.join(map(str, pids))}" if pids
                   else "TouchDesigner is not running", False))
    if pids:
        listener = envoy_listener(pids)
        checks.append(("envoy listening", bool(listener),
                       listener if listener
                       else "no localhost listener on the TD process", False))

    for label, ok, detail, _ in checks:
        state = "OK   " if ok else "MISS "
        line = f"{state}{label}"
        if detail:
            line += f"  ({detail})" if ok else f"  -> {detail}"
        print(line)

    missing = [c for c in checks if c[3] and not c[1]]
    print()
    if missing:
        print(f"NOT READY: {len(missing)} item(s) missing. "
              "Run the steps in templates/SEED-SETUP.md, then re-check.")
        return 1
    print("SEED READY: the factory can produce .toe projects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
