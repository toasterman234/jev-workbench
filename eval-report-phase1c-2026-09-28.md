# Jev Workbench — Work Judgment Phase 1C Evaluation Report (2026-09-28)

## Headline

- **Component (gold upstream): 128/162 = 79.0%** (Phase 1B: 125/161 = 77.6%)
- **End-to-end (predicted upstream): 119/159 = 74.8%** (Phase 1B: 114/158 = 72.2%)
- **Overall: 247/321 = 76.9%** (Phase 1B: 239/319 = 74.9%)
- Model: `jev-1.13.0`, real TypeSafe provider, 30 cases, 340 invocations, 2 provider 502 errors, 3 upstream-error skips.

Per-function (component / end-to-end), with Phase 1B in parentheses:

| function | component | end-to-end |
|---|---|---|
| classify_data_type | 16/29 = 55.2% (16/29 = 55.2%) | 17/30 = 56.7% (17/29 = 58.6%) |
| next_intent | 23/30 = 76.7% (22/30 = 73.3%) | 22/29 = 75.9% (21/29 = 72.4%) |
| select_artifact | 23/28 = 82.1% (20/27 = 74.1%) | 19/27 = 70.4% (15/27 = 55.6%) |
| select_playbook | 21/27 = 77.8% (21/27 = 77.8%) | 17/26 = 65.4% (17/26 = 65.4%) |
| requires_human_gate | 27/29 = 93.1% (27/29 = 93.1%) | 26/28 = 92.9% (25/28 = 89.3%) |
| evidence_satisfies_exit | 18/19 = 94.7% (19/19 = 100%) | 18/19 = 94.7% (19/19 = 100%) |

