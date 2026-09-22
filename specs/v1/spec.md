# Jev Workbench v1 — local browser edition development spec

**Scope:** single user, runs locally, inference on official Jev in the cloud, configurable judgment functions, an HTTP API, MCP, and a Pi extension.
**Sources checked:** 2026-09-18. Every path, interface, config format, limit, and page interaction here is this product's proposed design unless explicitly marked as an official fact.
**Nature of the deliverable:** this document is a development spec; the accompanying HTML is a backend-free interactive prototype. Jev was not actually called, and no agent was installed or connected on the user's machine.

## 1. Product definition and first-version boundary

The user configures "input → questions → rules → output" in the browser, previews it, and publishes it as an immutable version. Business services call the HTTP API with a configured key; Claude Code, Codex, and OpenCode call over MCP; Pi calls through a native extension. Every entry point shares one execution engine and the same published config.

The first version must deliver: function management, input field configuration, multi-question configuration, output mapping and review rules, draft preview, saved cases, publish and roll back the default version, scoped call credentials, the HTTP API, the MCP bridge, the Pi extension, config-change preview and recovery, basic call records, and start/stop.

The first version explicitly does not do: OpenJev weight download or local inference, a desktop installer, cloud multi-tenancy, a chat interface, proxying main-model traffic, workflow DAGs, arbitrary script/SQL/shell execution, automating business systems, webhooks, scheduled jobs, a persistent job queue, Redis, result caching, billing or quota systems, or OS startup registration.

"Local" means the admin interface, configuration, credential management, call entry points, and records are local; the state and questions sent to Jev still travel to TypeSafe. The production interface permanently displays "local control, cloud inference". [S1][S2]

The product's success path: start the service → set the key in the browser → create a function → fill in a sample and test → publish v1 → create a client and grant it → a successful curl → an agent successfully calling the same version.

## 2. Technology choices

| Layer | Choice | Constraint |
|---|---|---|
| Runtime | Node.js 24 LTS, TypeScript, pnpm workspace | Commit an exact lockfile and packageManager; never pull latest at production start |
| Front end | React + Vite | An SPA. No SSR, no Next.js, no second front-end server |
| Front-end state | TanStack Query for server data; React Hook Form for the editing form | No parallel global Redux/Zustand holding the same draft |
| Editor | Ordinary forms first; CodeMirror 6 for JSON and diffs | JSON and the form share one structured source of truth |
| HTTP service | Fastify, a single-process modular monolith | Serves the build output, the admin API, and the business API together |
| Persistence | better-sqlite3 plus raw SQL migrations | One local database, no ORM abstraction and no database server |
| Validation | Zod for the fixed API and config contracts; Ajv for the user function's input/output JSON Schema | A strictly limited JSON Schema subset; no remote `$ref` |
| Jev adapter | Node's own fetch plus AbortSignal and explicit, bounded retry | Two upstream endpoints; avoid an SDK retrying on top of our own |
| MCP | A stable release of the official TypeScript SDK, stdio transport | A separate lightweight process; never hand-roll the MCP protocol |
| Pi | A native TypeScript extension | Registers tools and calls the local API only; never intercepts the agent loop |
| Testing | Vitest, Fastify inject, Playwright, the MCP SDK client | Offline contract tests first, then an explicitly authorised real run with a key |

Node 24 is the current LTS; Vite and shadcn/ui document a React/Vite install path; the official MCP SDK supports stdio. [S8][S9][S10][S11]

> 2026-09-18: shadcn/ui and Tailwind were dropped. The component layer is plain CSS over Radix primitives — see `specs/dropagent-visual/spec.md`.

Because this version does no local OpenJev inference, there is no reason to bring in Python, PyTorch, or a separate GPU worker for model loading. One shared TypeScript contract across front end, back end, and Pi is enough.

## 3. Architecture and runtime shape

```text
Browser UI ─────────── admin API (local session) ────────┐
Business service ───── business API (scoped token) ──────┤
Claude/Codex/OpenCode → MCP stdio bridge ────────────────┤
Pi → native extension ───────────────────────────────────┤
                                                         ▼
                                       Fastify / one execution engine
                                        ├─ config and published versions
                                        ├─ credentials and grants
                                        ├─ input mapping, rules, output mapping
                                        ├─ log metadata
                                        └─ Jev provider → TypeSafe API
                                                 │
                                           local SQLite
```

Production listens on `127.0.0.1:17420` only. The browser opens `http://127.0.0.1:17420`, with static files and the API same-origin — no Nginx. During development Vite on 5173 may proxy the API to 17420; the development Origin allowlist must be enabled separately.

Closing the browser closes the interface, not the Node service. In foreground mode, exiting the terminal or pressing Ctrl-C stops the service; to keep it running across terminals, use this project's `service start` background mode. The Vite dev server is never a background daemon.

Each MCP client may start its own lightweight bridge, but those bridges never read the database, never hold the TypeSafe key, and never start another backend. They reach the existing service with their own scoped credential.

On a remote server, localhost means that server, not the user's computer. This version does not promise to serve cloud workloads over localhost; a cloud deployment would deploy the same backend separately and add network, TLS, and multi-user boundaries.

## 4. Domain model: a function is not a single question

```text
Function
  ├─ key / display name / draft / current default version / enabled
  ├─ Release v1 (immutable config snapshot)
  ├─ Release v2 (immutable config snapshot)
  └─ Test cases (inputs and assertions the user saved explicitly)

Client
  ├─ kind = api / mcp / pi
  ├─ its own call credential
  └─ Grants: which functions, at which pinned version
```

