# AGENTS.md (services/payments, Python)

Adds to the root AGENTS.md. **This is sensitive code** under the AI acceptable-use policy:
only tools in the **Supported** tier may work here.

## Commands (run in services/payments)
- Install dev tools: `pip install -e ".[dev]"`
- Test: `pytest -q`

## Conventions
- Python 3.11+, type hints on every function, dataclasses for structured data.
- Amounts are `int` cents. Reject `bool`, `float` and anything not a positive integer.
- Never log card numbers, tokens or customer names. Log the payment ID only.
- Make HTTP calls through the injected `post` function so tests never hit the network.
- Every change needs a test for the failure path, not just the happy path.

## Review
- Agents may propose changes, but a human from the payments owners must approve the pull request.
