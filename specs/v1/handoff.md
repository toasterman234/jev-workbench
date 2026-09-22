# Implementation handoff status

> Historical record. Everything marked outstanding below has since been done —
> the repository is pushed, the production React workbench replaced the design
> draft, and the UI now follows `specs/dropagent-visual/spec.md`. For current
> state read `AGENTS.md`, `README.md`, and `VALIDATION.md`.

The repository was built from an empty directory. `spec.md` was the only contract; the user later authorised offline simulation, since there was no key yet.

Implemented: the React/Vite workbench, Fastify, SQLite migrations, the strict DSL, the provider, version publishing, permissions/sessions/secrets, HTTP, the SDK MCP bridge, the Pi extension, integration plan/apply/revoke, the background CLI, and a separate demo mode. The user's real agent config was never silently modified; the real Claude CLI check was limited to a temporary project.

Running: `pnpm demo` opens 17430 against `~/.jev-workbench-demo` with a permanent demo banner and a seeded `ticket_route@1`, four cases, and a restricted API credential. Production 17420 was stopped; without a key it still supports configuration but refuses inference.

Acceptance entry points and gaps: README.md and VALIDATION.md. Real provider inference and model calls from the actual agents were to be verified once a key and the runtimes were available, and did not count as evidence of the simulated completion.

Later work should start from the spec and those two files rather than from chat. Build before testing, because the MCP and lifecycle tests use the real `dist`. Never copy the demo database or credentials into the repository.

## User course-correction, 2026-09-18: single-page design draft first

The user found the pages complicated and asked for a Coss-UI look, one integrated page, and all three primitives visible. A bilingual interactive draft was delivered as `design/single-page/index.html`, with `specs/single-page/spec.md` as its contract. It did not replace the production React app. Checks on the three primitives, edit retention across languages, save and restore, failure and review states, and responsiveness all passed; an independent review concluded "ship as interactive design draft".

Outstanding at the time: the initial Git commit and the push to molis-ai. The organisation had been checked for a name clash and creating the private molis-ai/jev-workbench was authorised, to be done after the production rework — the design draft was not to be treated as the complete deliverable.

Also outstanding at the time: the English production UI work was interrupted by the course correction. `en.json` and `i18n.ts` had been added, most of the UI translated, an English ticket example and English demo triggers added, and typecheck passed. Still to do were English coverage for API errors and integration messages, an English README, a bilingual production e2e run, a fresh build and test run, and removing two temporary i18n migration scripts. The demo on 17430 was still a pre-correction build. The earlier record of 20 passing tests was not to be presented as acceptance of any of this.
