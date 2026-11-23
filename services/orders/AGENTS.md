# AGENTS.md (services/orders, Java)

Adds to the root AGENTS.md.

## Commands (run in services/orders)
- Build and test: `./mvnw -q verify` (the Maven Wrapper downloads the pinned Maven version; no local Maven needed)
- Test one class: `./mvnw -q test -Dtest=OrderTotalsTest`
- Never edit `mvnw`, `mvnw.cmd` or `.mvn/wrapper/` by hand.

## Conventions
- Java 21. Use records for immutable data (see `LineItem`).
- Money is `long` cents. Never use `double`, `float` or `BigDecimal` for amounts in this service.
- Use `Math.addExact` / `Math.multiplyExact` so overflow throws instead of wrapping silently.
- Throw `IllegalArgumentException` with a clear message for invalid input. Never return null.
- Tests use JUnit 5 (`org.junit.jupiter`), one test class per production class, in the same package.
