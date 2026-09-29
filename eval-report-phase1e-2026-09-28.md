# Phase 1E Eval Report — 2026-09-28

Jev Workbench judgment-instructions experiment, phase 1E. Tests the v1e
instruction configs against the Phase 1C v2 suite, both modes, jev-1.13.0.

## Setup

- Eval branch: `work/eval-phase1e-2026-09-28` (from `work/eval-phase1d-2026-09-28`)
- Config branch: `work/work-judgment-instructions-v1e` @
  `d97bca5cb911282978d3c09f1f2112d5b02ccbb5`
- v1e vs v1d: ONLY `examples/work-judgment/classify_data_type.json` changed.
  Verified: `classify_data_type` sha256
  `a34e30e589acd41f98b44e1b81cc24ce1a17253856d75b048c08a733c41fd87d`
  (matches the recorded value); the other five JSONs byte-identical to v1d
  (verified by sha256). The change, per Ben's 2026-09-28 ruling on wj-025:
  reverted the 1D "vagueness alone is not unclear" line (now "Choose
  unclear_needs_review when ambiguity would change routing") and added
  negative guards (approval/sign-off record stays decision not verification;
  completed outcome stays result not verification_evidence/plan;
  vague-but-actionable item stays request not note; state_note only when no
  stronger domain object fits).
- Suite: `eval-run/suite-phase1c-v2.yaml` reused UNCHANGED (sha256
  `8f26909d7023ac703b6b8093d18f4a83b19f526d1877babcb7ce297137b7c5f2`).
  Golds untouched (wj-025 gold was already `unclear_needs_review`;
  wj-008/wj-013/wj-015 are Ben's calls, not re-golded).
- Fresh isolated instance: `JEV_HOME=~/.jev-workbench-phase1e-eval`, port
  17425, node v24.19.0. Server ran from `~/jev-workbench-pr2` (its
  node_modules are built for node 24; the `~/jev-workbench` checkout's
  better-sqlite3 was compiled for node 26 and fails to load under node 24).
  `dist/` is byte-identical between the two checkouts. `/health/live` 200,
  provider source `environment`, six functions instantiated verbatim from the
  canonical v1e JSONs (top-level `changelog` stripped at POST only — the
  workbench schema 422-rejects it; canonical SHAs recorded in the manifest),
  review rules byte-identical and live, draft checksums verified, preview
  smoke tests passed, functions published active_version=1.
- TYPESAFE_API_KEY from process environment only, fail-closed; never
  printed, logged, or persisted. Fresh API client token held in memory only.
- Instance stopped after the run. Nothing merged; no PR comment (per
  instructions). Production (`~/.jev-workbench`, :17420) untouched.

## Headline: 1E vs 1D (baselines 83.4% / 76.4%)

| mode | 1D | 1E | delta |
|---|---|---|---|
| Component (A) | 136/163 = 83.4% | 133/162 = 82.1% | −1.3pp |
| End-to-end (B) | 123/161 = 76.4% | 118/147 = 80.3% | +3.9pp |

Caveat: 1E hit 5 provider 502s (vs 1 in 1D) and 12 skipped-upstream (vs 1),
shrinking the scored denominators — especially in B (−14 cells). The honest
comparison is the 309 cells scored in BOTH phases: **251 vs 250 correct
(81.2% vs 80.9%) — effectively flat, +1 cell.** The +3.9pp B headline is
mostly denominator shrinkage, not real gain.

## The narrow goal: achieved

Ben's ruling was that the wj-025 gold (`unclear_needs_review`) stands over
the 1D instruction line. In 1E:

- A-wj-025-classify_data_type: 1D `request` → **1E `unclear_needs_review` = gold** ✓
- B-wj-025-classify_data_type: 1D `request` → **1E `unclear_needs_review` = gold** ✓
- B-wj-025-next_intent also recovered (`clarify` → `unclear_needs_review` = gold)

The reverted line was the blocker and reverting it fixed the case it was
ruling on. That part of the experiment worked exactly as intended.

## Regression / recovery accounting (common scored cells)

Of the 11 flagged 1D regressions: **1 recovered, 8 still wrong, 2 unscored**
(A/B-wj-030-classify hit 502s in 1E).

- Recovered: A-wj-006-select_playbook (`decision_assessment` →
  `none_required` = gold).
- Still wrong, same answer as 1D: A/B-wj-005-select_artifact and
  A-wj-006-select_artifact (`none_required` → `unclear_needs_review`;
  the confidence loss persists), A/B-wj-007-classify_data_type (`plan` →
  `quality_failure`), A-wj-010-select_artifact (`result` → `plan`).
- Still wrong, different answer: A/B-wj-028-classify_data_type — 1D said
  `state_note`, 1E says `result` (gold `plan`). The new "completed outcome is
  a result" guard fired on the approved plan and moved the error rather than
  fixing it.

**7 new 1E regressions** (correct in 1D → wrong in 1E) vs **8 fixes** (wrong
in 1D → ok in 1E) → net +1 cell on common cells:

| new regression | gold → 1E pred | note |
|---|---|---|
| A-wj-004-select_playbook | technical_project_exploration → none_required | playbook fns unchanged in 1E — variance |
| A-wj-007-select_artifact | plan → decision | artifact fns unchanged — variance |
| A-wj-020-classify_data_type | github_issue → state_note | **on the changed fn**: the new "do not reach for state_note" guard did not fire |
| A-wj-021-next_intent | explore → research | intent fns unchanged — variance |
| A-wj-028-evidence_satisfies_exit | True (p=0.55) → 0.48 | threshold wobble, evidence fn unchanged |
| B-wj-021-next_intent | explore → research | same as A |
| B-wj-021-select_artifact | explore → research | upstream cascade (fed intent=research) |

Only one of the seven is on the edited function — and it goes the wrong way
relative to the new guard's intent. The other six flipped on byte-identical
functions: run-to-run LLM variance is on the order of ±2–3 cells per
judgment, so deltas that small are noise the eval cannot resolve.

## classify_data_type (the edited function)

- A: 16/29 = 55.2% (1D 16/30 = 53.3%); flat on common cells (16/29 both).
- B: 17/28 = 60.7% (1D 16/30 = 53.3%); +1 cell on common cells.
- Still the weakest judgment by a wide margin: 24 of the 58 mismatches are
  classify_data_type. The v1e edit fixed its target case (wj-025) but did not
  move the judgment's overall accuracy.

## Per-judgment deltas (common cells only)

| judgment | A 1D | A 1E | Δ | B 1D | B 1E | Δ |
|---|---|---|---|---|---|---|
| classify_data_type | 16/29 55.2% | 16/29 55.2% | +0.0pp | 16/28 57.1% | 17/28 60.7% | +3.6pp |
| next_intent | 25/30 83.3% | 24/30 80.0% | −3.3pp | 20/27 74.1% | 22/27 81.5% | +7.4pp |
| select_artifact | 25/28 89.3% | 24/28 85.7% | −3.6pp | 18/24 75.0% | 18/24 75.0% | +0.0pp |
| select_playbook | 22/27 81.5% | 22/27 81.5% | +0.0pp | 16/23 69.6% | 17/23 73.9% | +4.3pp |
| requires_human_gate | 29/29 100% | 29/29 100% | +0.0pp | 26/26 100% | 26/26 100% | +0.0pp |
| evidence_satisfies_exit | 19/19 100% | 18/19 94.7% | −5.3pp | 18/19 94.7% | 18/19 94.7% | +0.0pp |

## Brier scores and thresholds (thresholds never changed)

| judgment | mode | Brier 1D → 1E | acc@0.50 | acc@provisional |
|---|---|---|---|---|
| requires_human_gate | A | 0.036 → 0.035 | 100% | 100% @0.70 |
| requires_human_gate | B | 0.043 → 0.038 | 100% | 100% @0.70 |
| evidence_satisfies_exit | A | 0.035 → 0.040 | 94.7% | 78.9% @0.80 |
| evidence_satisfies_exit | B | 0.039 → 0.041 | 94.7% | 78.9% @0.80 |

Raw Noul probabilities recorded per cell. Gate is perfectly calibrated at
both thresholds in both modes. Evidence slipped a hair on the
A-wj-028 wobble (0.55 → 0.48 crossing 0.50).

## Review-trigger counts

- classify_data_type: low_confidence 19 (A, same as 1D) / 18 (B); unclear
  1/1 (new — wj-025 correctly routed to review).
- next_intent: low_confidence 11/10; unclear 1/1.
- select_artifact: low_confidence 5/5; unclear 2/2.
- select_playbook: low_confidence 6/4; unclear 0/2; new_playbook_needed 1/1.
- requires_human_gate: ambiguous_gate 1 (A only).
- evidence_satisfies_exit: ambiguous_exit 3/3.

## Mismatch attributions (58 mismatches + 5 provider errors)

`eval-run/attributions-phase1e.json`: judgment instructions 32, upstream
error 13, bad expected label 11, insufficient context 2, provider error 5.
13 cells flagged `gold_review_needed` (carried from 1B/1D — wj-006
next_intent, wj-008 ×2, wj-010 classify, wj-012, wj-013 ×2, wj-015, wj-024
next_intent, plus 1D-era flags). 51 of the 58 mismatches also mismatched in
1D — the error set is sticky across instruction edits.

## Top remaining mismatch pattern

classify_data_type boundary confusion dominates (24/58): plan vs result vs
quality_failure vs state_note (wj-007, wj-008, wj-028, wj-029), request vs
note (wj-006), incident vs evidence (wj-013, wj-015 — Ben gold-review
candidates). Second: the `none_required` → `unclear_needs_review` confidence
collapse on select_artifact (wj-005, wj-006, both modes) that 1D introduced
and 1E did not touch. The negative guards reshuffled classify errors more
than they removed them.

## Honest assessment

1E is a null result on overall accuracy with one targeted win. The
instruction change did exactly what Ben asked — wj-025 is honored in both
modes — and recovered one 1D regression, but classify_data_type accuracy is
flat (A) to +1 cell (B), and the new guards introduced one fresh miss
(wj-020: `state_note` despite the guard) while overshooting on another
(wj-028: guard fired, gold still missed). Six of the seven new regressions
are on byte-identical functions, i.e. sampling noise — which means this eval
design cannot resolve instruction effects smaller than ±2–3 cells per
judgment without repeated runs. The sticky 51-cell overlap across 1D→1E
suggests the remaining errors are dominated by case/gold ambiguity and model
priors, not by instruction wording.

## Open items

1. 8 still-wrong 1D regressions (wj-005, wj-006 ×2 artifact, wj-007 ×2
   classify, wj-010 artifact, wj-028 ×2 classify).
2. wj-028 plan/result boundary needs Ben's call: is an approved plan with
   resolved decisions a plan or a result? Gold says plan; the v1e guard says
   result. This is the guard's sharpest overshoot.
3. 13 `gold_review_needed` flags outstanding (list in
   `eval-run/attributions-phase1e.json`).
4. 1B open question stands: does "incident" cover quality failures or only
   operational ones (wj-008, wj-013, wj-015)?
5. Provider flakiness: 5× HTTP 502 `UPSTREAM_INVALID_RESPONSE` this run vs 1
   in 1D — worth watching, not yet a trend.

## Artifacts (all on `work/eval-phase1e-2026-09-28`, nothing merged)

- `eval-report-phase1e-2026-09-28.md` (this file)
- `eval-run/run_phase1e.py` — driver (setup + run + score, resumable)
- `eval-run/results-phase1e-2026-09-28.json` — full records (no tokens)
- `eval-run/mismatches-phase1e-2026-09-28.json`
- `eval-run/attributions-phase1e.json`
- `eval-run/manifest-phase1e.json` — canonical + posted SHAs, scores, counts
- `eval-run/checkpoint-phase1e.jsonl`
