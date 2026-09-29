# Work Judgment Phase 1

This directory contains the first six Work Judgment functions expressed entirely
through Jev Workbench's existing v1 function DSL.

No engine, database, API, MCP, Pi, or UI changes are required for this proof.

Functions:

- `classify_data_type` — Choice
- `next_intent` — Choice
- `select_artifact` — Choice
- `select_playbook` — Choice
- `requires_human_gate` — Noul
- `evidence_satisfies_exit` — Noul

Design rules:

- stable machine keys are separate from human descriptions;
- low-confidence choices are reviewable rather than silently accepted;
- `other_needs_new` explicitly signals a missing vocabulary entry;
- `unclear_needs_review` explicitly signals insufficient context;
- fallback choices remain visible in the returned data even when business status is `needs_review`;
- human-gate and evidence-exit questions return Noul probabilities, with provisional ambiguity bands;
- published versions are not created by these files. Real publish still requires a successful preview using the configured TypeSafe provider.

The source planning package and 25-case projection suite are being reviewed separately
in PR #1. The next verification step after config/CI validation is to instantiate these
functions in an unmodified Workbench and run the applicable projection cases against a
fixed Jev model version.
