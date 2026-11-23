#!/usr/bin/env python3
"""Check that the shared AI layer has not drifted.

1. AGENTS.md exists at the root, and every AGENTS.md stays short enough for agents to follow.
2. Tool-specific instruction files only point to AGENTS.md (no second copy of the rules).
3. Legacy or alternative per-tool rule files are not added.
4. Committed agent settings do not switch off permission prompts.
5. Every tool's MCP config matches ai/approved-mcp.json, and that list meets the approval rules.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_mcp_configs import ROOT, check_configs  # noqa: E402

MAX_AGENTS_LINES = 150
SKIP_DIRS = {".git", "node_modules", "target", ".venv", "venv", "__pycache__", ".pytest_cache"}

# Files that must contain nothing but a pointer to AGENTS.md. A pointer is one of these exact lines.
POINTER_FILES = {"CLAUDE.md", "GEMINI.md", "copilot-instructions.md"}
POINTER_LINES = {"@AGENTS.md", "Follow the instructions in AGENTS.md at the repository root."}

# Other places tools read rules from. Rules there would bypass AGENTS.md, so none are allowed.
FORBIDDEN_FILES = {".cursorrules", ".windsurfrules", ".clinerules", "CLAUDE.local.md"}
FORBIDDEN_DIRS = {".cursor/rules", ".windsurf/rules", ".clinerules", ".github/instructions"}

# Committed Claude Code settings must not remove the human from the loop.
CLAUDE_SETTINGS = {".claude/settings.json"}
BROAD_ALLOW_RULES = {"Bash", "Bash(*)", "Bash(:*)", "*"}


def pointer_problem(path: Path, rel: str, root: Path) -> str | None:
    if path.is_symlink():
        return None if path.resolve() == (root / "AGENTS.md").resolve() else \
            f"{rel}: symlink must point to AGENTS.md."
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    extra = [line for line in lines if line not in POINTER_LINES]
    if extra or not lines:
        first = f' (first: "{extra[0][:60]}")' if extra else ""
        return (f"{rel}: must contain only a pointer to AGENTS.md "
                f"({' or '.join(sorted(POINTER_LINES))}){first}. Move any rules into AGENTS.md.")
    return None


def settings_problems(path: Path, rel: str) -> list[str]:
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"{rel}: not valid JSON."]
    permissions = settings.get("permissions", {}) if isinstance(settings, dict) else {}
    problems = []
    if permissions.get("defaultMode") == "bypassPermissions":
        problems.append(f"{rel}: defaultMode 'bypassPermissions' turns off all permission prompts. Remove it.")
    broad = [rule for rule in permissions.get("allow", []) if rule in BROAD_ALLOW_RULES]
    if broad:
        problems.append(f"{rel}: allows any shell command ({', '.join(broad)}). Allow specific commands instead.")
    return problems


def check_ai_layer(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    if not (root / "AGENTS.md").exists():
        problems.append("AGENTS.md is missing at the repo root.")

    for path in sorted(root.rglob("*")):
        rel_path = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel_path.parts):
            continue
        rel = rel_path.as_posix()
        if path.is_dir():
            if rel in FORBIDDEN_DIRS:
                problems.append(f"{rel}/: tool-specific rules folder. Delete it and put the rules in AGENTS.md.")
            continue
        if path.name == "AGENTS.md":
            lines = len(path.read_text(encoding="utf-8").splitlines())
            if lines > MAX_AGENTS_LINES:
                problems.append(f"{rel} has {lines} lines (limit {MAX_AGENTS_LINES}). Split it or move detail into docs.")
        elif path.name in FORBIDDEN_FILES:
            problems.append(f"{rel}: tool-specific rules file. Delete it and put the rules in AGENTS.md.")
        elif path.name in POINTER_FILES:
            if (p := pointer_problem(path, rel, root)):
                problems.append(p)
        elif rel in CLAUDE_SETTINGS:
            problems.extend(settings_problems(path, rel))

    problems.extend(check_configs(root))
    return problems



def main() -> int:
    problems = check_ai_layer()
    if problems:
        print("AI layer check failed:", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        return 1
    print("✓ AI layer OK: one AGENTS.md, pointer files only point, MCP configs match the approved list")
    return 0


if __name__ == "__main__":
    sys.exit(main())
