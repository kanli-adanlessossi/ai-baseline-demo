# AGENTS.md

Instructions for every AI coding tool used in this repo (Claude Code, Codex, Cursor, Copilot and others).
This file is the single source of truth. Tool-specific files (CLAUDE.md, .github/copilot-instructions.md) only point here.

## Repo layout
| Path | Language | What it is | Its own rules |
| --- | --- | --- | --- |
| `services/web/` | TypeScript (Node 22+) | Order summary for the web front end | `services/web/AGENTS.md` |
| `services/orders/` | Java 21, Maven Wrapper | Order totals and validation | `services/orders/AGENTS.md` |
| `services/payments/` | Python 3.11+ | Payment requests (sensitive code) | `services/payments/AGENTS.md` |
| `tools/` | Python 3 (stdlib only) | AI-layer checks and generators | this file |

Before changing a service, read its own AGENTS.md. It adds to these rules; it does not replace them.

## Commands (run from the repo root)
- All tests: `make test` (or one service: `make test-web`, `make test-orders`, `make test-payments`)
- AI layer drift check: `make check-ai`
- Secret scan: `make scan-secrets`
- Regenerate MCP configs after editing `ai/approved-mcp.json`: `make gen-mcp`
- Before saying a task is done, run the tests for every service you touched, plus `make check-ai`.

## Rules for all languages
- Money is always an integer number of cents. Never use floating-point types for amounts.
- Validate inputs at the edge of each public function and fail with a clear error.
- Every public function or method has a unit test, including at least one failure case.
- Keep changes inside one service unless the task says otherwise. Services talk over HTTP, never by importing each other's code.

## Never
- Commit secrets, tokens or real customer data. Use environment variables.
- Add a dependency (npm, Maven or pip) without approval from a maintainer.
- Hand-edit `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` or anything in `ai/generated/`.
  Change `ai/approved-mcp.json` and run `make gen-mcp` instead (security must approve; see CODEOWNERS).
- Weaken, skip or edit the checks in `tools/`, `.githooks/` or `.github/workflows/` to make a task pass.
  If a check blocks you, stop and say why.
- Add `secret-scan:allow` to silence the secret scanner. Only a person may add it, for a proven false positive.
- Commit agent settings that turn off permission prompts or allow any shell command.

## Definition of done
- Tests added or updated, and they pass.
- `make check-ai` passes.
- The pull request description states what AI generated and what you verified.
