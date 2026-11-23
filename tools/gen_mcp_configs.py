#!/usr/bin/env python3
"""Generate each AI tool's MCP config from ai/approved-mcp.json, the single approved list.

Usage:
  python3 tools/gen_mcp_configs.py          write the files
  python3 tools/gen_mcp_configs.py --check  exit 1 if any file is missing or out of date
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent


def load_approved(root: Path = ROOT) -> dict:
    return json.loads((root / "ai" / "approved-mcp.json").read_text(encoding="utf-8"))


REQUIRED_FIELDS = ("description", "command", "args", "env", "approvedBy", "approvedOn", "permissions")
RUNNERS = {"docker", "npx", "uvx"}
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
SEMVER = r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?"
NPM_PINNED = re.compile(rf"^(@[^/@\s]+/)?[^/@\s]+@{SEMVER}$")
PY_PINNED = re.compile(rf"^[A-Za-z0-9._-]+(\[[^\]]+\])?=={SEMVER}$")
DOCKER_VALUE_FLAGS = {"-e", "--env", "-v", "--volume", "-p", "--publish", "--name", "--network",
                      "-w", "--workdir", "-u", "--user", "--entrypoint", "--mount", "--env-file"}
SENSITIVE_ENV = re.compile(r"TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE", re.I)


def first_positional(args: list[str], value_flags: set[str] = frozenset()) -> str | None:
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg in value_flags:
            skip = True
        elif not arg.startswith("-"):
            return arg
    return None


def validate_approved(approved: dict) -> list[str]:
    """Approval rules every server must meet before configs are generated."""
    from scan_secrets import scan_text  # same patterns as the secret scanner

    problems = []
    for name, s in approved.get("servers", {}).items():
        where = f"ai/approved-mcp.json: server '{name}'"
        missing = [f for f in REQUIRED_FIELDS if not s.get(f) and s.get(f) != []]
        if missing:
            problems.append(f"{where} is missing {', '.join(missing)}")
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s["approvedOn"])):
            problems.append(f"{where}: approvedOn must be a date (YYYY-MM-DD)")
        args = [str(a) for a in s["args"]]
        bad_env = [e for e in s["env"] if not ENV_NAME.match(str(e))]
        if bad_env:
            problems.append(f"{where}: env must list variable names only, not values ({bad_env[0]!r})")
        if scan_text("\n".join(args)):
            problems.append(f"{where}: args look like they contain a secret. Pass it as an environment variable")
        for i, arg in enumerate(args[:-1]):
            if arg in ("-e", "--env") and "=" in args[i + 1] and SENSITIVE_ENV.search(args[i + 1].split("=")[0]):
                problems.append(f"{where}: sets {args[i + 1].split('=')[0]} inline. Pass secrets by name only")
        command = s["command"]
        if command not in RUNNERS:
            problems.append(f"{where}: command '{command}' is not an approved runner ({', '.join(sorted(RUNNERS))})")
        elif command == "npx":
            package = first_positional(args)
            if not package or not NPM_PINNED.match(package):
                problems.append(f"{where}: pin the npm package to an exact version, e.g. name@1.2.3 (got {package!r})")
        elif command == "uvx":
            package = first_positional(args, {"--from", "--with", "--python"})
            if not package or not PY_PINNED.match(package):
                problems.append(f"{where}: pin the Python package to an exact version, e.g. name==1.2.3 (got {package!r})")
        elif command == "docker":
            if not args or args[0] != "run":
                problems.append(f"{where}: docker servers must start with 'run'")
            else:
                image = first_positional(args[1:], DOCKER_VALUE_FLAGS) or ""
                tag = image.rsplit("/", 1)[-1]
                if "@sha256:" not in image and (":" not in tag or tag.endswith(":latest")):
                    problems.append(f"{where}: pin the image to a version tag or digest (got {image!r})")
            if "--privileged" in args or any("docker.sock" in a for a in args):
                problems.append(f"{where}: privileged containers and the Docker socket are not allowed")
    return problems


def build_configs(approved: dict) -> dict[str, str]:
    servers = list(approved.get("servers", {}).items())

    def dump(obj: dict) -> str:
        return json.dumps(obj, indent=2) + "\n"

    # Claude Code (project scope) and Cursor share the "mcpServers" shape.
    mcp_servers = {name: {"command": s["command"], "args": s["args"]} for name, s in servers}
    # VS Code / GitHub Copilot uses "servers" with an explicit transport type.
    vscode = {name: {"type": "stdio", "command": s["command"], "args": s["args"]} for name, s in servers}
    # Codex reads TOML from ~/.codex/config.toml; we generate a snippet to merge there.
    # json.dumps string escaping is valid TOML basic-string escaping.
    codex = ["# Generated from ai/approved-mcp.json. Merge into ~/.codex/config.toml."]
    for name, s in servers:
        args = ", ".join(json.dumps(a) for a in s["args"])
        codex += ["", f"[mcp_servers.{json.dumps(name)}]", f"command = {json.dumps(s['command'])}", f"args = [{args}]"]

    return {
        ".mcp.json": dump({"mcpServers": mcp_servers}),
        ".cursor/mcp.json": dump({"mcpServers": mcp_servers}),
        ".vscode/mcp.json": dump({"servers": vscode}),
        "ai/generated/codex-config.toml": "\n".join(codex) + "\n",
    }


def check_configs(root: Path = ROOT) -> list[str]:
    """Return problems; an empty list means every generated file matches the approved list."""
    approved = load_approved(root)
    problems = validate_approved(approved)
    for rel, expected in build_configs(approved).items():
        path = root / rel
        if not path.exists():
            problems.append(f"{rel} is missing. Run: make gen-mcp")
        elif path.read_text(encoding="utf-8") != expected:
            problems.append(f"{rel} does not match ai/approved-mcp.json (edited by hand?). Run: make gen-mcp")
    return problems


def main() -> int:
    if "--check" in sys.argv:
        problems = check_configs()
        for p in problems:
            print(f"✗ {p}", file=sys.stderr)
        if not problems:
            print("✓ MCP configs match ai/approved-mcp.json")
        return 1 if problems else 0
    approved = load_approved()
    problems = validate_approved(approved)
    if problems:
        for p in problems:
            print(f"✗ {p}", file=sys.stderr)
        print("Nothing written. Fix ai/approved-mcp.json first.", file=sys.stderr)
        return 1
    for rel, content in build_configs(approved).items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