A release contains format_version, the full name/description/when_to_use, provider/model, input_schema, state_mapping, questions, review, output_mapping, and output_schema. The descriptive copy is part of the version snapshot too; display_name in the main list can be changed on its own, but it must never quietly change the contract of a published tool.

Function key, client token, and TypeSafe API key live in three separate namespaces. `ticket_route` is a public identifier, not a password; a random client token authenticates; the vendor key is for the backend only.

A function key cannot change once first published. Question ids and Choice option keys are business contracts too: changing them requires a new version. A question id inside a single Jev request is not the same thing as the key of a function we persist.

## 5. Official API adaptation boundary

Upstream facts: the evaluation endpoint is `POST https://api.typesafe.ai/v1/systemone` with bearer auth; the request is `{model, state, questions}` and answers are keyed by question id; the model list is `GET /v1/models`. [S1][S3]

| Type | Request criteria | Main answer |
|---|---|---|
| Noul | Optional true/false description | noul: the probability of yes; no separate confidence |
| Choice | Option key → description or null | choice, probabilities, confidence |
| Score | An ordered array of level descriptions, at least two | score, legend, probabilities, confidence; level indices start at 0 and score may be fractional |

The official model documentation currently lists `jev-1.13.0`. GET models may return only aliases right now, so a pinned version missing from the list must not be treated as invalid. A production release requires a pinned version and lets the user confirm it from the resolved_model of a real preview; aliases are fine for draft exploration but must never silently remain in a production release. [S3]

Confidence on Choice and Score is a statistic of the probability distribution, not business accuracy. Noul must never be given a fabricated confidence; treating 0.2–0.8 as a review band is the user's policy. Thresholds are never built in as a "universally correct answer". [S4]

Questions in one request see the same state independently and cannot consume each other's answers. In the first version a function issues one batch of independent questions and combines results afterwards; multi-stage flows that explicitly depend on a previous answer are out of scope. [S5][S6]

This version accepts JSON and text content only. It does not read arbitrary file paths, download user URLs, or parse PDFs and images. A caller that needs to handle files extracts the text first. The official state is a text payload today, not a local file handle. [S7]

## 6. Config DSL: limited, declarative, executes no code

A complete example is in `ticket_route.v1.json`. It is this product's format, not a request that can be sent straight to TypeSafe. The backend compiles state_mapping and questions into the official request; every other field executes locally.

### 6.1 Input

The v1 form supports string, number, boolean, and string[], with required/description/length or numeric range per field. The root input must be an object with additionalProperties=false by default. Advanced JSON editing allows only the same subset — no arbitrary `$ref`, no code execution, no remote schema.

Strings are never implicitly coerced to numbers, unknown fields are never silently dropped, and bodies are never silently truncated. A missing field or wrong type returns a field-level error. A missing optional field omits the corresponding state field; required fields are already caught during validation.

### 6.2 state_mapping

`{"ticket_text":"/content"}` reads `/content` from the validated input and builds `{ticket_text: ...}`. Paths use JSON Pointer semantics over own properties; dangerous segments such as `__proto__`, `constructor`, and `prototype` are forbidden. There is no Jinja, no eval, and no string-template expansion.

Question instructions live in the config. User text is always placed into state as data and never used to generate backend code or config paths. This does not claim to eliminate prompt injection at the model layer; it constrains the software execution boundary.

### 6.3 questions

