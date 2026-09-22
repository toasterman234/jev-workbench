# Acceptance record · 2026-09-18

Completion level this round: **functional, with real TypeSafe**. On 2026-09-18 a production service key was used to run configure → preview → publish → HTTP call, plus the official `/v1/systemone`. Agent runtimes offer optional install/uninstall of the official TypeSafe skill, and write nothing before confirmation; tests use a fake `npx` and never touch the local Claude or Codex setup.

## Environment and results

macOS ARM64, Node v24.14.0, pnpm 11.9.0, better-sqlite3 12.11.1, MCP SDK 1.30.0; Chromium 153 (Playwright 1.63).

- `pnpm typecheck`: pass.
- `pnpm build`: pass — same-origin SPA, service, MCP bridge, and the complete Pi extension package are all produced; the editor is split into its own chunk.
- `pnpm test`: 33 pass, covering the official public-example contract, official-entry grant isolation, archive/delete, and the shared HTTP/MCP/Pi contract.
- `pnpm test:e2e`: one complete bilingual browser story passes — create Choice → preview → save a case → publish → leave an unsaved edit → create Noul and Score → edit and preview in English → return to the first function with its draft intact → pinned-grant HTTP call → token cleared → archive/restore → trash/restore/permanent delete → search → phone width → language survives reload. No page JS errors.
- Layout verified at 1440 and 1024 with no vertical page scroll, and at 390 with no horizontal document overflow. An independent visual review found two problems — the narrow-width preview grouping and the phone grant row — both fixed and re-reviewed as resolved. Screenshots are in `.impeccable/review`.

## Acceptance matrix against the spec

| Scope | Status | Evidence and boundary |
|---|---|---|
| string / number / boolean / string[] input, unknown fields rejected, no implicit coercion | pass | engine tests; forms plus a limited JSON Schema subset |
| Noul, Choice, Score / any, all / interval endpoints / null review output | pass | engine production-path tests; probability is explicitly not accuracy |
| Missing path, dangerous path, incomplete enum map, model mismatch, corrupt answer | pass | publish and execution contracts reject the error instead of falling back to a default category |
| configure → preview → publish → call | pass (simulated) | browser e2e plus a real HTTP call against the demo service |
| Revision conflict, old version immutable, v2 does not affect a pinned v1, rollback | pass | integration tests assert final DB state and the following call |
| Missing token, over-scope, revocation, list isolation, admin isolation | pass | integration tests; a grant pins a version by default and can explicitly follow the default |
| Host, Origin, session, CSRF, one-time bootstrap | pass | integration tests; the launch URL uses a fragment that the browser strips, and a restart invalidates sessions |
| Key encryption, file permissions, runs store no bodies, client tokens hashed only | pass | real file and DB inspection, AES-GCM round-trip; explicitly saved cases are the documented exception |
| 429/529 bounded retry, 401/422 and network error classification, concurrency queue and cancel | pass (contract) | provider and gate tests; the deadline spans the network wait. Not yet a cloud load test |
| Saved cases, assertion runs, state after delete | pass | persistence and assertion tests; a deliberately wrong case is expected to fail at run time |
| HTTP / MCP / Pi share one version and result contract | pass (fixture) | real stdio subprocess through the SDK, plus HTTP and Pi `registerTool`; behaviour after revoke and offline |
| MCP still registers tools while offline and reports unavailable on call | pass | tools called through the SDK after actually stopping the backend |
| OpenCode JSONC keeps comments, other MCP servers, preview conflicts, revoke keeps later edits | pass | temporary directories containing spaces, real file I/O, final content checked |
| Pi install/remove and tool forwarding | pass (files and contract) | loader file and the complete dist extension package generated; the Pi CLI was not run |
| Claude project install/revoke | pass (real CLI) | Claude Code 2.1.206 in an isolated temporary project; existing and later-added MCP entries preserved; no model message sent |
| Codex user-scope install, Claude user scope | not run | CLI version and command arguments verified; the user's real agent config was not modified |
| OpenCode / Pi actually loading in their runtimes | not run | neither CLI is installed on this machine |
| Start/stop, double start, port conflict, instance validation, restart recovery | pass | lifecycle tests launch the real built process; no kill is sent to an unverified PID |
| Production start and preview without a key | pass | the UI stays editable, the provider returns 503 `PROVIDER_NOT_CONFIGURED`, and nothing falls back |
| Offline demo isolated from production publishing | pass | separate port and directory, permanent banner; reopening a fixture-tainted database in production still refuses to publish from it |
| Official `/v1/systemone` and `/v1/models` grant isolation | pass (fixture) | 403 without the grant, 409 in demo, 503 without a key; question bodies are never stored |
| Noul / Choice / Score answer shapes from the public TypeSafe docs | pass (no key) | `tests/official-contract.test.ts` uses the complete 2026-09-17 documentation examples; Score is checked as Σ i·P(i) |
| `GET /v1/models` HTTP shape | pass (mock transport) | fixed to `https://api.typesafe.ai/v1/models`, GET sent without Content-Type |
| Real TypeSafe inference and real agent runtimes | partial (2026-09-18, real key) | Production 17420: `GET /v1/models` returned the `jev-latest` / `jev-preview` aliases; requesting `jev-1.13.0` echoed `model` back unchanged. A duplicate-charge ticket previewed `ok/billing` and an ambiguous one `needs_review/unclassified`; after publishing v1 a client invoke returned the same `ok/billing` with `simulated=false`. Official `POST /v1/systemone` returned Noul `0.98` with usage. No agent runtime has yet made a real tool call |
| Business accuracy calibration, macOS x64 / Windows / Linux distribution | not run | not something a local simulated pass can demonstrate |

