# One set of commands for every language and every AI tool. See AGENTS.md.
PYTHON ?= python3

.PHONY: test test-web test-orders test-payments test-tools check-ai scan-secrets gen-mcp hooks

test: test-tools test-web test-orders test-payments

test-web:
	cd services/web && npm ci --silent --ignore-scripts && npm run typecheck && npm test

test-orders:
	cd services/orders && ./mvnw -q verify

test-payments:
	cd services/payments && $(PYTHON) -m pytest -q

test-tools:
	cd tools && $(PYTHON) -m unittest -q

check-ai:
	$(PYTHON) tools/check_ai_layer.py

scan-secrets:
	$(PYTHON) tools/scan_secrets.py

gen-mcp:
	$(PYTHON) tools/gen_mcp_configs.py

# Turn on the shared pre-commit hook for this clone.
hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit
	@echo "Pre-commit hook enabled: secret scan + AI layer check on every commit."