A function allows 1–16 questions (this product's conservative ceiling, not an official hard limit), and Choice allows 2–32 options. The mapping to the official question shape stays direct. Stable option keys are kept separate from display names. Every question needs complete instructions; a question id alone must never carry the meaning.

### 6.4 Review rules

`review.match` supports any/all. An empty rules array never triggers review. Each rule is id/source/operator/value.

- eq/ne: strict equality or inequality within the same type.
- lt/lte/gt/gte: finite numbers only.
- in: a scalar present in a constant array.
- between_exclusive: a number strictly between `[min,max]`; equal to an endpoint does not match.

Strings as numbers, arbitrary functions, regex code execution, and cross-function calls are not supported. A missing read path or a type mismatch is a config or upstream contract error, never "the rule did not match".

When any or all of the specified rules match, the business status is needs_review and the matched rule ids are returned. That is a completed judgment, not an HTTP failure.

### 6.5 Output mapping

Each target field has a source, an optional enum_map, and an optional on_review. Sources in the first version are limited to `/answers/...` and `/input/...`. The source value is extracted first, then a total enum mapping is applied, then on_review overrides. A missing on_review field means keep the original value; an explicit null means blank it out on review. Publishing fails if enum_map is missing a possible value.

Field types are derived from the source and on_review to generate output_schema. Advanced mode may tighten it further within a compatible range but may not declare a schema that conflicts with the derived type. The actual data is still validated before every return.

The first version allows no arbitrary string generation, no overwriting the whole HTTP response, and no custom status codes — only customising the fields of data. A business service can forward the uniform envelope or take only data and shape its own interface.

## 7. Execution engine and return contract

Every entry point calls the same `invokeFunction(principal, key, version, input, signal)` application service.

1. Verify the local Host and Origin plus the client token; resolve the real client id and never trust a self-declared source.
2. Look up the function grant and resolve the published version: a pinned grant may use only that version; an unpinned grant may name a published version, defaulting to active_version.
3. Read the immutable config snapshot, check the function's enabled flag, and fix the config checksum for the whole call.
4. Validate request size and input_schema; build state; create run metadata containing no bodies.
5. After queueing and rate limiting, call Jev with model, state, and questions.
6. Validate the upstream answer: every question present, types matching, options belonging to criteria, numbers finite and in range, probabilities consistent with the question, model information recordable. Probability sums allow a reasonable floating-point tolerance and are never renormalised on our own.
7. If a pinned version was explicitly requested and upstream returned a different pinned version, return MODEL_VERSION_MISMATCH rather than passing the result off as the original version.
8. Evaluate review rules, apply output mapping, validate output_schema.
9. Write completion metadata and return data/status/meta.

A database transaction must never wrap a network wait. The publish transaction is short; during inference only an in-memory config snapshot is held.

Illustrative success (not a real model result):

```json
{
  "status": "ok",
  "data": {"department": "billing"},
  "review_reasons": [],
  "meta": {
    "request_id": "req_example",
    "function_key": "ticket_route",
    "version": 1,
    "model": "jev-1.13.0",
    "config_checksum": "sha256:..."
  }
}
```

Illustrative review:

```json
{
  "status": "needs_review",
  "data": {"department": null},
  "review_reasons": ["low_confidence"],
  "meta": {"request_id":"req_example","function_key":"ticket_route","version":1,"model":"jev-1.13.0","config_checksum":"sha256:..."}
}
```

External responses do not expose state, questions, raw answers, or the full vendor error by default. The admin preview can see the input, the generated request, the raw answers, rule matches, and the final return; those debug bodies live only in the current browser's memory by default.

### 7.1 Reliability defaults

Initial values: 256 KiB HTTP body, a 12000-character default content limit, global upstream concurrency of 4, a wait queue of 16, a 30-second total call budget including queueing and retries, and a suggested client timeout of 35 seconds. These are starting configuration, not a performance promise or an official quota. A character count is not a token count; upstream input limits still have to be handled correctly.

Retry at most once, and only on an explicit 429 or 529, honouring a valid Retry-After, adding jitter, and staying inside the total deadline. A network timeout or a connection dropped before the response may already have consumed inference, so v1 never automatically retries a request whose outcome is unknown. With fetch, retry lives only in the adapter layer; switching to an SDK later means turning off one of the two layers. [S1]

Cancellation travels through AbortSignal. Once a request has reached the vendor, cancelling is not promised to stop upstream inference or billing. On startup, leftover running records are marked interrupted and never replayed.

**v1 implements no persistent idempotency and no result cache.** A repeated call may be billed again and may return a different result; exactly-once is never claimed. If duplicate traffic turns out to be real, implement Idempotency-Key later and design version resolution, output retention, privacy, and the "response lost but inference happened" state separately. Do not pass a simple input hash off as an idempotency guarantee in the first version.

### 7.2 Error contract

Errors are uniformly `{error:{code,message,fields?}, meta:{request_id}}`, never carrying fabricated judgment data.

| HTTP | Example code | Behaviour |
|---|---|---|
| 400 | BAD_REQUEST | Invalid JSON or a bad fixed parameter |
| 401 | INVALID_CLIENT_TOKEN | The caller's credential is missing, invalid, or revoked |
| 403 | FUNCTION_FORBIDDEN / VERSION_FORBIDDEN | The function or version is not granted |
| 404 | FUNCTION_NOT_FOUND / VERSION_NOT_FOUND | No usable resource found; control enumeration after auth |
| 409 | DRAFT_REVISION_CONFLICT / CONFIG_CHANGED | Concurrent change to the draft or to external config |
| 413 | INPUT_TOO_LARGE | Input beyond this product's limit |
| 422 | INPUT_SCHEMA_INVALID / CONFIG_INVALID | Field-level validation error |
| 502 | UPSTREAM_AUTH_FAILED / UPSTREAM_INVALID_RESPONSE / MODEL_VERSION_MISMATCH | Upstream or vendor config error; never misreported as a bad client token |
| 503 | PROVIDER_NOT_CONFIGURED / FUNCTION_DISABLED / LOCAL_BUSY / UPSTREAM_BUSY | Cannot serve right now |
| 504 | UPSTREAM_TIMEOUT | The call exceeded its budget |

An upstream 422 is returned explicitly as UPSTREAM_INPUT_REJECTED with a redacted, actionable explanation. A vendor 401 is never translated into "your business token is wrong". needs_review returns 200, because the call and the judgment did complete.

## 8. API routes

### 8.1 Business API (bearer, scoped credential)

| Method and path | Content |
|---|---|
| GET /v1/functions | Functions visible to this client and the versions it may call; used by MCP list |
| GET /v1/functions/:key?version=N | The granted version's description, input_schema, and output_schema; internal questions and rules stay hidden |
| POST /v1/functions/:key/invoke | `{version?:number, input:object}`; omitting the version resolves by grant rules |
| POST /v1/systemone | Official `{model,state,questions}` pass-through; requires the client's `official_invoke`. Contract in specs/official-proxy/spec.md |
| GET /v1/models | Official model list pass-through; same grant |
| GET /health/live | Whether the process exists; public, and returns no local path, credential, or config |

```bash
curl http://127.0.0.1:17420/v1/functions/ticket_route/invoke \
  -H "Authorization: Bearer $JEV_CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version":1,"input":{"content":"Please refund the duplicate charge."}}'
```

Production call documentation copies an explicit version by default. When a token's pinned_version is 1, omitting the version still resolves to 1 and asking for 2 must fail. Ticking a function in the UI creates a pinned grant by default.

### 8.2 Admin API (local admin session + CSRF)

| Method and path | Content |
|---|---|
| POST /api/admin/bootstrap | Consume the one-time local bootstrap token and establish a browser session |
| GET /api/admin/status | DB, vendor key, last model test, and local port status |
| GET/POST /api/admin/functions | List / create a draft |
| GET /api/admin/functions/:id | Draft, revision, published versions, and a binding summary |
| PUT /api/admin/functions/:id/draft | Full draft save with If-Match; success increments revision |
| POST /api/admin/functions/:id/preview | Submit the current editing snapshot and a sample without implicitly saving the draft |
| POST /api/admin/functions/:id/publish | Save a version and optionally make it default; must check draft_revision and the config checksum |
| POST /api/admin/functions/:id/activate | Switch the default published version without touching historical snapshots |
| PATCH /api/admin/functions/:id | Update management fields only: display name, enabled, archived |
| GET/POST/DELETE /api/admin/functions/:id/test-cases[/caseId] | Save and delete the user's cases |
| POST /api/admin/functions/:id/test | Run saved cases against a chosen draft or version and return field assertion results |
| GET /api/admin/runs | Paged metadata, filterable by function, source, or status |
| GET/POST/PATCH /api/admin/clients | Query, create, or update grants; the credential is shown only at creation |
| POST /api/admin/clients/:id/revoke | Revoke immediately; an in-flight call is not promised to be cancelled retroactively |
| PUT /api/admin/provider | Save or replace the TypeSafe key; GET returns only configured/masked status |
| POST /api/admin/provider/test | Query the model list; only an explicit preview button sends a small billable judgment |
| POST /api/admin/integrations/detect | Check the CLI and config in fixed supported locations; a user-supplied path is only verified explicitly |
| POST /api/admin/integrations/plan | Generate the install actions and a redacted diff without writing to disk |
| POST /api/admin/integrations/apply | Verify the original file hash, then apply the fixed actions |
| POST /api/admin/integrations/:id/test | MCP initialise, list tools, and a local HTTP check; never passed off as a real model call |
| POST /api/admin/integrations/:id/remove | Remove only this product's entry, after checking for conflicts |

Endpoints may be refined into a more RESTful shape during implementation, but admin and call permissions must never be conflated. A token held by a runtime can never call anything under `/api/admin/*`.

## 9. Persistence, versions, and recovery

The full initialisation SQL is in schema.sql. Core tables: functions, releases, test_cases, clients, client_grants, runs, installations, app_settings, audit_events, plus a migration version table.

Draft saves use optimistic locking with `If-Match: "draft-7"`. A conflict between tabs returns 409 and the interface offers reload or copy-local-draft; it never overwrites directly.

Publishing: normalise and compute the config checksum → check mappings and schema → check that the current snapshot has at least one real completed preview → BEGIN IMMEDIATE → re-check draft_revision → allocate max(version)+1 → insert the release → optionally update active_version → write an audit event → COMMIT. A preview only proves the pipeline and the contract; it never means task accuracy has been calibrated. Offline CI uses an explicit test mode that allows publishing from a fixture; production mode never accepts a fixture as evidence of a real run.

When the page has unsaved changes, Publish saves first and re-checks validity. It never publishes the old draft and then claims the new edits are live.

Rolling back the default only changes active_version. Pinned calls are unaffected, and the interface shows "default v2, 3 clients still pinned to v1". Old versions cannot be edited in place and version numbers are never reused. The original spec made delete an archive; the user's later requirement, recorded in specs/single-page/spec.md, revised it to a restorable trash plus a confirmed permanent delete. Historical versions never disappear because the default was rolled back.

SQLite lives on the local disk with WAL, FULL sync, and busy_timeout. One service process is the primary reader and writer; MCP bridges must never open the database directly. WAL allows concurrent readers with one writer and is not suitable for a shared network drive. [S12]

Backups use SQLite's online backup API rather than copying a live `.db` file. A function export contains no secret, no client token, no other runtime config, and no raw call content. Publish and integration changes write a small audit record.

## 10. Security and privacy boundary

### 10.1 A local browser still needs a permission boundary

Bind 127.0.0.1, validate the full Host and Origin, and reject unknown origins. A CORS wildcard is never a substitute for authentication. Origin-less requests from business services and MCP need a valid bearer. `/health/live` exposes the minimum. The official MCP transport guidance also stresses localhost binding, Origin checking, and authentication. [S13]

The startup CLI generates a 256-bit, one-time, 60-second bootstrap token and opens the browser with it in the URL fragment. The browser removes the fragment from the address bar immediately and POSTs the token in exchange for an HttpOnly, SameSite=Strict session cookie; state changes additionally need a CSRF token. Over HTTP loopback we do not rely on the Secure cookie flag for HTTPS safety, and the service is never exposed externally. Temporary credentials are never written to localStorage, ordinary logs, or a URL query.

Admin sessions are held in memory; after a restart, use `service open` to bootstrap again. There is no registration, no login, and no third-party account — a single-machine first version does not invent a user system.

### 10.2 Three kinds of secret

- **TypeSafe key:** read from the launch environment first; when set from the page it is encrypted into secrets.json using Node crypto AES-GCM with a random nonce, and the master key lives in master.key protected by local file permissions. When the environment variable is in effect the page states the source, so nothing looks "saved but not applied".
- **Client token:** 256 random bits; the database stores only a SHA-256 hash and a display prefix, and the plaintext is shown once at creation. The raw token for MCP and Pi lives in an owner-only credential file, and the runtime config references only that path.
- **Admin bootstrap and session tokens:** short-lived, local, and never reused as a business token.

Directories are 0700, credentials and backups 0600. Windows ACL support comes later; this version's acceptance is macOS-first. The master key and the ciphertext still sit on the same user's machine, so no claim is made against a process that already has that user's file access. A client grant is application-level isolation, not an OS sandbox.

### 10.3 Content handling

Call bodies, state, question snapshots, and full answers are not written to run logs by default. Only the function and version, client, status, duration, actual model, token usage, rule ids, and redacted errors are recorded. Debug bodies are lost on page refresh; "save as a case" is a separate, explicit action that states what business content it contains.

Arbitrary URL fetching, file path reads, shell templates, expression eval, and a custom upstream base URL are all forbidden. The provider address is fixed to the official domain, so a configuration tool never becomes an SSRF or arbitrary-code service. A model is not a security sandbox, and confidence is never a permission to act.

## 11. Agent integration

### 11.1 The three tools exposed everywhere

v1 keeps a fixed tool table, which reduces differences in dynamic schema hot-reload:

| Tool | Input | Returns |
|---|---|---|
| jev_list_functions | none / paging | The keys, descriptions, when_to_use, and versions available to this credential |
| jev_describe_function | key, optional version | input_schema, output_schema, and a brief usage note |
| jev_invoke | key, optional version, input | The same status/data/meta as HTTP |

Discovery uses list and describe; after that, invoke directly. A short skill explaining when to call may ship alongside the install, but installing it never claims the agent will definitely call. Per-function named tools can come later if the experience needs them; the first version does not maintain two tool modes at once.

### 11.2 The MCP bridge

On stdio, stdout carries protocol messages only and logs go to stderr. Use the SDK for initialisation and tool responses; return structuredContent while also providing text JSON. Failures use isError, and needs_review is never marked a tool error. The bridge reads only its own credential file and endpoint — never the vendor key or the database.

When the backend is not running, the bridge still registers its tools as fast as possible; an actual call returns BACKEND_UNAVAILABLE plus startup instructions, and no backend is auto-started per client. Cancellation and deadlines pass from the bridge through to the backend.

Claude Code and Codex both provide an MCP add command; OpenCode's local config uses `type=local` with a command array. [S14][S15][S16]

The following are examples generated after implementation, not ready-made published commands:

```bash
claude mcp add --transport stdio --scope user jev-workbench \
  -- /absolute/node /absolute/project/dist/mcp/index.js \
  --credentials-file /absolute/home/.jev-workbench/clients/claude.json

codex mcp add jev-workbench \
  -- /absolute/node /absolute/project/dist/mcp/index.js \
  --credentials-file /absolute/home/.jev-workbench/clients/codex.json
```

```json
{
  "mcp": {
    "jev-workbench": {
      "type": "local",
      "command": ["/absolute/node", "/absolute/project/dist/mcp/index.js", "--credentials-file", "/absolute/home/.jev-workbench/clients/opencode.json"],
      "enabled": true
    }
  }
}
```

### 11.3 Pi

The Pi extension registers the same three tools with `pi.registerTool()`, forwards to the local API, and passes execute's cancellation signal through. A global extension can live in `~/.pi/agent/extensions/` and a project one in `.pi/extensions/`, following the project trust and `/reload` mechanisms; no tool-interception hook is injected. [S17]

Ship a complete, version-controlled extension package with its package.json and dependencies — never a single TS file with missing dependencies. The credential path is independent of the project repository. The first-version Pi smoke test uses `pi -e /absolute/path/to/extension`; auto-loading is tested after a real install.

### 11.4 The correct install flow

The browser never reads or writes the user's config files. The already-running, authenticated local backend does the work, and it implements four fixed adapters only — there is no general "pass in any shell command" interface.

Detect version and path → generate fixed actions and a diff → user confirms → back up the current file → re-check the file hash → modify this product's entry through the CLI or a structured AST → atomic write and verify → connectivity test. JSONC must keep its comments; TOML and JSON must not be crudely rewritten wholesale. CLIs are spawned with an argument array and shell=false.

Claude and Codex prefer the official CLI; for an unknown version, stop at the generated-command page rather than guessing a config path. OpenCode uses a JSONC-aware editor. The target is chosen precisely by user or project scope, never by scanning the whole home directory. Uninstall reverses only this product's entry; if existing config has been modified by the user, report the conflict rather than overwriting their later work with a whole-file backup.

Status distinguishes: not detected, configurable, written, initialisation verified, recently called successfully, and conflict or error. Writing a config is not the agent having loaded it, and neither is proof that a real model call succeeded. Multiple runtimes under one UID cannot provide strong security identity; different tokens serve least privilege and audit attribution.

## 12. Front-end information architecture

Two primary destinations only, with settings and history as secondary entries:

```text
Functions /functions
  └─ /functions/:id
       basic info, input, questions, output/rules
       preview panel on the right
       versions drawer / call drawer / history drawer
Connections /connections
  ├─ API calls
  └─ Agents
Settings: a global drawer from the top right
```

The default home is the function list, not a KPI dashboard. An empty list invites "create a judgment function" and offers three editable examples — ticket routing, evidence check, content relevance — with no invented usage figures.

### 12.1 Visual specification

> Superseded on 2026-09-18 by `specs/dropagent-visual/spec.md`, which replaces
> the palette, typography, spacing, and component rules below. The behavioural
> requirements in this section — state always stated in words, no fabricated
> metrics — still stand.

- Desktop first, against 1440×960. Global sidebar 200–208px; content padding 28–32px; the main editing column `flex:1, min-width:480px`; the preview column 380–420px; gap 24px.
- Below 1280px the preview panel moves under the editor as two horizontal columns; below 900px the sidebar collapses to icons and editing stays one column; narrower still, preview content keeps stacking, down to a minimum of 768px. Phones only guarantee readability; phone editing is not a first-version acceptance target.
- Page background #F7F8FA, panels #FFFFFF, sidebar #F3F5F8; primary text #20252D, secondary #596473, borders #E2E6EC; primary action #405BCF.
- A system sans stack including a Chinese fallback; headings 24/20px, body 14px, labels 12px, code 13px; nothing important below 12px.
- An 8px spacing system, inputs 36–40px tall, primary buttons 40px, 8px radius, 1px borders. Lists over stacked cards; no large gradients, glass effects, marketing illustration, or animated metrics.
- Status always carries words and never depends on colour alone. error = red, review = amber, published = green; draft is a neutral tag.
- Charts show only the probability distribution the model returned, labelled "model probability, not accuracy". No fabricated precise durations, success rates, or trust scores.

### 12.2 Function list

Columns: name and purpose, key, current default version, draft status, enabled status, last call status, actions. Above it, only search, an enabled filter, and create. Clicking a row opens the detail — no second wall of cards.

Empty states distinguish "no functions yet", "no search results", and "failed to load"; a failure keeps the previous data and offers retry rather than drawing an empty list.

### 12.3 Function editor

Top: breadcrumb, name, read-only key, current published vN, and a draft-modified marker; on the right, "save draft" and "publish new version", plus secondary "versions" and "call".

Four tabs in the middle:

1. **Basic info:** name, key, purpose, when_to_use, pinned model version. when_to_use is described as tool documentation, not a trigger.
2. **Input:** field name/type/required/description/bounds; add and remove fields; derive initial fields from a sample JSON; input schema preview.
3. **Questions:** the question list; add Noul/Choice/Score; id, instructions, criteria; Choice keeps stable option keys separate from display names; Score levels can be dragged with a warning that level indices shift; saving still leaves a draft.
4. **Output and rules:** the field mapping table, a source dropdown, the returned name, and blank-on-review; any/all review conditions; a sample output and output_schema. Advanced JSON and the form stay in sync both ways.

The preview panel on the right: form/JSON switch → pick a saved case → "test the current edit" → result. A note beside the button says "sent to TypeSafe, may incur charges". The request can be cancelled. While a request is outstanding, only the real in-progress state is shown; no fake stage progress.

Results split into four views: final return, raw answers, actual request, and rule matches. After a real completion it shows the version or draft checksum, provider and model, and duration. A draft preview shows "unpublished" and never disguises itself as v1.

After the user changes anything that affects execution, the previous result is immediately marked "from an older config" and the current snapshot must be re-run before publishing. A single preview never marks anything "calibrated".

### 12.4 Publish and version drawers

Shows the current draft's diff against the previous version, breaking input/output changes, saved case results, the pinned model, and the release note. The publish button reads "publish v2 and make it default", and "make default" can be unticked. It shows which pinned clients are still on v1 and never upgrades them by default.

Rolling back only picks a published version and moves the default pointer, stating clearly that pinned clients are unaffected. Leaving with unsaved work offers save/discard/cancel; auto-publishing never decides for the user.

### 12.5 Connections — API

Pick a function and version on the left; the right shows the endpoint, the required input fields, a response example, and curl/Python/TypeScript tabs. Examples are generated from the published schema rather than hardcoded separately.

The client list shows name, granted functions and versions, token prefix, last request, and revoke. Creating a credential grants no function by default; after the user ticks some, the plaintext is shown once. Copyable code uses a `$JEV_CLIENT_TOKEN` placeholder and never stores a plaintext credential in browser localStorage.

"Test call" must not quietly use admin identity: the user can test in memory right after creating a credential, or paste an existing client token. The backend validates as the real business principal. The page's credential variable is cleared after the test and never persisted.

### 12.6 Connections — Agents

Four cards: Claude Code, Codex, OpenCode, Pi. Each shows detection info, granted functions and pinned versions, config scope, and status. The button moves through the stages: generate config → review changes → apply → test → revoke.

The credential file path is part of the generated config, but the actual token never appears in the diff. A connectivity test states clearly whether it only tested the connection; a real billable judgment requires an explicit click. Whether a real agent loaded the tools needs bridge initialisation telemetry or evidence of an actual call — the existence of an installation row in the database never displays as "connected".

### 12.7 Settings and history

Settings: vendor key (masked, replaceable), model list and test, read-only port and local paths, the content-leaves-the-machine notice, advanced concurrency and timeout, export without secrets, and backend status. Changing the port requires a restart and a reminder to update client configuration.

Call history does not take a primary navigation slot; it opens as a drawer from the function detail or the connections page. Rows show time, function version, source, status, real duration, model, and usage, with error and needs_review kept apart. There is no raw content by default, and a detail view can never "replay" an unsaved request out of thin air. Only a saved case can be re-run explicitly.

### 12.8 Interaction and accessibility

Every control is reachable by Tab; labels are bound to error text; focus is visible; Escape closes a drawer and returns to its trigger; dialogs trap focus; Cmd/Ctrl+S saves the draft and Cmd/Ctrl+Enter runs a preview. Shortcuts behave sensibly inside ordinary text areas and never swallow necessary editing input.

Every async operation has idle/pending/success/error and guards against double submission. Form validation shows the field path — `questions.department.criteria`, not just "invalid parameter". A network error never clears unsaved input.

## 13. Project layout and module boundaries

```text
jev-workbench/
  apps/
    web/src/
      pages/FunctionList.tsx
      pages/FunctionEditor.tsx
      pages/Connections.tsx
      features/functions/{InputEditor,QuestionEditor,OutputEditor,Playground}.tsx
      features/releases/ReleaseDrawer.tsx
      features/connections/{ApiPanel,AgentPanel,ConfigDiffDialog}.tsx
      features/settings/SettingsDrawer.tsx
      lib/api.ts
    server/src/
      app.ts
      routes/{admin,invoke,health}.ts
      services/{functions,invoke,clients,integrations}.ts
      engine/{validate-input,map-state,validate-answer,review,map-output}.ts
      providers/typesafe.ts
      storage/{db,repositories,migrate}.ts
      security/{session,client-token,secret-store,origin}.ts
      integrations/{claude,codex,opencode,pi}.ts
      lifecycle/{start,stop,open}.ts
    mcp/src/index.ts
    pi-extension/{index.ts,package.json}
  packages/contracts/src/{config,http,provider}.ts
  migrations/001_initial.sql
  examples/ticket_route.v1.json
  tests/{unit,integration,mcp,e2e,fixtures}/
  scripts/{build,start,service}.mjs
  package.json
  pnpm-workspace.yaml
  pnpm-lock.yaml
  .nvmrc
```

Do not generate a separate Node service per function, and do not let the UI, MCP, and Pi each implement judgment rules. Contracts can be shared; storage and execution logic live only in the backend. The provider is a small interface wrapper, not a general plugin marketplace in the first version.

## 14. Startup, data directory, and background lifecycle

Once a developer has the final implementation repository, the target commands are:

```bash
pnpm install --frozen-lockfile
pnpm build
pnpm start
```

Those are scripts the project is required to implement; the design package itself is not that executable repository. The first start migrates SQLite automatically, creates permission-restricted directories, checks the port, prints the local address, and opens a one-time session bootstrap page. Without a TypeSafe key the interface is still editable, but preview and calls show "provider not configured" and never return a mock passed off as a real result.

Background mode targets:

```bash
pnpm jev service start
pnpm jev service status
pnpm jev service open
pnpm jev service stop
```

A background start records an instance id, PID, and port, and the health probe verifies the same instance so a reused PID is never killed by mistake. A port conflict fails with a change-the-port suggestion rather than silently moving and disconnecting agents. Stop first refuses new calls, waits a bounded time, cancels the rest, and then closes the database — it never sends a kill to an arbitrary PID.

```text
~/.jev-workbench/                 # 0700
  data/workbench.db
  secrets.json                   # AES-GCM ciphertext, 0600
  master.key                     # 0600, never exported
  clients/claude.json            # local call token, 0600
  clients/codex.json
  clients/opencode.json
  clients/pi.json
  backups/                       # may contain the user's original config, files 0600
  logs/server.log                # redacted, rotated
  runtime/instance.json
```

Two backends must never run against the same directory. Backup, restart, and upgrade all have to be reproducible; upgrades follow the lockfile, and the SQLite driver's native binary must be accepted on the target macOS ARM64/x64 — no claim of zero-compile installation on every platform. Where a platform has no prebuilt binary, state the prerequisites or provide a verified distribution instead of blindly installing a compiler at startup.

## 15. Testing and acceptance

| Scope | Must be tested |
|---|---|
| Pure execution engine | All three question types, any/all rules, threshold edges, on_review=null, missing paths, enum map completeness, output schema |
| Provider contract | Missing answer, wrong question type, unknown option, out-of-range or non-finite numbers, corrupt JSON, model version mismatch, 429/529, vendor 401 |
| Publishing | A draft does not affect v1, revision conflict 409, version allocation in one transaction, old versions immutable, rolling back the default does not affect pinned versions |
| Authentication | Missing token 401, over-scope 403, revoked token fails, an API client cannot reach admin, list never leaks an ungranted function |
| Front end | Empty/error/loading states, keyboard operation, edit retention, stale-result marking, saved cases, publish diff, token shown once |
| Config install | Existing MCP entries preserved, JSONC comments preserved, paths with spaces, file hash conflict, repeated install idempotent, only our own entry revoked |
| Process | Port conflict, second start, background detach, closing the browser keeps it running, restart recovery, missing key |
| Privacy | No secret in a URL or log, no bodies in runs, no key in an export, external Origin rejected, no LAN listening by default |
| Across entry points | The same fixture, version, and input give the same result contract over HTTP, MCP, and Pi |
| Real integration | Call the official API and each of the four real runtimes once, recording the actual version, platform, and result; mark unrun platforms unverified |

A mock provider may be enabled only by an explicit test or demo mode and always shows a permanent banner. It must never be an automatic fallback when the real service errors.

Real models can differ between runs. Cross-entry real verification checks the same config, the same grant, and a correct contract; it does not require floating-point values to match exactly. A probability, or a single example, never proves the model is accurate for the business — accuracy needs an independent labelled set.

Minimum end-to-end acceptance story:

1. Start against an empty data directory, open the browser, set the key, and confirm the data-leaves-the-machine notice.
2. Create ticket_route with a content field, a four-way classification question, a review rule, and an output mapping.
3. Test an unambiguous and an ambiguous ticket, inspect the actual request, answers, and output, and save a case.
4. Publish v1, create a business token allowed only `ticket_route@1`, and get a contract-conforming result from curl.
5. Edit the draft without affecting v1; after publishing v2, a client pinned to v1 still gets v1 metadata.
6. Create four agent credentials and connect them; find and call the function through the three tools.
7. An upstream timeout surfaces as an error with no default classification; revoking one credential affects only that credential's later requests.
8. Close and reopen the browser: the backend and published versions are still there. After stopping the service, every call returns a clear unavailable.

## 16. Implementation order

**Phase A — the minimal vertical slice.** Initialise the project, fix the contracts, SQLite migrations, session auth, import a single function config, the provider, invoke, curl. Do not draw every page first, and do not connect four runtimes yet.

**Phase B — the function workbench.** List and editor, preview, cases, draft optimistic locking, immutable publishing, real API responses. Finish "configure → test → publish → curl" first.

**Phase C — call management.** Client credentials, pinned-version grants, generated API examples, log metadata, error and retry policy.

**Phase D — agent integration.** The MCP bridge and SDK client tests first, then the Claude/Codex/OpenCode config adapters, then the Pi extension. Every adapter needs a config fixture and a record of testing against the real target version.

**Phase E — delivery.** Same-origin production build, background lifecycle, config diff and safe revoke, backup and migration, a full-chain Playwright run, the README, and the platform compatibility matrix.

Every phase must have a runnable entry point. Simulating all buttons with timers and fake data and wiring the backend last is forbidden. Done means the real business API and all four integration paths work, not that the HTML pages exist.

## 17. Constraints for the coding agent

Treat this spec as the only first-version scope and deliver a real, runnable local browser application. Build the HTTP vertical slice first, then the UI and the agents. Do not add chat, model download, multi-tenancy, cloud accounts, a workflow canvas, or a main-model proxy. Do not change the user's main model configuration.

Do not treat prototype.html as production code or claim the product is done because of it; it exists only to align information architecture and visuals. Every mock stays isolated in test or demo mode, and the production provider must call the official API. The config layer forbids arbitrary JS, SQL, and shell execution; config changes go only through the fixed adapters.

The delivery must include the lockfile, migrations, examples, unit tests, integration tests, MCP tests, end-to-end tests, start/stop scripts, a platform compatibility record, and the list of unverified items. Never let "configured" stand in for "verified by a real call", and never let one preview stand in for a business accuracy evaluation.

## 18. Index of official sources

Check these links during implementation; runtimes and model capabilities may change, and this document makes no promise that later versions keep the same commands or interfaces.

- [S1] TypeSafe HTTP API: `https://docs.typesafe.ai/api`
- [S2] Quickstart: `https://docs.typesafe.ai/introduction/quickstart`
- [S3] Models: `https://docs.typesafe.ai/models`
- [S4] Confidence: `https://docs.typesafe.ai/confidence`
- [S5] Primitives: `https://docs.typesafe.ai/primitives`
- [S6] Fan-out: `https://docs.typesafe.ai/patterns/fan-out`
- [S7] State: `https://docs.typesafe.ai/concepts/state`
- [S8] Node releases: `https://nodejs.org/en/about/previous-releases`
- [S9] Vite: `https://vite.dev/guide/`
- [S10] shadcn/ui + Vite: `https://ui.shadcn.com/docs/installation/vite`
- [S11] MCP TypeScript SDK: `https://ts.sdk.modelcontextprotocol.io/`
- [S12] SQLite WAL: `https://www.sqlite.org/wal.html`
- [S13] MCP transports: `https://modelcontextprotocol.io/specification/2025-06-18/basic/transports`
- [S14] Claude Code MCP: `https://code.claude.com/docs/en/mcp`
- [S15] Codex MCP: `https://developers.openai.com/codex/mcp/` (redirected to the official ChatGPT Learn page when checked)
- [S16] OpenCode MCP: `https://opencode.ai/docs/mcp-servers/`
- [S17] Pi extensions: `https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md`
- [S18] better-sqlite3: `https://github.com/WiseLibs/better-sqlite3`
- [S19] Fastify: `https://fastify.dev/docs/latest/Reference/Server/`

## Implementation addendum (2026-09-18, confirmed by the user this round)

The user had no TypeSafe key and explicitly asked to "simulate the data first and finish the rest". This round therefore adds a separate offline demo: `pnpm demo` on port 17430 against `~/.jev-workbench-demo`, with a permanent simulation banner and built-in normal, review, error, and timeout scenarios. Production on 17420 still calls only the fixed official endpoint, returns a clear error without a key, and never degrades automatically. Demo publish records carry a fixture marker, and a production publish never accepts one as evidence of a real preview. Real cloud and billable calls from the four real agents are recorded as not run, which does not affect this round's simulated acceptance.

Integration implementation: OpenCode JSONC and the Pi extension support structured writes; Claude Code 2.1.206 and Codex 0.154.0, whose command arguments were verified locally, use their CLIs. An unknown CLI version gets only the credential and command prepared. The Codex CLI has no project-scope add argument, so project scope keeps a manual configuration path and never pretends user scope is project scope. An external config change still has to be reviewed inside the product before Apply is clicked.

### Bilingual and code delivery addendum (explicitly authorised by the user)

Keep the Chinese interface and add an English toggle with a persisted language preference (only the language may go in localStorage — never a token or key). Both languages cover navigation, editing forms, preview, versions, connections, settings, empty states, and error messages; switching language never modifies the user's configuration content or loses unsaved edits. Add English examples and an English README. After bilingual end-to-end acceptance, commit to Git and push to the molis-ai organisation, creating a private molis-ai/jev-workbench if no repository of that name exists, without overwriting any other repository.

### Latest single-page design correction

The user asked for a Coss-UI single-page design draft first, exposing the three primitives directly and reducing navigation. The draft's contract is `specs/single-page/spec.md`. After it, the user said explicitly "change it, then build", which authorised and completed the production left/right workbench; a later directory screenshot added compact groups, type tags, and trash. The implementation reuses the existing engine, and acceptance rests on the production UI and API tests.
