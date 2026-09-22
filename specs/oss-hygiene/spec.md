# Open-source hygiene and a no-key contract check

## Goal

Bring the repository up to common open-source standards, and verify the call logic against the public TypeSafe documentation. There is no Jev API key, so neither a simulation nor a documentation comparison may be reported as a passing cloud call.

## Scope

- Add LICENSE, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md. Drop the machine-specific narration from the README and add the repository, licence, and the two API entries.
- Remove unused imports, state, and dependencies. `GET /v1/models` no longer sends a meaningless Content-Type.
- Tighten Score against the official docs: `score` must equal `Σ i·P(i)` within a 0.05 tolerance.
- Add `tests/official-contract.test.ts`: verify the official body, all three primitive answer shapes, Noul having no confidence, and the model echo rule on the function path, using the published examples.
- Update the test count and the no-key boundary in VALIDATION.md.

## Non-goals

- Do not connect to real TypeSafe, and do not change the product boundary of the function or official call paths.
- Do not delete old style blocks that CSS selectors may still depend on.
- Do not add a CI workflow.
