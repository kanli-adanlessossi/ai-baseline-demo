## What changed

<!-- One or two sentences. Which service(s)? -->

## AI disclosure (required by the AI acceptable-use policy)

- [ ] No AI tool was used for this change
- [ ] AI was used. Tool(s): <!-- e.g. Claude Code, Codex, Cursor, Copilot -->

What the AI generated:
<!-- e.g. "first draft of OrderTotals.totalCents and its tests" -->

What I verified myself:
<!-- e.g. "read every line, ran the tests, added the overflow case the AI missed" -->

## Checklist

- [ ] Tests pass for every service I touched (`make test-web` / `make test-orders` / `make test-payments`)
- [ ] `make check-ai` passes
- [ ] No secrets, tokens or customer data in the diff
- [ ] I can explain every line of this change in review
- [ ] Payments changes only: reviewed by a payments owner
