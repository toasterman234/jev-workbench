# Jev · single-page design preview

> Historical. This standalone draft has been superseded twice: first by the
> production React workbench (`specs/single-page/spec.md`), then by the current
> visual system (`specs/dropagent-visual/spec.md`). It is kept as a record of
> the information architecture the user approved, not as a design reference.

A bilingual, interactive design preview built after the user's feedback that the pages were too complicated. It explores a simpler single-page interface inspired by Coss UI ([styling docs](https://coss.com/ui/docs/styling)). It never replaced the production React workbench and never called a provider.

## Open

From the project root:

```sh
python3 -m http.server 17431 --bind 127.0.0.1 --directory design/single-page
```

Open http://127.0.0.1:17431. No dependencies are required. You can also open index.html directly; clipboard and browser storage availability depend on the browser.

## Interactions

- Noul / Choice / Score always visible; no page navigation.
- Primitive-specific configuration and results.
- Chinese / English toggle; edits are preserved when switching languages or primitives.
- Save draft to browser localStorage; reload to resume. No credentials are stored.
- Offline illustrative test states: normal, needs review, failure, empty input, stale result.
- Inline advanced settings, response JSON, release preview, HTTP / MCP / Pi examples.
- Responsive desktop and mobile layout; visible keyboard focus.

All results are illustrative. Changing a proposition does not run inference; publish and connect controls only preview the proposed interaction. There are no real releases, credentials, or external writes.

## Verification

With the local preview server running and project dependencies installed:

```sh
node scripts/check-design.mjs
```

Checks three primitives, language preservation, saved drafts, review/error/empty states, inline release/MCP examples, and overflow at 1440/768/390 px. Screenshots are saved to `.impeccable/review/single-page` (ignored by Git).

The production implementation is in `apps/`. The design contract and integration boundary are in `specs/single-page/spec.md`.
