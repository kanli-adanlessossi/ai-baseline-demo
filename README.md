# AI baseline demo

A small repo with three services (TypeScript, Java, Python) that shows how to standardize
**the layer around AI coding tools**, so Claude Code, Codex, Cursor and Copilot all follow the same rules.

Developers keep their preferred tool. What's shared is everything around it:

| Layer | What's standard | Files |
| --- | --- | --- |
| 1. Instructions | One `AGENTS.md` at the root, plus one per service for language rules. Other tools' files only point to it. | `AGENTS.md`, `services/*/AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` |
| 2. Integrations | One approved list of MCP servers, pinned to exact versions and run read-only, generated into each tool's config format | `ai/approved-mcp.json` → `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, `ai/generated/codex-config.toml` |
| 3. Guardrails | Secret scanning and a drift check on every commit and pull request, whichever tool wrote the code | `.githooks/pre-commit`, `.github/workflows/ai-guardrails.yml`, `tools/` |
| 4. Review | AI disclosure checked on every pull request; named owners approve changes to the AI layer and to payments | `.github/pull_request_template.md`, `.github/CODEOWNERS` |

Account settings (SSO, data retention, no training on your code, spending caps) live in each vendor's
admin console, not in the repo. See the AI acceptable-use policy.

## Layout

```
AGENTS.md                      shared rules for every tool and language
CLAUDE.md                      one line: @AGENTS.md
.github/copilot-instructions.md  one line pointing to AGENTS.md
ai/approved-mcp.json           the only place MCP servers are added
services/web/       TypeScript  + its own AGENTS.md
services/orders/    Java 21     + its own AGENTS.md, Maven Wrapper (mvnw)
services/payments/  Python      + its own AGENTS.md (sensitive code, stricter rules)
tools/                         drift check, MCP config generator, secret scanner (Python stdlib only)
```

## Try it

Requirements: Git, Python 3.11+, and for the services you want to run: Node 22.18+ and Java 21.
Maven is not needed: `services/orders/mvnw` downloads the pinned Maven version on first use.

The repo uses hidden folders (`.github/`, `.githooks/`, `.cursor/`, `.vscode/`) and files (`.mcp.json`, `.gitignore`).
Finder and File Explorer hide them by default: press Cmd+Shift+. on a Mac, or turn on "Hidden items" in Windows.
Push with Git rather than a web upload, so they are included.

```bash
git init && git add . && git commit -m "AI baseline"   # skip if you cloned it
make hooks        # turn on the pre-commit hook for this clone
make check-ai     # ✓ AI layer OK
make scan-secrets # ✓ No secrets found
make test         # tools + all three services
```

## How each tool picks up the rules

| Tool | Reads | Notes |
| --- | --- | --- |
| Codex | `AGENTS.md` (nested files too) | Native. MCP servers: merge `ai/generated/codex-config.toml` into `~/.codex/config.toml`. |
| Cursor | `AGENTS.md` | Native. MCP servers from `.cursor/mcp.json`. |
| GitHub Copilot | `AGENTS.md`, `.github/copilot-instructions.md` | The pointer file covers setups where AGENTS.md support is off. MCP servers from `.vscode/mcp.json`. |
| Claude Code | `CLAUDE.md` → `@AGENTS.md` | Claude Code also reads AGENTS.md when there's no CLAUDE.md, but the import line works in every setup. MCP servers from `.mcp.json`. |

MCP servers read their tokens (for example `GITHUB_PERSONAL_ACCESS_TOKEN`) from the environment of
the tool that starts them. Never put token values in `ai/approved-mcp.json`.

## Security and governance

What the checks enforce:

- **Rules in one place.** Pointer files may contain only an exact pointer line (or be a symlink to AGENTS.md).
  Other rules locations (`.cursorrules`, `.cursor/rules/`, `.github/instructions/`, `.windsurf/rules/`, `CLAUDE.local.md`) fail the check.
- **MCP servers.** Each entry needs an approver and date, a runner of `npx`, `uvx` or `docker`, an exact package
  version or image tag (no `latest`), and environment variable names only. Privileged containers and the Docker
  socket are refused. Both example servers run in read-only mode.
- **Agent permissions.** A committed `.claude/settings.json` may not set `bypassPermissions` or allow any shell command.
- **Secrets.** The pre-commit hook scans what is actually staged. CI scans again and runs gitleaks over the full
  history. Every `secret-scan:allow` exemption is listed on each run, and gitleaks ignores it.
- **Pull requests.** CI fails until one AI disclosure box is ticked, and, if AI was used, the author says what it
  generated and what they verified. The description is passed to the check as data, so it cannot inject commands.
- **CI supply chain.** Actions are pinned to commit SHAs, checkout keeps no credentials, every job has a timeout,
  `npm ci` runs with `--ignore-scripts`, and Dependabot proposes updates as reviewed pull requests.

What only GitHub settings can enforce (do these when you adopt it):

1. Branch protection on `main`: require pull requests, require the `AI guardrails` jobs to pass,
   and turn on **Require review from Code Owners**.
2. Replace the placeholder teams in `.github/CODEOWNERS` with your own.
3. Turn on GitHub secret scanning and push protection, if your plan includes them.

What no repo file can enforce: which AI tool someone uses on `services/payments` (the policy's Supported tier),
SSO and data-retention settings (vendor admin consoles), and MCP servers a developer adds to their personal,
user-level config. CODEOWNERS review and the vendor admin consoles cover these.

The local pre-commit hook is a convenience: it is opt-in (`make hooks`) and can be skipped with `--no-verify`.
CI is the enforcement point.

## Rolling it out

1. Agree the root `AGENTS.md` with two or three developers who use different tools.
2. Turn this repo into a template (`ai-baseline`) and copy its `AGENTS.md`, pointer files, `ai/`, `tools/`,
   hook, workflow and PR template into each real repo, one pull request per repo.
3. Write each repo's own build commands and conventions into its `AGENTS.md` files.
4. Apply the GitHub settings listed under Security and governance.

See `docs/DEMO_SCRIPT.md` for a 15-minute walkthrough to run with the team.