(n differences vs 1B are error placement: the 2 provider 502s hit different
judgments than 1B's 3 errors.)

## The two taxonomy decisions, tested

### 1. Merge: `work_item_change` → `result` — resolved

The four close-intent cases whose golds moved `work_item_change` → `result`
(wj-001, wj-010, wj-016, wj-030), select_artifact:

- Component: **4/4 predict `result`** (wj-010/016/030 under needs_review, still correct).
- End-to-end: **3/4** — wj-010 misses (`plan`) only because upstream
  next_intent was mispredicted (upstream_error=True); the artifact choice
  itself is no longer the failure point.

Phase 1B's systematic result→work_item_change confusion (4/4 on close intent)
does not recur: with the duplicate retired, the model selects `result`
directly. select_artifact gained +8.0pp component / +14.8pp end-to-end,
the largest move in the eval.

### 2. Split: `incident` (operational) vs `quality_failure` (deliverable) — new type works, one boundary needs a gold decision

**quality_failure: 6/6 = 100%.** All three botched-deliverable cases
(wj-002 falsely-claimed-verified app, wj-003 screenshot proof missing the
claimed nodes, wj-009 page marked successful with broken render) are
classified `quality_failure` in both modes, including under needs_review.

**incident: 4/10 = 40%** (was 8/8 with the suite-level candidate in 1B).
The three new misses are the weakest incident golds, and the model's
answers are defensible under the split:

- wj-011 (audit incorrectly reports vault folders missing, doubles down):
  model says `quality_failure`. The defective object here is the audit
  *report* — a deliverable falsely claimed correct. Under Ben's split this
  reads more like quality_failure than an operational incident.
  **Recommend re-golding wj-011 → quality_failure.**
- wj-013 / wj-015 (timeout-mechanism diagnostic cases): model says
  `evidence`. Both cases center on diagnostic evidence about a mechanism,
  not on the disruption itself. Debatable; gold could stay incident or move
  with a narrower incident criterion.
- wj-012 / wj-014 (clear operational incidents: intermittent 120s timeouts,
  recurring sorter failure): still correct, both modes.

Net: the split gives botched deliverables a home the model uses perfectly;
the cost is concentrated on incident golds that were already the softest.
No new systematic model failure — the open question is gold placement on
the incident/quality_failure/evidence boundary, which is a taxonomy-owner
call.

Also notable: wj-008 ("agent repeatedly claims completion without
verification proof", gold `result`) is now predicted `quality_failure` in
both modes. The model reads a pattern of false completion claims as a
defective deliverable. Genuine boundary case — flagging for gold review
rather than relabeling unilaterally.

## Calibration (thresholds unchanged: gate 0.50/0.70, exit 0.50/0.80)

| question | mode | Brier | acc@0.50 | acc@provisional |
|---|---|---|---|---|
| requires_human_gate | A | 0.060 (1B 0.061) | 93.1% | 100.0% @0.70 |
| requires_human_gate | B | 0.060 (1B 0.070) | 92.9% | 100.0% @0.70 |
| evidence_satisfies_exit | A | 0.036 (1B 0.037) | 94.7% | 78.9% @0.80 |
| evidence_satisfies_exit | B | 0.037 (1B 0.033) | 94.7% | 78.9% @0.80 |

No calibration performed (thresholds reported as-is, per protocol).
The evidence_satisfies_exit dip (19/19 → 18/19 both modes) is a single
boundary case, wj-028: p=0.50→0.49 (A), p=0.53→0.49 (B) — stochastic wobble
at the gate, unrelated to the taxonomy.

## Review triggers

- Component: 54 needs_review / 108 ok. Reasons: low_confidence 46,
  ambiguous_gate 3, unclear 3, ambiguous_exit 3, new_playbook_needed 1.
- End-to-end: 53 needs_review / 106 ok. Reasons: low_confidence 43,
  unclear 5, ambiguous_gate 3, ambiguous_exit 3, new_playbook_needed 1.
- Correct-under-review still counts as correct in the accuracy figures
  above (same convention as 1B).

## Errors

2 provider-side 502s (`UPSTREAM_INVALID_RESPONSE`, same class as 1B's
workbench-limitation attributions): A/wj-007/classify_data_type,
B/wj-002/next_intent (the latter caused 3 downstream skips in Mode B via
the upstream-error chain rule). No client/token failures; no fabricated
data — errored invocations are excluded from scoring, never imputed.

## Persistent weaknesses (unchanged from 1B)

- `request` remains the weakest classify category: gold=request cases
  scatter to review_request / open_question / unclear_needs_review / risk
  (wj-001, wj-004, wj-005, wj-021, wj-024).
- End-to-end trails component by ~4pp via upstream cascade
  (artifact 82.1→70.4, playbook 77.8→65.4), same shape as 1B.

## Method

- Branch: `work/eval-phase1c-2026-09-28` (from `work/eval-phase1b-2026-09-28`).
- Suite: `eval-run/suite-phase1c-v1.yaml` (phase1c-v1, 30 cases). Phase 1B
  suite byte-identical, untouched. Deltas per case under `delta_vs_phase1b`:
  4× select_artifact work_item_change→result ("vocabulary merge 2026-09-28"),
  3× classify_data_type →quality_failure ("Ben decision 2026-09-28: split").
- Configs: six canonical JSONs read verbatim from
  `origin/work/work-judgment-vocab-v1c` @ `f074310e469720a9f4dba6db18ed88ce995ae5e0`
  (SHAs in `eval-run/manifest-phase1c.json`). Review rules byte-identical
  in the instantiated drafts. One adaptation: the workbench function schema
  rejects the top-level `changelog` provenance field
  (422 CONFIG_INVALID: "Unrecognized key(s) in object: 'changelog'"), so it
  was stripped from the POSTed configs only; canonical file SHAs are the
  provenance record (see manifest `changelog_note`).
- Instance: fresh `JEV_HOME=/Users/bencharney/.jev-workbench-phase1c-eval`,
  port 17423, Node 24. `/health/live` and `/v1/models` both 200.
  Provider source verified `environment`. Production `~/.jev-workbench`
  and port 17420 untouched. Instance stopped after the run.
- Tokens: `TYPESAFE_API_KEY` from process environment only (fail-closed);
  admin bootstrap via dynamic controlToken→URL-fragment flow; API client
  token held in memory only. No key or token printed, logged, or persisted
  anywhere in the artifacts.
- Driver: `/tmp/run_phase1c.py` (fresh-instance setup + both modes +
  scoring in one script; checkpoint `eval-run/checkpoint-phase1c.jsonl`).

## Files (all under `eval-run/` on this branch)

- `eval-report-phase1c-2026-09-28.md` — this report
- `suite-phase1c-v1.yaml` — the Phase 1C suite
- `manifest-phase1c.json` — config SHAs, function ids/versions, preview record
- `results-phase1c-2026-09-28.json` — full per-invocation results + scores
- `mismatches-phase1c-2026-09-28.json` — all 74 mismatches with upstream flags
- `checkpoint-phase1c.jsonl` — resumable per-record checkpoint

## Recommended follow-ups

1. Gold decision: wj-011 incident→quality_failure (model's reading matches
   the split criterion better than the current gold).
2. Gold review: wj-008 (result vs quality_failure), wj-013/wj-015
   (incident vs evidence).
3. `request` category remains the weakest classify area — candidate for a
   criterion-sharpening pass, not a taxonomy change.
