# AGENTS.md (services/web, TypeScript)

Adds to the root AGENTS.md.

## Commands (run in services/web)
- Install: `npm ci`
- Type-check: `npm run typecheck`
- Test: `npm test` (Node's built-in test runner on the .ts files)

## Conventions
- TypeScript `strict` mode. No `any`; use `unknown` and narrow it.
- ES modules only. Import local files with the `.ts` extension.
- Make all HTTP calls through `src/http.ts`. Never call `fetch` directly anywhere else.
- Format money for display with `formatCents` from `src/orderSummary.ts`; never divide cents by 100 inline.
- Tests live in `test/`, named `<module>.test.ts`, using `node:test` and `node:assert/strict`.
