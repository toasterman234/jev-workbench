# Jev Workbench project facts

- Node 24 / pnpm 11.9.0 / TypeScript. React + Vite SPA served same-origin by Fastify; better-sqlite3.
- Base contract: specs/v1/spec.md. Confirmed revisions: specs/single-page/spec.md (left list / right content, delete, bilingual), specs/settings-split/spec.md, specs/cc-switch-agents/spec.md (nine runtimes), specs/dropagent-visual/spec.md (current UI). The tail of specs/single-page/spec.md records the user-authorised offline demo mode and the current runtime scope.
- Commands: pnpm typecheck; pnpm build; pnpm test; pnpm test:e2e.
- Production defaults to 127.0.0.1:17420 and ~/.jev-workbench; demo to 17430 and ~/.jev-workbench-demo. Tests use temporary directories and ports 17423/17425/17426/17428/17429.
- Every entry point shares one Invoker. MCP and Pi read only their own credential file — never the database or the vendor key.
- Never fall back after a real provider failure. Fixtures are for explicit test or demo mode only. Publishing requires a successful preview of the current checksum and a pinned model version.
- A published release is immutable. Drafts use optimistic locking. A client token must never gain admin capability.
- Never write raw input, answers, or secrets to logs, runs, or Git. A saved test case is the one exception the user opts into.
- Runtime config changes are plan-then-apply, touch only this product's entry, and stop on conflict. Never silently rewrite the user's existing agent config just to verify something.
- Run from the project root. Build output is in dist (git-ignored) and screenshots in .impeccable/review (git-ignored); run pnpm build before the MCP and lifecycle tests, which exercise the built artefacts.
- Docs are English. README.zh.md is the one deliberate exception; keep it in sync with README.md. Chinese literals in apps/web/src are i18n keys — en.json maps them to English — so do not "translate" them in place.
