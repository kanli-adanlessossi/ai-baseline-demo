#!/usr/bin/env python3
"""Lightweight secret scanner with no dependencies, so the demo runs anywhere.

In real repos, also run a dedicated scanner such as gitleaks (see .pre-commit-config.yaml and CI).

Usage:
  python3 tools/scan_secrets.py           scan all files tracked by git
  python3 tools/scan_secrets.py --staged  scan only staged files (used by the pre-commit hook)

Silence a known false positive by adding "secret-scan:allow" on that line. Every exemption is
listed on each run, and gitleaks in CI ignores the marker, so it cannot hide a real key.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("Hard-coded credential",
     re.compile(r"""\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['"][^'"\s]{8,}['"]""", re.I)),
]


ALLOW_MARKER = "secret-scan:allow"


def scan_text(text: str, file: str = "") -> list[tuple[str, int, str]]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for name, pattern in PATTERNS:
            if pattern.search(line):
                findings.append((file, number, name))
    return findings


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def files_to_scan(staged: bool) -> list[tuple[str, str]]:
    """Return (path, content) pairs.

    Staged mode reads the content from the git index (what will actually be committed),
    not from the working tree, so a secret that is staged and then deleted locally is still caught.
    """
    if staged:
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0")
        read = lambda name: git("show", f":{name}")  # noqa: E731
    else:
        names = git("ls-files", "-z").split("\0")
        read = lambda name: (ROOT / name).read_text(encoding="utf-8")  # noqa: E731
    result = []
    for name in filter(None, names):
        if not staged and not (ROOT / name).is_file():
            continue
        try:
            result.append((name, read(name)))
        except (UnicodeDecodeError, subprocess.CalledProcessError):
            continue  # binary or unreadable file
    return result


def main() -> int:
    try:
        files = files_to_scan("--staged" in sys.argv)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Not a git repository (or git is not installed). Run `git init` first.", file=sys.stderr)
        return 2
    findings = [f for name, text in files for f in scan_text(text, name)]
    # Lines the marker actually silences are listed every time, so reviewers can see what is exempted.
    allowed = [(name, i) for name, text in files
               for i, line in enumerate(text.splitlines(), start=1)
               if ALLOW_MARKER in line and scan_text(line.replace(ALLOW_MARKER, ""))]
    for name, i in allowed:
        print(f"  note: {name}:{i} is exempted with '{ALLOW_MARKER}'", file=sys.stderr)
    if findings:
        print("✗ Possible secrets found. Remove them, use environment variables, and rotate anything real:",
              file=sys.stderr)
        for file, line, name in findings:
            print(f"  {file}:{line}  {name}", file=sys.stderr)
        return 1
    print(f"✓ No secrets found in {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