## Added for the left/right workbench

The production React interface replaced the old navigation and list pages: directory on the left, content on the right, advanced config and connections expanding in place. Screenshots are in `.playwright`. A v2 database migration preserves existing functions and cases. Trash can be restored, blocks business calls, and hides the function from agent lists. Permanent delete is allowed only from Trash; the API clears that function's versions, test cases, grants, and runs in one transaction, refuses while a call is running, and still enforces CSRF. Other functions and clients are untouched. Archive and restore were verified by real call behaviour before and after. All three primitive result views come from real execution-engine output, with simulated status stated plainly.

中文 and English cover the main forms, statuses, create/delete/connect flows, and error summaries. Configuration, cases, and history text the user wrote are never auto-translated, and field-level diagnostics keep their original wording. English docs are in README.md; Chinese in [README.zh.md](README.zh.md).

## Added for the DropAgent visual rebuild

The front end was rebuilt against the contract in [specs/dropagent-visual/spec.md](specs/dropagent-visual/spec.md): shared palette, reorganised shell, dark default with a light toggle, and per-column scrolling in the editor. Verified by the unchanged e2e story — including its 1440 / 1024 no-page-scroll and 390 no-horizontal-overflow assertions — plus a manual check that expanding advanced config scrolls only its own column, and that both themes render the whole app including the JSON editor. Tailwind was removed; the built CSS is byte-identical without it, which confirms no utility class was in use.

## Reproducible demo

`pnpm demo` starts on 17430 with a seeded ticket-routing v1 and four saved cases.

```sh
pnpm demo:call
pnpm demo:call 'unclear, needs review'
pnpm demo:call 'simulate error'
pnpm demo:call 'simulate timeout'
```

The first two return `ok/billing` and `needs_review/null`; the last two return the 502 and 504 error contracts and the script exits 1 as expected. Simulated responses are marked `meta.simulated=true` and never claim a model was used. The reported duration is real local time spent simulating, not model performance.

## Current limits

- The Codex CLI can be configured automatically at user scope. It has no equivalent project-scope argument, so the product only prepares manual instructions rather than writing to the wrong scope.
- For unrecognised Claude or Codex versions the product prepares the command and credential only, and does not modify the config.
- Upgrading requires keeping the whole source project and its dependencies; there is no cross-platform installer or signed distribution yet.
- When only the connection initialisation has been tested, status never claims the target agent has loaded or that a model call succeeded.
