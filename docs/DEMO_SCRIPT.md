# Demo script (about 15 minutes)

Run from the repo root, with the hook enabled (`make hooks`). Each step shows one layer.
Undo each change before the next step with `git checkout -- .` (and `git reset` if you staged anything).

## 1. One set of rules, every tool (4 min)

Show `AGENTS.md`, then `services/orders/AGENTS.md`, then `CLAUDE.md` (one line).

Then the live part. Ask the **same request** in two or three tools, for example Claude Code and Cursor:

> In services/orders, add a method that applies a percentage discount to an order total.

What to point out:
- Both read the same rules: `long` cents, `Math.multiplyExact`, `IllegalArgumentException`, a JUnit 5 test with a failure case.
- Neither was told the rules in the prompt. They came from AGENTS.md.
- Try the same in `services/payments` to show the stricter nested rules (no logging of card details, failure-path test).

## 2. Someone copies rules into a tool's own file (2 min)

```bash
echo "Always use tabs." >> CLAUDE.md
make check-ai
```
Result: the check fails and names `CLAUDE.md`: rules belong in AGENTS.md, so they can't drift apart.

```bash
echo "Use 2 spaces." > .cursorrules
make check-ai
```
Result: fails on the legacy `.cursorrules` file.

## 3. Someone adds an unvetted MCP server by hand (2 min)

Open `.cursor/mcp.json` and add a server inside `mcpServers`:
```json
"random-server": { "command": "npx", "args": ["-y", "some-unvetted-mcp"] }
```
```bash
make check-ai
```
Result: fails, because `.cursor/mcp.json` no longer matches `ai/approved-mcp.json`.
The right way: add it to `ai/approved-mcp.json` after review, then `make gen-mcp`, which updates all four tools' configs at once.

## 4. An agent hard-codes a secret (3 min)

This command appends a fake API key to the payments code, as an agent might (the key is split
in the command so this script doesn't trip the scanner itself):
```bash
printf 'API_KEY = "%s%s"\n' 'sk-ant-' 'api03-FAKEFAKEFAKEFAKEFAKE' >> services/payments/payments/charges.py
git add services/payments/payments/charges.py
git commit -m "add key"
```
Result: the pre-commit hook blocks the commit and points at the file and line.
CI runs the same scan plus gitleaks, so a bypassed hook (`--no-verify`) still gets caught.

## 5. The pull request (2 min)

Open `.github/pull_request_template.md`: every PR says which AI tool was used, what it generated and
what the author verified. Show `.github/workflows/ai-guardrails.yml`: one job for the AI layer and secrets,
one per language. Make it a required check.

## 6. Wrap-up (2 min)

- Developers keep their tool. The rules, integrations and checks are shared.
- Adding a tool next year means adding one pointer file at most.
- Next step: copy this baseline into one real repo and write its AGENTS.md together.
