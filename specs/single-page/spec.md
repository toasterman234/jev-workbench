# Single-page left/right workbench · development contract

## Background and goal

The user found the original pages complicated and the three primitives hard to discover. They asked for, and authorised: a Coss-UI-style neutral look, a function list on the left, the current item on the right, status tags in the list, and add / archive / delete — design first, then build. An earlier standalone design draft lives in `design/single-page`; this contract makes a production React implementation the deliverable.

## Completion level and boundary

Functional, offline-simulated. Configuration, persistence, versioning, permissions, and the HTTP/MCP/Pi contracts are real implementations; real TypeSafe inference was not exercised here because the user had no key at the time. The existing DSL and advanced configuration are preserved while the default view gets simpler. Built on the existing Fastify/SQLite/React stack, with no new runtime dependency.

## Modules and verification

`main.tsx` carries the list, filters, status actions, and the selected item. `FunctionEditor` and `SimpleDefinition` carry the draft cache, the default form, and the primitive result views. `Connections` keeps using the existing real APIs. `Functions.delete` cleans up related data transactionally. Server-side localisation keeps stable error codes.

Verify with `pnpm typecheck`, `pnpm build`, `pnpm test`, `pnpm test:e2e`. The standalone design draft's `node scripts/check-design.mjs` only proves the prototype and does not replace these.

## Development scope confirmed by the user (2026-09-18)

The user asked for a function list on the left and the selected item on the right, with status tags, add, archive, and delete, and said explicitly: "change it, then build". This section replaces the earlier boundary that was waiting on design feedback, and authorises production development.

- The left column is about 280px with search and status filters. Each entry shows the name, its primitive set, and draft / published / disabled / archived. A row menu disables, archives, restores, or deletes. Creation offers Noul, Choice, and Score.
- The right column shows the selected function and edits the name, question instructions, and primitive-specific criteria directly. Input schema, output mapping, and similar move into a collapsed advanced area; preview and its real result share the same screen. Connections and settings are separate entries in the left rail that open a full page on the right, and settings splits again internally (categories / config rows). Versions and history stay in local drawers.
- Switching functions preserves unsaved config, raw JSON edits, and preview input for the session. Refresh or close warns. Business text is never written to localStorage automatically.
- Archiving keeps every version, case, and grant but blocks business calls; restoring returns the previous enabled state.
- Delete is a new real API. The UI states clearly that it cannot be undone and that it removes the function's versions, cases, grants, and run records. It is refused while a call is executing, cleans foreign-key relations transactionally, and leaves other functions, clients, and installations untouched. An audit event without bodies is kept. This requirement explicitly replaces the v1 "delete only archives" agreement.
- The real provider, immutable publishing, CSRF, and the pinned-grant contract all stand; the user's agent config is never changed automatically. The English UI, English README, and English examples continue.
- Acceptance: real HTTP archive blocking and restore; delete persistence, permissions, and refusal while running; a bilingual browser story creating all three primitives → configure → preview → save and publish → granted call; draft retention on switch, list filters, add, archive, restore, delete; layout at 1440 / 1024 / 390; build plus the existing regression suite. Commit to Git afterwards and create/push the private molis-ai/jev-workbench.

## Acceptance result

- Pass: typecheck and a same-origin production build.
- Pass: 23 Vitest tests, including archive blocking and restore, delete persistence, CSRF rejection, refusing delete while a real execution is interleaved, and other functions and clients staying intact.
- Pass: one complete bilingual browser story — Choice → save case → publish → Noul/Score preview → draft preserved across switching → create in English → pinned-grant HTTP call → archive/restore/delete → search → language persists across reload.
- Pass: no horizontal document overflow at 1440 / 1024 / 390, with screenshots covering all three primitives, English, connections, narrow, and phone.
- Not run: real TypeSafe inference and model calls from the four actual agents (the user had no key; explicitly deferred).

## User screenshot addendum (directory style and trash)

The directory screenshot supplied by the user is the current visual reference: new and filter at the top, compact row-based directory, and current / archive / trash groups with counts. Selection fills the whole row in light grey, and each of the three primitives has a clear tag — no more multi-line cards. Functions have no parent-child relationship, so no tree structure and no non-functional view switcher may be invented.

This section replaces the previous "delete permanently straight from the list": an ordinary delete moves the function to Trash, keeping every related record and blocking business calls, and can restore the previous archived and enabled state. Permanent delete exists only inside Trash and keeps the confirmation and the refusal while running, with the same transactional cleanup. A migratable `deleted_at` column is added without resetting existing databases. Trash content is read-only; it becomes editable after restore. Unsaved drafts survive within the session.

Added acceptance: old data survives migration; trash blocks calls, hides from lists, and restores; permanent delete is refused outside Trash; group counts and type tags are correct; the browser story covers move to trash, restore, and permanent delete.

## Config surface and connection entry (2026-09-18)

Function configuration follows the Molis Work project settings pattern: a page header (title, one-line description, top-right actions) plus grouped rows (title, description, control on the right), with hairlines between rows inside a rounded container. Connections moved out of the bottom of the editor and became a separate left-rail entry that opens a full page on the right. The default editing state still fits one screen with no page scrolling.

## One screen on the right (2026-09-18)

The user asked that the right-hand content area not scroll, and that the default content be compressed to one screen.

- On desktop and at 1024 wide, the default state — advanced config, response diagnostics, and connections all collapsed — produces no vertical scrolling of the window or the right-hand content area, and definition and preview stay side by side.
- Expanding advanced config, diagnostic JSON, or connections scrolls only within that panel or content area, never stretching the page.
- Phones (≤700) may still scroll the whole page.

Acceptance: `documentElement.scrollHeight <= innerHeight` at 1440 and 1024; screenshots of Choice with a result after publishing and of the default Noul/Score editors show no page scrollbar.
