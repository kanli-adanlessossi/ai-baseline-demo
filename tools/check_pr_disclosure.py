#!/usr/bin/env python3
"""Fail a pull request whose AI disclosure is not filled in.

CI passes the pull request description in the PR_BODY environment variable
(never interpolated into the shell command, so a crafted description cannot run code).
"""
from __future__ import annotations

import os
import re
import sys

NO_AI = re.compile(r"^\s*-\s*\[[xX]\]\s*No AI tool was used", re.M)
USED_AI = re.compile(r"^\s*-\s*\[[xX]\]\s*AI was used", re.M)
COMMENT = re.compile(r"<!--.*?-->", re.S)


def section(body: str, heading: str) -> str:
    """Text under a `Label:` line, up to the next `Label:` line or `##` heading, without HTML comments."""
    match = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^\S[^\n]*:[ \t]*$|^## |\Z)", body, re.M | re.S)
    return COMMENT.sub("", match.group(1)).strip() if match else ""


def check(body: str) -> list[str]:
    no_ai, used_ai = bool(NO_AI.search(body)), bool(USED_AI.search(body))
    if no_ai == used_ai:
        return ["Tick exactly one AI disclosure box: 'No AI tool was used' or 'AI was used'."]
    if used_ai:
        problems = []
        if not section(body, "What the AI generated:"):
            problems.append("Say what the AI generated.")
        if not section(body, "What I verified myself:"):
            problems.append("Say what you verified yourself.")
        return problems
    return []


def main() -> int:
    problems = check(os.environ.get("PR_BODY", ""))
    for p in problems:
        print(f"✗ {p}", file=sys.stderr)
    if problems:
        print("Fill in the AI disclosure section of the pull request description.", file=sys.stderr)
        return 1
    print("✓ AI disclosure complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
